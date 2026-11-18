# Decisions: 7-batch-calculate-savings

## 2026-11-18: Replace /calculate_savings with a list-of-measures endpoint
- Decision: `POST /calculate_savings` now takes `{"MarketEffectsBenefits": float = 0, "Measures": [...]}` and returns one savings record per measure, in input order.
- Reason: a single endpoint, and the request mirrors a CET job (a list of measures plus job-level market effects).
- Alternatives: keep the single-measure endpoint and add a batch one (rejected: duplicate surface); pass market effects as a query parameter or hard-code 0 (rejected: it belongs to the request body).

## 2026-11-18: Include WeightedSavings, computed per PrgID within the request
- Decision: port the SQL WeightedSavings calculation, grouping by PrgID across the submitted measures, including the 1/count fallback.
- Reason: it's part of CalcSavings output and later cost allocation depends on it.
- Alternative: defer to the cost-calc slice.

## 2026-11-18: Output names follow OutputSavings columns, with "Therm" spelled out
- Decision: e.g. `LifecycleNetkWh`, `FirstYearGrossTherm`, `AnnualNetkW`.
- Reason: lines up with CET output files while matching input naming (`UnitTherm1stBaseline`, `NTGRTherm`).
- Alternatives: the SQL "Thm" names; "Therms" (plural, as the old code used).

## 2026-11-18: Port InputMeasurevw NULL defaults and EUL/RUL normalization
- Decision: before calculating, apply the defaults from the InputMeasurevw view (`dbo.InitializeTables`): NULL quantity and savings become 0; NULL IR/RR/NTGRkWh become 1; NTGRkW and NTGRTherm fall back to NTGRkWh, then to 1; if RUL >= EUL, then EUL = RUL and RUL = 0.
- Reason: CalcSavings reads from that view, so its formulas assume these values. Without them, results would not match CET.

## 2026-11-18: SQL first-year CASE inconsistencies collapse to one rule
- Decision: use a single pair of first-year fractions for all fuels.
- Reason: the SQL mixes `RUL >= 1` / `RUL > 1` / `RUL <= 1`. Once inputs are normalized, RUL = 1 hits the ELSE 1 branch anyway. The water `RUL <= 1 AND EUL < 1` case can't occur, because RUL >= EUL forces RUL to 0. So the variants are equivalent.

## 2026-11-18: Duplicate CEInputIDs are not merged
- Decision: each measure in the request gets its own record.
- Reason: the SQL GROUP BY (PA, PrgID, CET_ID) would sum duplicates, but in an API, returning results 1:1 with inputs is clearer. Validation of duplicate IDs can come later.
