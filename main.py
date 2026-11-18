from collections import defaultdict

from fastapi import Depends, FastAPI

from auth import require_user
from models import Item, Measure, MeasureSavings, ProgramCost, SavingsRequest

app = FastAPI(dependencies=[Depends(require_user)])

THERM_CONVERSION = 29.307111111

TEST_CO2Gas = 0.00531


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/{api_version}/test_version")
async def version_test(api_version: str):
    return {"message": api_version}


@app.post("/measures")
async def create_measure(measure: Measure):
    return measure


def calculate_measure_savings(
    measure: Measure, market_effects_benefits: float
) -> dict[str, float]:
    """Calculate one measure's savings, keyed by output name.

    Ported from dbo.CalcSavings (CET 25.1), including the NULL defaults and
    EUL/RUL normalization that its source view, InputMeasurevw, applies.
    """
    # InputMeasurevw: a RUL at or beyond the EUL is treated as single baseline.
    remaining_useful_life = measure.rul_yrs or 0
    effective_useful_life = measure.eul_yrs or 0
    if remaining_useful_life >= effective_useful_life:
        effective_useful_life = remaining_useful_life
        remaining_useful_life = 0

    # Fraction of the first year credited to each baseline.
    if remaining_useful_life >= 1:
        first_baseline_first_year_fraction = 1
    elif remaining_useful_life > 0:
        first_baseline_first_year_fraction = remaining_useful_life
    elif effective_useful_life < 1:
        first_baseline_first_year_fraction = effective_useful_life
    else:
        first_baseline_first_year_fraction = 1

    if 0 < remaining_useful_life < 1 and effective_useful_life < 1:
        second_baseline_first_year_fraction = (
            effective_useful_life - remaining_useful_life
        )
    elif 0 < remaining_useful_life < 1:
        second_baseline_first_year_fraction = 1 - remaining_useful_life
    else:
        second_baseline_first_year_fraction = 0

    # InputMeasurevw defaults: missing savings are 0, missing rates are 1, and
    # the kW and therm net-to-gross ratios fall back to the kWh ratio.
    unit_kwh_site_1st_baseline = measure.unit_kwh_1st_baseline or 0
    unit_kwh_site_2nd_baseline = measure.unit_kwh_2nd_baseline or 0
    unit_kwh_water_1st_baseline = measure.unit_kwh_iou_water_1st_baseline or 0
    unit_kwh_water_2nd_baseline = measure.unit_kwh_iou_water_2nd_baseline or 0
    net_to_gross_ratio_kwh = 1 if measure.ntgr_kwh is None else measure.ntgr_kwh
    net_to_gross_ratio_kw = (
        net_to_gross_ratio_kwh if measure.ntgr_kw is None else measure.ntgr_kw
    )
    net_to_gross_ratio_therm = (
        net_to_gross_ratio_kwh if measure.ntgr_therm is None else measure.ntgr_therm
    )
    installation_rate_kwh = (
        1 if measure.installation_rate_kwh is None else measure.installation_rate_kwh
    )
    realization_rate_kwh = (
        1 if measure.realization_rate_kwh is None else measure.realization_rate_kwh
    )

    # Output-name suffix -> (unit savings 1st baseline, unit savings 2nd baseline,
    # installation rate, realization rate, net-to-gross ratio).
    savings_inputs_by_fuel = {
        "kWh": (
            unit_kwh_site_1st_baseline + unit_kwh_water_1st_baseline,
            unit_kwh_site_2nd_baseline + unit_kwh_water_2nd_baseline,
            installation_rate_kwh,
            realization_rate_kwh,
            net_to_gross_ratio_kwh,
        ),
        "kWhSite": (
            unit_kwh_site_1st_baseline,
            unit_kwh_site_2nd_baseline,
            installation_rate_kwh,
            realization_rate_kwh,
            net_to_gross_ratio_kwh,
        ),
        "kWhWater": (
            unit_kwh_water_1st_baseline,
            unit_kwh_water_2nd_baseline,
            installation_rate_kwh,
            realization_rate_kwh,
            net_to_gross_ratio_kwh,
        ),
        "kW": (
            measure.unit_kw_1st_baseline or 0,
            measure.unit_kw_2nd_baseline or 0,
            1 if measure.installation_rate_kw is None else measure.installation_rate_kw,
            1 if measure.realization_rate_kw is None else measure.realization_rate_kw,
            net_to_gross_ratio_kw,
        ),
        "Therm": (
            measure.unit_therm_1st_baseline or 0,
            measure.unit_therm_2nd_baseline or 0,
            1
            if measure.installation_rate_therm is None
            else measure.installation_rate_therm,
            1
            if measure.realization_rate_therm is None
            else measure.realization_rate_therm,
            net_to_gross_ratio_therm,
        ),
    }

    savings = {}
    for fuel_suffix, (
        unit_savings_1st_baseline,
        unit_savings_2nd_baseline,
        installation_rate,
        realization_rate,
        net_to_gross_ratio,
    ) in savings_inputs_by_fuel.items():
        adjusted_quantity = (
            (measure.num_units or 0) * installation_rate * realization_rate
        )
        net_factor = net_to_gross_ratio + market_effects_benefits

        if remaining_useful_life == 0:
            lifecycle_gross = (
                adjusted_quantity * unit_savings_1st_baseline * effective_useful_life
            )
            annual_gross = adjusted_quantity * unit_savings_1st_baseline
        else:
            lifecycle_gross = adjusted_quantity * (
                unit_savings_1st_baseline * remaining_useful_life
                + unit_savings_2nd_baseline
                * (effective_useful_life - remaining_useful_life)
            )
            annual_gross = lifecycle_gross / effective_useful_life

        first_year_gross = adjusted_quantity * (
            unit_savings_1st_baseline * first_baseline_first_year_fraction
            + unit_savings_2nd_baseline * second_baseline_first_year_fraction
        )

        savings[f"AnnualGross{fuel_suffix}"] = annual_gross
        savings[f"AnnualNet{fuel_suffix}"] = annual_gross * net_factor
        savings[f"FirstYearGross{fuel_suffix}"] = first_year_gross
        savings[f"FirstYearNet{fuel_suffix}"] = first_year_gross * net_factor
        # Demand (kW) savings have no lifecycle total.
        if fuel_suffix != "kW":
            savings[f"LifecycleGross{fuel_suffix}"] = lifecycle_gross
            savings[f"LifecycleNet{fuel_suffix}"] = lifecycle_gross * net_factor

    return savings


