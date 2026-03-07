# Thesis Implementation Update 04: Reporting Layer + Data Hardening + Matrix Standardization

- Date: 2026-03-07 (Asia/Karachi)
- Goal:
  1. Add Step 4 reporting outputs for hierarchical crop-planning + fertilization runs.
  2. Harden Pakistan economics with year-varying crop/fertilizer series.
  3. Standardize thesis matrix execution with RL-vs-baseline comparable metrics.

## What Was Implemented

1. Step 4 reporting layer for hierarchical runs:
- `cyclesgym/envs/hierarchical.py`
  - step `info` now includes structured report keys:
    - weekly N/P/K masses (`report_n_kg`, `report_p_kg`, `report_k_kg`)
    - nutrient-wise costs (`report_cost_n`, `report_cost_p`, `report_cost_k`, `report_cost_total`)
    - yearly crop decision fields (crop, planting DOY/end DOY, SMC)
    - season-window compliance fields (`report_window_*`, `report_window_compliant`)
- `cyclesgym/utils/thesis_reporting.py` (new)
  - `HierarchicalThesisReportCallback` writes:
    - `weekly_npk_log.csv`
    - `yearly_crop_decisions.csv`
    - `season_window_compliance.csv`
    - `reporting_summary.json`
- `experiments/crop_planning/train.py`
  - hierarchical runs automatically attach reporting callback (configurable).

2. Pakistan data hardening (year-varying economics):
- `scripts/build_pakistan_price_series.py` (new)
  - downloads and builds yearly series from online primary sources.
- `cyclesgym/resources/pricing/pakistan_yearly_series.json` (new generated data asset)
  - Pakistan yearly crop series (maize, soybean) in LCU/tonne.
  - Pakistan yearly fertilizer-derived nutrient prices (N/P/K) in Rs/kg nutrient.
  - Corn silage proxy linked to Pakistan maize series (`0.35 * maize`), replacing legacy US-ratio scaffolding.
- `cyclesgym/utils/pricing_utils.py`
  - now loads the generated Pakistan data file.
  - keeps runtime fallback if data file is unavailable.
  - exposes `lookup_year_value(...)` for consistent year fallback logic.

3. Thesis matrix + standardized RL-vs-baseline metrics:
- `experiments/crop_planning/train.py`
  - now evaluates baseline open-loop crop policies (when action space is MultiDiscrete).
  - writes standardized per-run summary JSON (`--summary-json`).
  - logs uplift vs best baseline deterministic return.
- `experiments/fertilization/train.py`
  - writes standardized per-run summary JSON (`--summary-json`).
  - baseline-only mode also emits structured summary.
- `run_all_2.py`
  - adds per-run `--summary-json` wiring automatically.
  - supports hierarchical crop-planning runs in matrix (`--include-hierarchical` / `--no-hierarchical`).
  - includes standardized metric columns in CSV:
    - deterministic/stochastic returns
    - best baseline return
    - uplift vs baseline
    - holdout return (fertilization)
  - tracks `hierarchical` flag per experiment row.

## Why This Matters (Layman Terms)

1. You can now explain not only *what* score the agent got, but *how* it made decisions:
- what crop it chose each year,
- how much N/P/K it applied each week,
- what each nutrient cost contributed,
- whether planting respected season windows.

2. Economics are now less static and more realistic for Pakistan:
- prices vary by year instead of using one fixed baseline.

3. Experiment outputs are thesis-ready:
- each run can emit machine-readable summary metrics,
- matrix CSV now directly supports RL-vs-baseline comparison.

## Online Data Sources / APIs Used

1. FAOSTAT Prices bulk dataset (Pakistan producer prices):
- https://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip

2. NFDC fertilizer historical price table (Pakistan):
- https://nfdc.gov.pk/Web-Page%20Updating/prices.htm

## Key New Usage

1. Refresh Pakistan yearly series:
```bash
python scripts/build_pakistan_price_series.py
```

2. Run matrix with standardized summaries (includes hierarchical by default):
```bash
python run_all_2.py --seeds 0,1,2 --fert-total-years 1000,3000,5000 --include-baseline
```

3. Run hierarchical crop-planning with reporting:
```bash
python experiments/crop_planning/train.py --hierarchical True --price_profile pakistan_baseline
```

## Verification

1. Compile:
- `python -m compileall` on all changed modules -> PASS

2. New/updated targeted tests:
- `pytest cyclesgym/tests/test_pricing_utils.py cyclesgym/tests/test_rewarders.py cyclesgym/tests/test_hierarchical_env.py cyclesgym/tests/test_thesis_reporting.py -q`
- Result: PASS

3. Full suite:
- `pytest cyclesgym/tests -q`
- Result: `57 passed`, warnings only.

## Post-Implementation Runtime Hardening

1. Training entrypoints now support no-tracking execution:
- `experiments/crop_planning/train.py` and `experiments/fertilization/train.py`
  - Added `--without-tracking`.
  - Added safe no-op W&B fallback for environments without a working `wandb` install.
  - Disabled SB3 tensorboard logger in no-tracking mode to avoid hard dependency on tensorboard.

2. Backward compatibility fix for fertilization wrapper env:
- `experiments/fertilization/corn_soil_refined.py`
  - Initialized attributes required by updated `Corn` nutrient-mode logic.
  - Fixed runtime error:
    - `AttributeError: 'CornSoilCropWeatherObs' object has no attribute 'nutrient_action_mode'`.

## Follow-up Note

Fertilization full NPK + Pakistan-default final-run readiness was completed in:
- `Changes/THESIS_IMPLEMENTATION_05_FERTILIZATION_NPK_PAKISTAN_FINAL_RUN_READINESS.md`
