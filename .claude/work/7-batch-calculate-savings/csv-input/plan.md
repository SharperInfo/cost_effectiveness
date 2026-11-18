# Plan: accept the CET Measure.csv input format

Branch: `7-batch-calculate-savings` · Component: `csv-input`
Work folder: `.claude/work/7-batch-calculate-savings/csv-input/`
Status: implemented, not yet committed. All 29 savings and auth tests pass.

## Context

`POST /calculate_savings` only accepts JSON. CET users already have their measures in CET's input format: a pipe-delimited `Measure.csv` with CRLF line endings and a header row. Its column names already match the `Measure` model's aliases, plus an extra `IOU_AC_Territory` column that will be ignored. Today, using the API means converting that file to JSON first.

The goal is to upload `Measure.csv` as it is and get the savings back as a pipe-delimited CSV.

## Decisions (confirmed with you)

- **Input:** a single `Measure.csv` upload. CET zips and `ProgramCost.csv` are out of scope until the cost-calculation work.
- **Endpoint:** a new `POST /calculate_savings/csv`, sent as `multipart/form-data`:
  - `MeasureFile`: the file
  - `MarketEffectsBenefits`: optional form field, default 0, same meaning as in JSON
  - The JSON endpoint doesn't change.
- **Response:** a pipe-delimited CSV download with CRLF line endings, matching CET's output files.
- **CSV column names:** the same names as the JSON response (`CEInputID`, `LifecycleNetkWh`, `FirstYearGrossTherm`, …), in CET's `outputs.csv` column order:
  1. identification
  2. FirstYear
  3. Lifecycle
  4. Annual
  5. `WeightedSavings`

## Implementation

### `models.py`
- Reorder the `MeasureSavings` fields into CET output order: `CEInputID`, `PA`, `PrgID`, then the FirstYear fields, then Lifecycle, then Annual, then `WeightedSavings`.
- The CSV header can then come straight from `MeasureSavings.model_fields` (each field's alias). There's no separate column list to maintain.
- The JSON response keys get the same order. That's harmless, since nothing depends on key order.

### `main.py`
1. **Shared calculation.** Move the body of the JSON `calculate_savings` endpoint into `calculate_savings_for_request(savings_request: SavingsRequest) -> list[MeasureSavings]`. That body is the per-measure calculation plus the `WeightedSavings` pass. Both endpoints call it, so the weighting logic isn't duplicated. The JSON endpoint becomes a one-line wrapper.
2. **New endpoint** `calculate_savings_csv(measure_file: UploadFile = File(alias="MeasureFile"), market_effects_benefits: float = Form(0.0, alias="MarketEffectsBenefits"))`:
   - **Read the file:** read the upload, decode it as `utf-8-sig` (which handles a byte-order mark if Excel added one), and parse it with `csv.DictReader(io.StringIO(text), delimiter="|")`. Empty strings become `None`, the same rule the tests already use.
   - **Validate:** build the request with `SavingsRequest.model_validate({"MarketEffectsBenefits": ..., "Measures": rows})`.
   - **Errors:** on `ValidationError`, return a 422 that lists each error with its CSV line number (measure index + 2) and the column alias. For example: `line 7, NumUnits: Input should be a valid number`. That way users can fix the file.
   - **Calculate:** call `calculate_savings_for_request`.
   - **Write the results:** use `csv.writer(..., delimiter="|")` with the default CRLF line terminator. The header comes from the `MeasureSavings` field aliases, and each row is `model_dump(by_alias=True)` values. `None` (e.g. a missing PA) becomes an empty cell.
   - **Return:** `Response(content, media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="savings_outputs.csv"'})`.
   - The calculation itself doesn't change, and no other helpers are added.

### `CET_tests.http`
- Add a multipart upload request that sends `references/development_data/cet_input_02/Measure.csv`, using REST Client's `< ./path` file syntax. A comment will note that the file is local, gitignored development data.

### Tests: `test_savings.py`
- **CSV regression test:** for each `cet_input_NN` dataset, upload the raw `Measure.csv` bytes, parse the pipe-delimited response, and compare every savings column against `<JobID>_outputs.csv`. This reuses the existing dataset discovery, receipt parsing, and the `kW`→`KW` / `Therm`→`Thm` name mapping. To avoid duplicating the comparison loop, the existing regression test is parametrized over input mode (`json`, `csv`), with the results normalized to dictionaries in both cases.
- **Small cases (no reference data needed):**
  - the response header is in CET column order, uses `|`, and has CRLF line endings
  - blank cells use CET's defaults
  - a BOM-prefixed file parses
  - the extra `IOU_AC_Territory` column is ignored
  - the `MarketEffectsBenefits` form field is applied
  - a bad value returns 422 naming the right line and column
  - a header-only file returns just the header row

## Out of scope

- CET zip upload and `ProgramCost.csv` (that comes with costs).
- Streaming or chunked parsing. A 130k-measure file (47 MB) reads fine into memory.
- Adding a CSV column to `test_timing.py`. That's easy to add later if you want it.

## Verification

1. `pytest`: all existing tests pass, and the new CSV tests pass, including the CSV regression on all three datasets (155,887 measures).
2. `fastapi dev main.py`, then send the new upload request in `CET_tests.http`. The response downloads `savings_outputs.csv` with one row per measure.
3. `/docs` shows `/calculate_savings/csv` with a file picker and the `MarketEffectsBenefits` field. Upload `cet_input_02/Measure.csv` there as well.
