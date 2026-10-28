# CalcSavings vs. the facet `Measure` and `ProgramCost` models

How [`dbo.CalcSavings`](stored_procedures_v25.1/dbo.CalcSavings.StoredProcedure.sql) relates to the Pydantic models in [facet/models.py](facet/models.py).

## Summary

`CalcSavings` uses part of `Measure`: quantity, unit savings, the four adjustment factors and useful life. It doesn't use `ProgramCost` at all. Its `WeightedSavings` column looks like a key for splitting program costs across measures, but the CE calculation in v25.1 doesn't read it.

## What the procedure does

It reads one row per measure from `InputMeasurevw`. It works out annual, lifecycle and first-year savings, gross and net, for kWh (site, water and total), kW and therms. It then adds each measure's share of its program's first-year savings and writes everything to `OutputSavings`.

### Step 1: `InputMeasurevw` cleans the inputs first

The procedure's formulas depend on cleanup done earlier by `InitializeTables` ([dbo.InitializeTables.StoredProcedure.sql](stored_procedures_v25.1/dbo.InitializeTables.StoredProcedure.sql)). That procedure maps the source columns, which are the same columns the `Measure` aliases use, to short names and fills in defaults:

| `Measure` field (alias) | View column | Default / rule |
|---|---|---|
| `ce_input_id` (`CEInputID`) | `CET_ID` | — |
| `num_units` | `Qty` | 0 |
| `unit_kw/kwh/therm_1st_baseline` | `kW1`, `kWh1`, `Thm1` | 0 |
| `unit_kw/kwh/therm_2nd_baseline` | `kW2`, `kWh2`, `Thm2` | 0 |
| `unit_kwh_iou_water_1st/2nd_baseline` | `kWhWater1`, `kWhWater2` | 0 |
| `ntgr_kwh` | `NTGRkWh` | 1 |
| `ntgr_kw`, `ntgr_therm` | `NTGRkW`, `NTGRThm` | fall back to `NTGRkWh`, then 1 |
| `installation_rate_*` | `IRkW`, `IRkWh`, `IRThm` | 1 |
| `realization_rate_*` | `RRkW`, `RRkWh`, `RRThm` | 1 |
| `eul_yrs`, `rul_yrs` | `EUL`, `RUL` | **If RUL ≥ EUL, then EUL is set to RUL and RUL to 0.** So RUL > 0 always means 0 < RUL < EUL. |

That last rule is why dividing by `EUL` can never divide by zero.

### Step 2: The savings formulas

For each fuel *f* (where U₁/U₂ are the first- and second-baseline unit savings), the per-unit adjustment is `Qty × IR_f × RR_f`. Net savings multiply that by `(NTGR_f + @MEBens)`. `@MEBens` is a market-effects adder read from `CETJobs.MarketEffectBens`.

| Metric | Single baseline (RUL = 0) | Dual baseline (RUL > 0) |
|---|---|---|
| Annual | `adj × U₁` | `adj × (U₁·RUL + U₂·(EUL−RUL)) / EUL`, an average over the life |
| Lifecycle | `adj × U₁ × EUL` | `adj × (U₁·RUL + U₂·(EUL−RUL))` |
| First year | `adj × U₁ × min(1, EUL)` | `adj × (U₁·min(RUL,1) + U₂·(min(EUL,1) − RUL))` when RUL < 1 |

- Total kWh is site plus water (`kWh1 + kWhWater1`). Site and water are also reported separately.
- kW has no lifecycle value, because demand isn't summed over years.
- Results are summed by `PA, PrgID, CET_ID`.

### Step 3: `WeightedSavings`

Each measure's weight is its positive first-year gross savings divided by the program's total, with therms converted to kWh at 29.307 kWh/therm:

```
weight = (max(FYkWh,0) + 29.307·max(FYThm,0)) / Σ program (same)
```

If the program has no positive savings, each claim gets `1 / count`.

## Inputs to CalcSavings

Every per-row value comes from `Measure` fields, through `InputMeasurevw`. Three inputs don't:

| Input | Source | Effect |
|---|---|---|
| `@MEBens` | A parameter, or `CETJobs.MarketEffectBens` for the job if it isn't passed (0 if neither) | Added to every NTG ratio in the **net** savings: `(NTGR + @MEBens)`. Gross savings don't use it. |
| `@JobID` | A parameter | Only labels the output rows. |
| `@ThermConv` = 29.307111111 | Fixed in the procedure | Converts therms to kWh, used only for `WeightedSavings`. |

It doesn't use:

- `ProgramCost` or `InputProgramvw`
- avoided costs (`AvoidedCost*vw`)
- `Settingsvw` (discount rates)
- emissions or rate schedules
- `FirstYear` or `ClaimYearQuarter`, so no time value, no discounting and no quarter indexing

It uses `Measure` values *after* `InputMeasurevw` changes them, not the raw fields (see Step 1). So in Python, `calc_savings` can be a pure function of `list[Measure]` plus a `me_bens: float = 0` argument, as long as those defaults are applied first.

## How this compares to the facet models

### `Measure`

Used by `CalcSavings`: `ce_input_id`, `pa`, `prg_id`, `num_units`, the eight unit-savings fields, `ntgr_kw/kwh/therm`, the six installation/realization rates, `eul_yrs` and `rul_yrs`.

