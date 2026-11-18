"""Tests for POST /calculate_savings (port of dbo.CalcSavings, CET 25.1).

Run from the repo root:  pytest
"""

import csv
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import auth
from main import THERM_CONVERSION, app

TEST_USERS = {"test-user": "test-password"}
TEST_CREDENTIALS = ("test-user", "test-password")
ENDPOINT = "/calculate_savings"

REFERENCE_DATA_FOLDER = Path(__file__).parent / "references" / "development_data"
# Each cet_input_NN folder (Measure.csv) pairs with a cet_output_NN folder
# holding the CET run's <JobID>_outputs.csv and <JobID>_runreceipt.txt.
REFERENCE_INPUT_FOLDERS = sorted(REFERENCE_DATA_FOLDER.glob("cet_input_*"))
IDENTIFICATION_FIELDS = ("CEInputID", "PA", "PrgID")


@pytest.fixture
def client(monkeypatch):
    # Use a fixed user list so the tests don't depend on .env or CET_API_USERS.
    monkeypatch.setattr(auth.settings, "api_users", TEST_USERS)
    return TestClient(app)


def post_measures(client, measures, market_effects_benefits=None):
    request_body = {"Measures": measures}
    if market_effects_benefits is not None:
        request_body["MarketEffectsBenefits"] = market_effects_benefits
    response = client.post(ENDPOINT, json=request_body, auth=TEST_CREDENTIALS)
    assert response.status_code == 200, response.text
    return response.json()


def build_measure(**fields):
    return {
        "CEInputID": "CE-0001",
        "PrgID": "PGE_21001",
        "ClaimYearQuarter": "2027Q1",
        **fields,
    }


@pytest.mark.skipif(
    not REFERENCE_INPUT_FOLDERS,
    reason="CET reference data is gitignored and not present locally",
)
@pytest.mark.parametrize(
    "reference_input_folder", REFERENCE_INPUT_FOLDERS, ids=lambda folder: folder.name
)
def test_matches_cet_reference_output(client, reference_input_folder):
    reference_output_folder = (
        REFERENCE_DATA_FOLDER
        / reference_input_folder.name.replace("cet_input_", "cet_output_")
    )
    [reference_output_file] = reference_output_folder.glob("*_outputs.csv")
    [run_receipt_file] = reference_output_folder.glob("*_runreceipt.txt")
    # The run receipt records market effects as a percentage, e.g. "-Market Effects: 0%".
    market_effects_percent = re.search(
        r"Market Effects: ([\d.]+)%", run_receipt_file.read_text()
    ).group(1)

    with (reference_input_folder / "Measure.csv").open() as input_file:
        measures = [
            {key: (None if value == "" else value) for key, value in row.items()}
            for row in csv.DictReader(input_file, delimiter="|")
        ]
    with reference_output_file.open() as output_file:
        expected_by_ce_input_id = {
            row["CET_ID"]: row for row in csv.DictReader(output_file, delimiter="|")
        }

    results = post_measures(
        client, measures, market_effects_benefits=float(market_effects_percent) / 100
    )

    assert len(results) == len(measures)
    for result in results:
        expected = expected_by_ce_input_id[result["CEInputID"]]
        for field_name, value in result.items():
            if field_name in IDENTIFICATION_FIELDS:
                continue
            # CET output files spell these "KWh", "KW", and "Thm".
            reference_field_name = field_name.replace("kW", "KW").replace(
                "Therm", "Thm"
            )
            assert value == pytest.approx(
                float(expected[reference_field_name]), rel=1e-9, abs=1e-9
            ), (result["CEInputID"], field_name)


def test_single_baseline(client):
    measure = build_measure(
        NumUnits=10,
        EUL_Yrs=12,
        UnitkWh1stBaseline=25,
        UnitkWhIOUWater1stBaseline=5,
        UnitkW1stBaseline=0.01,
        NTGRkWh=0.8,
        InstallationRatekWh=0.9,
        RealizationRatekWh=0.5,
    )

    [result] = post_measures(client, [measure])

    # Adjusted quantity for kWh = 10 * 0.9 * 0.5 = 4.5
    assert result["FirstYearGrosskWh"] == pytest.approx(4.5 * 30)
    assert result["FirstYearGrosskWhSite"] == pytest.approx(4.5 * 25)
    assert result["FirstYearGrosskWhWater"] == pytest.approx(4.5 * 5)
    assert result["AnnualGrosskWh"] == pytest.approx(4.5 * 30)
    assert result["LifecycleGrosskWh"] == pytest.approx(4.5 * 30 * 12)
    assert result["LifecycleNetkWh"] == pytest.approx(4.5 * 30 * 12 * 0.8)
    # kW rates default to 1 and NTGRkW falls back to NTGRkWh.
    assert result["FirstYearGrosskW"] == pytest.approx(10 * 0.01)
    assert result["FirstYearNetkW"] == pytest.approx(10 * 0.01 * 0.8)
    assert "LifecycleGrosskW" not in result


