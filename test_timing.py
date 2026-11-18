"""Time /calculate_savings on every CET development dataset and print a table.

Run from the repo root:  pytest test_timing.py
"""

import csv
import re
import time

import pytest
from fastapi.testclient import TestClient

import auth
from main import app, calculate_measure_savings
from models import SavingsRequest
from test_savings import (
    ENDPOINT,
    REFERENCE_INPUT_FOLDERS,
    TEST_CREDENTIALS,
    TEST_USERS,
)


@pytest.mark.skipif(
    not REFERENCE_INPUT_FOLDERS,
    reason="CET reference data is gitignored and not present locally",
)
def test_savings_timing(monkeypatch, capsys):
    # Use a fixed user list so the test doesn't depend on .env or CET_API_USERS.
    monkeypatch.setattr(auth.settings, "api_users", TEST_USERS)
    client = TestClient(app)

    table_rows = []
    for reference_input_folder in REFERENCE_INPUT_FOLDERS:
        reference_output_folder = reference_input_folder.with_name(
            reference_input_folder.name.replace("cet_input_", "cet_output_")
        )
        [run_receipt_file] = reference_output_folder.glob("*_runreceipt.txt")
        receipt_text = run_receipt_file.read_text()
        job_id = re.search(r"Job ID: (\d+)", receipt_text).group(1)
        market_effects_benefits = (
            float(re.search(r"Market Effects: ([\d.]+)%", receipt_text).group(1)) / 100
        )

        with (reference_input_folder / "Measure.csv").open() as input_file:
            measures = [
                {key: (None if value == "" else value) for key, value in row.items()}
                for row in csv.DictReader(input_file, delimiter="|")
            ]
        request_body = {
            "MarketEffectsBenefits": market_effects_benefits,
            "Measures": measures,
        }

        # Savings math only: inputs are validated first and excluded from the timing.
        savings_request = SavingsRequest.model_validate(request_body)
        started = time.perf_counter()
        for measure in savings_request.measures:
            calculate_measure_savings(measure, market_effects_benefits)
        savings_math_seconds = time.perf_counter() - started

        # Full API request: JSON parsing, validation, math, WeightedSavings, response.
        started = time.perf_counter()
        response = client.post(ENDPOINT, json=request_body, auth=TEST_CREDENTIALS)
        full_request_seconds = time.perf_counter() - started

        assert response.status_code == 200, response.text
        assert len(response.json()) == len(measures)
        table_rows.append(
            (
                reference_input_folder.name,
                job_id,
                len(measures),
                savings_math_seconds,
                full_request_seconds,
            )
        )

    total_measures = sum(table_row[2] for table_row in table_rows)
    total_savings_math_seconds = sum(table_row[3] for table_row in table_rows)
    total_full_request_seconds = sum(table_row[4] for table_row in table_rows)
    header = (
        f"{'Dataset':<14} {'CET job':>8} {'Measures':>10} "
        f"{'Savings math only':>18} {'Full API request':>17}"
    )
    lines = ["", header, "-" * len(header)]
    for (
        dataset_name,
        job_id,
        measure_count,
        savings_math_seconds,
        full_request_seconds,
    ) in table_rows:
        lines.append(
            f"{dataset_name:<14} {job_id:>8} {measure_count:>10,} "
            f"{savings_math_seconds:>17.2f}s {full_request_seconds:>16.2f}s"
        )
    lines.append("-" * len(header))
    lines.append(
        f"{'Total':<14} {'':>8} {total_measures:>10,} "
        f"{total_savings_math_seconds:>17.2f}s {total_full_request_seconds:>16.2f}s"
    )
    lines.append(
        f"Savings math per measure: "
        f"{total_savings_math_seconds / total_measures * 1e6:.1f} µs"
    )
    with capsys.disabled():
        print("\n".join(lines))
