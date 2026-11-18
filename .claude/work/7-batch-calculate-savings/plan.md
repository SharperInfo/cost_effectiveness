# Plan: calculate all savings for a list of measures

Branch: `7-batch-calculate-savings` · Work folder: `.claude/work/7-batch-calculate-savings/`
(after approval, copy this plan to `<work-folder>/plan.md` and log the decisions below in `<work-folder>/decisions.md`)

## Context

Right now `POST /calculate_savings` in `main.py` takes one measure and returns only 4 lifecycle values. It also has bugs: every formula uses `ntgr_therm`, there are no NULL defaults, and it ignores RUL / 2nd baseline. The goal is to port the full `dbo.CalcSavings` stored procedure (`references/stored_procedures_v25.1/dbo.CalcSavings.StoredProcedure.sql`) to Python. That means all 30 savings outputs plus `WeightedSavings`, calculated for a JSON list of measures, with full descriptive output names.

## Decisions (confirmed with you)

- **Endpoint:** replace the body of `POST /calculate_savings`. It now accepts a list of measures and returns one savings record per measure, in input order.
- **Request shape:** `{"MarketEffectsBenefits": 0.0, "Measures": [ {...Measure...}, ... ]}`. `MarketEffectsBenefits` is optional and defaults to 0 (SQL `@MEBens`).
- **WeightedSavings:** included. It's computed per `PrgID` across the measures in the request, exactly as the SQL does.
- **Naming:** use the SQL `OutputSavings` column names but spell out "Therm", e.g. `LifecycleNetkWh`, `LifecycleNetTherm`, `FirstYearGrossTherm`, `AnnualNetkW`, `AnnualGrosskWhWater`.

## Formulas (from CalcSavings plus the InputMeasurevw view in `dbo.InitializeTables`)

**Input normalization (InputMeasurevw):**
- `NumUnits` and all unit savings: NULL becomes 0.
- IR and RR: NULL becomes 1.
- `NTGRkWh`: NULL becomes 1.
- `NTGRkW` = coalesce(NTGRkW, NTGRkWh, 1). `NTGRTherm` = coalesce(NTGRTherm, NTGRkWh, 1).
- EUL/RUL: NULL becomes 0. If `RUL >= EUL`, then `EUL = RUL` and `RUL = 0`.

**Per-measure factors (the same for every fuel):**
- `first_baseline_first_year_fraction`: 1 if RUL ≥ 1; RUL if 0 < RUL < 1; EUL if RUL = 0 and EUL < 1; otherwise 1.
- `second_baseline_first_year_fraction`: EUL − RUL if 0 < RUL < 1 and EUL < 1; 1 − RUL if 0 < RUL < 1 and EUL ≥ 1; otherwise 0.
  - The SQL's small `RUL > 1` / `RUL >= 1` / `RUL <= 1` inconsistencies give identical results once inputs are normalized. I'll log this in decisions.md.

**For each fuel, with `adjusted_quantity = NumUnits × IR × RR`:**

The fuels are:
- kWh, where the unit savings are site + IOU water
- kWhSite
- kWhWater
- kW
- Therm

| Output | RUL = 0 | RUL > 0 |
|---|---|---|
| AnnualGross | qty × unit1 | qty × (unit1·RUL + unit2·(EUL−RUL)) / EUL |
| LifecycleGross (not for kW) | qty × unit1 × EUL | qty × (unit1·RUL + unit2·(EUL−RUL)) |
| FirstYearGross | qty × (unit1·fraction1 + unit2·fraction2) | same |
| …Net | Gross × (NTGR_fuel + MarketEffectsBenefits) | same |

**WeightedSavings, per PrgID:**
- Each measure's share is `(max(FirstYearGrosskWh, 0) + THERM_CONVERSION × max(FirstYearGrossTherm, 0))` divided by the program's sum of the same quantity.
- If that program sum is 0, the share is `1 / count of measures in the program`.

## Implementation

### Slice 1: models, calculation, endpoint

**`models.py`:**
- Add `SavingsRequest`: `market_effects_benefits: float = Field(0.0, alias="MarketEffectsBenefits")` and `measures: list[Measure] = Field(alias="Measures")`.
- Add `MeasureSavings`: identification fields (`CEInputID`, `PA`, `PrgID`), the 30 savings fields, and `WeightedSavings`. These are snake_case attributes with aliases, following the existing `Measure` pattern. It's used as the endpoint's `response_model` so the outputs show up in OpenAPI docs.

**`main.py`:**
- Replace the `calculate_savings` body:
  1. For each measure, normalize the inputs, compute the two first-year fractions, then loop over a small fuel table. The table maps an output suffix (`kWh`, `kWhSite`, `kWhWater`, `kW`, `Therm`) to (unit savings 1st baseline, unit savings 2nd baseline, installation rate, realization rate, NTGR). Results go into a dict keyed by output alias. This avoids writing 30 near-identical formulas.
  2. In a second pass, group by PrgID and fill in `WeightedSavings`.
- Reuse the existing `THERM_CONVERSION` constant.
- The per-measure calculation is multi-step, so it gets one function, `calculate_measure_savings(measure, market_effects_benefits)`. Weighting stays inline in the endpoint. No other new helpers.
- Remove the old 4-formula body (dead code).

**`CET_tests.http` (you confirmed this file should be updated):**
- Update the `/calculate_savings` example to the new `{"Measures": [...]}` body, with an explicit `"MarketEffectsBenefits": 0`.
- Add a second request that has two measures, including a dual-baseline one (RUL > 0).

### Slice 2: tests (`test_savings.py`, alongside `test_auth.py`)

- **Regression test:** load all 20,304 rows of `references/development_data/cet_input_01/Measure.csv` (pipe-delimited; empty strings become None). POST them through `TestClient` and compare every savings field and `WeightedSavings` to `cet_output_01/123297_outputs.csv` using `pytest.approx`. The CSV header uses `KWh`/`Thm`, so the test maps those to the API names. This reference run used 0% market effects and is all single-baseline.
- **Hand-computed dual-baseline cases:** RUL ≥ 1; 0 < RUL < 1 with EUL ≥ 1; 0 < RUL < 1 with EUL < 1; RUL ≥ EUL (normalization).
- **Other cases:**
  - NULL defaults (missing NTGRTherm falls back to NTGRkWh)
  - `MarketEffectsBenefits` added to NTGR
  - `WeightedSavings` fallback to 1/count when a program has no positive savings
- Auth uses the same `monkeypatch` fixture pattern as `test_auth.py`.

## Behavior notes

- Duplicate `CEInputID`s in a request are returned as separate records. The SQL GROUP BY would sum them; I'll log this in decisions.md.
- An empty `Measures` list returns `[]`.
- Unknown extra fields on a measure (e.g. `JobID`, `FuelType` in the .http examples) are ignored, as they are today.

## Verification

1. `pytest` from the repo root: the existing auth tests plus the new savings tests all pass, including the 20k-row match against the CET reference output.
2. Run `fastapi dev main.py`, then send the `/calculate_savings` requests in `CET_tests.http`. Check that the response is a list with all 31 fields and that `WeightedSavings` sums to 1 per PrgID.
3. Check the `/docs` page: it shows the `SavingsRequest` body and the `MeasureSavings` response schema.