@app.post("/calculate_savings", response_model=list[MeasureSavings])
async def calculate_savings(savings_request: SavingsRequest):
    savings_by_measure = [
        calculate_measure_savings(measure, savings_request.market_effects_benefits)
        for measure in savings_request.measures
    ]

    # WeightedSavings: each measure's share of its program's positive first-year
    # gross savings (therms converted to kWh). Programs with no positive savings
    # split evenly across their measures.
    weighting_savings_by_measure = [
        max(savings["FirstYearGrosskWh"], 0)
        + THERM_CONVERSION * max(savings["FirstYearGrossTherm"], 0)
        for savings in savings_by_measure
    ]
    program_weighting_savings_total = defaultdict(float)
    program_measure_count = defaultdict(int)
    for measure, weighting_savings in zip(
        savings_request.measures, weighting_savings_by_measure
    ):
        program_weighting_savings_total[measure.prg_id] += weighting_savings
        program_measure_count[measure.prg_id] += 1

    results = []
    for measure, savings, weighting_savings in zip(
        savings_request.measures, savings_by_measure, weighting_savings_by_measure
    ):
        program_total = program_weighting_savings_total[measure.prg_id]
        if program_total != 0:
            weighted_savings = weighting_savings / program_total
        else:
            weighted_savings = 1 / program_measure_count[measure.prg_id]
        results.append(
            MeasureSavings(
                CEInputID=measure.ce_input_id,
                PA=measure.pa,
                PrgID=measure.prg_id,
                WeightedSavings=weighted_savings,
                **savings,
            )
        )
    return results


@app.post("/calculate_emissions")
async def calculate_emissions(measure: Measure):

    GrossGasCO2 = (
        measure.num_units
        * measure.installation_rate_therm
        * measure.realization_rate_therm
        * TEST_CO2Gas
        * (min(measure.eul_yrs, 1))
        * (
            0
            if measure.unit_therm_1st_baseline is None
            else measure.unit_therm_1st_baseline
        )
    )

    return {"GrossGasCO2": GrossGasCO2}


@app.post("/program_costs")
async def create_program_cost(program_cost: ProgramCost):
    return program_cost


@app.post("/items/")
async def create_item(item: Item):
    return item