@pytest.mark.parametrize(
    (
        "effective_useful_life",
        "remaining_useful_life",
        "expected_first_year_gross",
        "expected_lifecycle_gross",
        "expected_annual_gross",
    ),
    [
        # RUL >= 1: first year is all 1st baseline.
        (10, 3, 2 * 100, 2 * (100 * 3 + 40 * 7), 2 * (100 * 3 + 40 * 7) / 10),
        # 0 < RUL < 1, EUL >= 1: first year splits at RUL.
        (
            5,
            0.25,
            2 * (100 * 0.25 + 40 * 0.75),
            2 * (100 * 0.25 + 40 * 4.75),
            2 * (100 * 0.25 + 40 * 4.75) / 5,
        ),
        # 0 < RUL < 1, EUL < 1: 2nd baseline runs only until EUL.
        (
            0.8,
            0.5,
            2 * (100 * 0.5 + 40 * 0.3),
            2 * (100 * 0.5 + 40 * 0.3),
            2 * (100 * 0.5 + 40 * 0.3) / 0.8,
        ),
        # RUL >= EUL: treated as single baseline with EUL = RUL.
        (3, 5, 2 * 100, 2 * 100 * 5, 2 * 100),
        # Single baseline with EUL < 1: first year is prorated.
        (0.5, 0, 2 * 100 * 0.5, 2 * 100 * 0.5, 2 * 100),
    ],
)
def test_dual_baseline_and_short_lives(
    client,
    effective_useful_life,
    remaining_useful_life,
    expected_first_year_gross,
    expected_lifecycle_gross,
    expected_annual_gross,
):
    measure = build_measure(
        NumUnits=2,
        EUL_Yrs=effective_useful_life,
        RUL_Yrs=remaining_useful_life,
        UnitkWh1stBaseline=100,
        UnitkWh2ndBaseline=40,
        UnitTherm1stBaseline=100,
        UnitTherm2ndBaseline=40,
        NTGRkWh=0.5,
    )

    [result] = post_measures(client, [measure])

    for fuel_suffix in ("kWh", "Therm"):
        assert result[f"FirstYearGross{fuel_suffix}"] == pytest.approx(
            expected_first_year_gross
        )
        assert result[f"LifecycleGross{fuel_suffix}"] == pytest.approx(
            expected_lifecycle_gross
        )
        assert result[f"AnnualGross{fuel_suffix}"] == pytest.approx(
            expected_annual_gross
        )
        assert result[f"LifecycleNet{fuel_suffix}"] == pytest.approx(
            expected_lifecycle_gross * 0.5
        )


def test_missing_values_use_cet_defaults(client):
    measure = build_measure(NumUnits=4, EUL_Yrs=1, UnitTherm1stBaseline=10)

    [result] = post_measures(client, [measure])

    # Rates and every NTGR default to 1; missing savings are 0.
    assert result["FirstYearNetTherm"] == pytest.approx(40)
    assert result["FirstYearNetkWh"] == 0
    assert result["FirstYearNetkW"] == 0


def test_missing_ntgr_therm_falls_back_to_ntgr_kwh(client):
    measure = build_measure(
        NumUnits=4, EUL_Yrs=1, UnitTherm1stBaseline=10, NTGRkWh=0.6, NTGRkW=0.2
    )

    [result] = post_measures(client, [measure])

    assert result["FirstYearNetTherm"] == pytest.approx(4 * 10 * 0.6)


def test_market_effects_benefits_added_to_ntgr(client):
    measure = build_measure(NumUnits=1, EUL_Yrs=10, UnitkWh1stBaseline=100, NTGRkWh=0.7)

    [result] = post_measures(client, [measure], market_effects_benefits=0.1)

    assert result["FirstYearNetkWh"] == pytest.approx(100 * 0.8)
    assert result["LifecycleNetkWh"] == pytest.approx(100 * 10 * 0.8)
    # Gross savings are unaffected.
    assert result["FirstYearGrosskWh"] == pytest.approx(100)


def test_weighted_savings_per_program(client):
    measures = [
        build_measure(
            CEInputID="A-kWh", PrgID="A", NumUnits=1, EUL_Yrs=5, UnitkWh1stBaseline=100
        ),
        build_measure(
            CEInputID="A-Therm",
            PrgID="A",
            NumUnits=1,
            EUL_Yrs=5,
            UnitTherm1stBaseline=1,
        ),
        # Negative savings are excluded from the weighting.
        build_measure(
            CEInputID="A-Negative",
            PrgID="A",
            NumUnits=1,
            EUL_Yrs=5,
            UnitkWh1stBaseline=-50,
        ),
        # A program with no positive savings splits evenly.
        build_measure(CEInputID="B-1", PrgID="B", NumUnits=1, EUL_Yrs=5),
        build_measure(
            CEInputID="B-2", PrgID="B", NumUnits=1, EUL_Yrs=5, UnitkWh1stBaseline=-10
        ),
    ]

    results = post_measures(client, measures)

    weighted_savings_by_id = {
        result["CEInputID"]: result["WeightedSavings"] for result in results
    }
    program_a_total = 100 + THERM_CONVERSION
    assert weighted_savings_by_id == pytest.approx(
        {
            "A-kWh": 100 / program_a_total,
            "A-Therm": THERM_CONVERSION / program_a_total,
            "A-Negative": 0,
            "B-1": 0.5,
            "B-2": 0.5,
        }
    )


def test_results_keep_input_order_and_identification(client):
    measures = [
        build_measure(CEInputID="second", PA="SCE", PrgID="P2"),
        build_measure(CEInputID="first", PA="PGE", PrgID="P1"),
    ]

    results = post_measures(client, measures)

    assert [
        (result["CEInputID"], result["PA"], result["PrgID"]) for result in results
    ] == [("second", "SCE", "P2"), ("first", "PGE", "P1")]


def test_empty_measure_list_returns_empty_list(client):
    assert post_measures(client, []) == []