Not used by `CalcSavings`, though other procedures use them:

- `claim_year_quarter` (CE/emissions use it for quarter indexing)
- the `e3_*` mapping fields (avoided-cost keys)
- all cost and incentive fields
- `ntgr_cost`
- other costs and benefits
- rate schedules
- `meas_inflation`
- the descriptive fields

What a Python port needs to carry over:

1. **The view's defaults belong in the Python model or the calculation layer.** In Pydantic, a missing value is `None`, but SQL treats a missing NTG/IR/RR as 1 and missing savings as 0. A `model_validator` or a separate "normalized measure" step could apply the NTG fallback chain and the RUL ≥ EUL swap.
2. **The `*_id` fields aren't read by the calculation.** `ntg_id`, `eul_id` and `gsia_id` are only labels; the engine reads the numeric values.
3. **`Measure.pa` is optional, but the procedure groups by it and the allocation keys depend on it.** Leaving it `None` would give results that aren't keyed correctly.

### `ProgramCost`

`CalcSavings` never reads program costs. Program costs come in through `InputProgramvw` in `CalcCE` and `CalcCost`. In `CalcCE` (around [line 2114](stored_procedures_v25.1/dbo.CalcCE.StoredProcedure.sql#L2114)), costs are split across measures by **positive benefits**, using the same pattern of a positive-share ratio and an even split as the fallback. They are not split by `WeightedSavings`.

So in v25.1, `WeightedSavings` is only computed and saved by `SaveSavings`. Its comment says "divide program costs evenly", but nothing in the engine reads it. It's probably kept for savings-only runs (`SavingsOnly = 1`) or for downstream reporting. A `ProgramCost` allocator in facet needs to pick one of the two allocation methods.

## Source of EUL and RUL

Both are inputs. They come from the `EUL_Yrs` and `RUL_Yrs` columns of the measure input file, one value per measure row. The CET doesn't look them up or calculate them.

**How they reach `CalcSavings`:**

1. The caller's measure table is exposed as `SourceMeasurevw`.
2. `MappingMeasurevw` renames the columns: `EUL_Yrs` becomes `EUL` and `RUL_Yrs` becomes `RUL`.
3. `InputMeasurevw` applies the defaults and the swap: missing values become 0, and if RUL ≥ EUL, EUL is set to RUL and RUL to 0.
4. `CalcSavings` uses the cleaned `EUL` and `RUL`.

In facet, they're `Measure.eul_yrs` and `Measure.rul_yrs`.

**Where the values come from originally:** [database/create_tables/measure.sql:49-52](database/create_tables/measure.sql#L49-L52) pairs each value with an ID:

- `EUL_ID` with `EUL_Yrs`, which must be between 0 and 40 years.
- `RUL_ID` with `RUL_Yrs`, which must be between 0 and 30 years.

The `CedarsNumRange` constraints suggest this follows CPUC's CEDARS claim format. If so, the ID likely points to a published useful-life entry (DEER or eTRM), and the program administrator copies that entry's years onto the claim. This is an inference from the schema; nothing in this repo holds an EUL/RUL lookup table, and the engine never resolves the IDs.

**What they mean:**

- **EUL** (effective useful life) is how long the measure keeps saving energy.
- **RUL** (remaining useful life) applies to early replacement. It's how long the old equipment would have lasted. For those RUL years, savings are measured against the existing equipment (first baseline). For the remaining EUL − RUL years, they're measured against standard new equipment (second baseline). RUL = 0 means there is only one baseline.

`ValidateInput` warns when RUL ≥ EUL, RUL > EUL/3, or the RUL and second-baseline savings don't agree. It only warns and doesn't fix anything; the swap in `InputMeasurevw` is the only thing that changes the values.

## Quirks to know before porting

1. **It clears `SavedSavings` entirely.** Line 513, `DELETE FROM SavedSavings`, removes every row, not just this job's. `SaveSavings` itself deletes only `WHERE JobID = @JobID`. When `@CETDataDbName` is blank, saved results live in the core database, so this may erase earlier jobs' savings. Check with the database owner whether that's intended.
2. **The weight update joins only on `CET_ID`.** At [line 508](stored_procedures_v25.1/dbo.CalcSavings.StoredProcedure.sql#L508), the update matches rows on `CET_ID` alone, while the insert grouped by `PA, PrgID, CET_ID`. If one `CET_ID` appears under two programs, the weights can collide. Also, `SavingsSUM` groups by `PrgID` without `PA`.
3. **The first-year conditions don't match each other.** `FirstYearGrosskWh` uses `RUL >= 1` and `RUL <= 1` (line 250), while the other columns use `> 1` and `< 1`. They give the same result because of the view's normalization and the `ELSE 1` fallback. A port should use one consistent rule, for example a single `first_year_fractions(eul, rul)` helper.
4. **Some names don't match.** The aliases `AnnualGrossTherms` and `LifecycleGrossTherms` differ from the column names (`...Thm`). This does no harm because the insert matches columns by position, but use one name in Python.
5. **One sort is pointless.** The `ORDER BY` on `INSERT … SELECT` (line 435) has no effect.
6. **The procedure works on shared tables.** It depends on views that other procedures rewrite before each run and on shared `Output*` tables. A Python version can just be a pure function that takes a list of `Measure` objects and returns savings rows.
