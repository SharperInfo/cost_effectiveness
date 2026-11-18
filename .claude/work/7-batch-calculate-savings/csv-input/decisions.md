# Decisions: csv-input (branch 7-batch-calculate-savings)

## 2026-11-18: Accept a single Measure.csv upload on a new endpoint
- Decision: `POST /calculate_savings/csv`, multipart with `MeasureFile` and an optional `MarketEffectsBenefits` form field. The JSON endpoint is unchanged.
- Reason: CET users already have Measure.csv; savings only need measures.
- Alternatives: the CET zip (Measure.csv + ProgramCost.csv), deferred until costs; content-type negotiation on the existing endpoint (rejected: one input format per endpoint is clearer in /docs).

## 2026-11-18: Return a pipe-delimited CSV using the API's column names, in CET order
- Decision: CRLF, `|`-delimited, with the JSON names (`CEInputID`, `FirstYearGrossTherm`, …) ordered like CET's outputs.csv (identification, FirstYear, Lifecycle, Annual, WeightedSavings).
- Reason: consistent naming across the API, and a familiar layout for CET users.
- Alternative: CET's exact names (`CET_ID`, `KWh`, `Thm`) for direct diffing (rejected: breaks the descriptive naming).

## 2026-11-18: Order MeasureSavings fields in CET order and derive the CSV header from the model
- Decision: reorder the model's fields instead of keeping a separate CSV column list.
- Reason: there's one source of truth for the columns. JSON key order changes too, which is harmless.

## 2026-11-18: Share the calculation between the JSON and CSV endpoints
- Decision: `calculate_savings_for_request(savings_request)` holds the per-measure loop and the WeightedSavings pass; both endpoints call it.
- Reason: avoids duplicating the weighting logic.

## 2026-11-18: Use Annotated[...] for the upload parameters
- Decision: `Annotated[UploadFile, File(alias="MeasureFile")]` instead of `= File(...)` defaults.
- Reason: ruff B008 flags function calls in argument defaults, and Annotated is FastAPI's recommended style.
