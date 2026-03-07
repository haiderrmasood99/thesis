# Thesis Context Handoff

- Date: 2026-03-06 (Asia/Karachi)
- Repository: `C:/Users/Haider/Desktop/CYCLES GYM WORKING/thesis_new/thesis`
- Thesis title: **Optimizing Agricultural Resource Allocation through Reinforcement Learning: A Cost-Driven Approach to Crop Efficiency Enhancement in Pakistan**

## 1. Current Repository Purpose

This repo provides a Gym/Gymnasium-compatible RL interface (`cyclesgym`) around the CYCLES crop simulator (`cycles/`).  
Main thesis-relevant use cases currently implemented:

1. Nitrogen fertilization optimization (weekly decisions).
2. Crop planning / rotation decisions (yearly decisions).
3. Weather uncertainty via shuffled historical weather years.
4. Pakistan-focused weather/soil/control defaults.

## 2. Documentation Entry Points

1. Primary consolidated docs: `final_docs/README.md`
2. Setup/run docs: `final_docs/01_Setup_and_First_Run.md`
3. Architecture: `final_docs/03_Architecture_and_Code_Map.md`
4. RL + experiments: `final_docs/05_Training_Algorithms_and_Experimentation.md`
5. Thesis defense framing: `final_docs/07_Thesis_Defense_Pack.md`
6. Gaps/future work: `final_docs/08_Gaps_and_Future_Work.md`

## 3. Core Thesis-Relevant Code Map

1. Base env lifecycle: `cyclesgym/envs/common.py`
2. Fertilization env: `cyclesgym/envs/corn.py`
3. Crop planning env: `cyclesgym/envs/crop_planning.py`
4. Action implementers (fertilizer/planter): `cyclesgym/envs/implementers.py`
5. Rewards/economics: `cyclesgym/envs/rewarders.py`, `cyclesgym/utils/pricing_utils.py`
6. Constraints/environmental costs: `cyclesgym/envs/constrainers.py`
7. Weather generation: `cyclesgym/envs/weather_generator.py`
8. Fertilization training pipeline: `experiments/fertilization/train.py`
9. Crop planning training pipeline: `experiments/crop_planning/train.py`
10. Inference/demo: `demo/inference_engine.py`, `demo/app.py`

## 4. Pakistan Data Assets in Repo

1. Weather (2005-2024): `cycles/input/Pakistan_Site_final.weather`
2. Soil profile: `cycles/input/Pakistan_Soil_final.soil`
3. Operations baseline: `cycles/input/Pakistan_Corn_final.operation`
4. Raw weather source CSV (NASA POWER derived): `cycles/input/power_islamabad_2005_2024.csv`
5. SoilGrids raw JSON snapshots:
   - `cycles/input/soilgrids_islamabad_raw.json`
   - `cycles/input/soilgrids_islamabad_hydro_raw.json`
6. Soil fetching helper script: `soildata.py`

## 5. Bug-Fix Session Status (This Session)

Detailed activity log is in `Changes/BUG_FIX_LOG.md`.  
Summary:

### Fixed in code

1. Observation-space high bound bug fixed.
   - File: `cyclesgym/envs/crop_planning.py`
2. Fertilization collision detection key fixed (`FIXED_FERTILIZATION`).
   - File: `cyclesgym/envs/implementers.py`
3. Planter "is new action" logic fixed (`!=` instead of `==`).
   - File: `cyclesgym/envs/implementers.py`
4. Incremental nutrient mass update corrected to use prior absolute mass.
   - File: `cyclesgym/envs/implementers.py`
5. Zero-total-mass guard added for fertilizer operation creation.
   - File: `cyclesgym/envs/implementers.py`
6. Empty-data fallback added in leaching constrainer (prevents undefined variable path).
   - File: `cyclesgym/envs/constrainers.py`
7. Callback eval log-path collisions fixed (`eval_train_det`, `eval_train_sto` separated).
   - File: `experiments/fertilization/train.py`
8. Weather year bounds made dynamic from Pakistan weather file.
   - File: `experiments/fertilization/train.py`
9. Crop-planning `_evaluate_policy` unpack mismatch fixed (6 outputs handled).
   - File: `experiments/crop_planning/train.py`
10. Crop-planning evaluation week-table made dynamic.
   - File: `experiments/crop_planning/train.py`
11. Implementer collision unit test updated to match corrected behavior.
   - File: `cyclesgym/tests/test_implementers.py`

### Verification outcomes

1. Syntax compile:
   - `python -m compileall cyclesgym experiments/fertilization/train.py experiments/crop_planning/train.py`
   - Result: PASS
2. Unit tests:
   - `pytest cyclesgym/tests/test_implementers.py cyclesgym/tests/test_rewarders.py -q`
   - Result: PASS (`6 passed`)
3. Integration-style tests invoking external `./Cycles` binary:
   - `test_crop_planning.py` and one case in `test_random_weather.py` fail in this environment with:
   - `PermissionError: [WinError 5] Access is denied`
   - Interpretation: environment execution permission blocker, not Python patch syntax issue.

### Are all bugs resolved?

1. **Code-level logic bugs identified in this session: resolved.**
2. **Full end-to-end simulator execution validation: not fully resolved due host permission blocking execution of `./Cycles`.**

## 6. Working Tree / Artifacts

Current modified tracked files:

1. `cyclesgym/envs/constrainers.py`
2. `cyclesgym/envs/crop_planning.py`
3. `cyclesgym/envs/implementers.py`
4. `cyclesgym/tests/test_implementers.py`
5. `experiments/crop_planning/train.py`
6. `experiments/fertilization/train.py`

Untracked files currently present (generated during tests/logging):

1. `Changes/` (new handoff + bug log folder)
2. `cycles/input/CropPlanningTest.ctrl`
3. `cycles/input/CropPlanningTest.operation`
4. `cycles/input/weather0.weather`

## 7. Pakistan-Alignment Notes

1. Current default operation uses fixed corn timings (e.g., DOY 75).
2. Crop-planning action mapping currently supports planting DOY range anchored to spring-window logic.
3. For strict thesis alignment, season windows should be explicitly constrained by Pakistan crop calendars (Kharif/Rabi, crop-specific windows).

## 8. External Data/Policy Sources Already Identified

These are suitable for thesis-grounded extensions:

1. PBS crop calendars (Kharif/Rabi)
2. KP agriculture extension production technology PDFs (maize/wheat)
3. NFDC annual fertilizer review (fertilizer prices/offtake)
4. Pakistan Economic Survey (agriculture/fertilizer context)
5. NASA POWER API (weather)
6. ISRIC SoilGrids API (soil properties)
7. FAO/FAOSTAT (supporting price/agri series where needed)

## 9. Recommended Next Implementation Sequence

1. Enable `./Cycles` execution in environment and rerun full tests.
2. Clean generated test artifacts (`CropPlanningTest.*`, `weather0.weather`) if not needed.
3. Complete hierarchical integration (crop planning + fertilization) in a single experiment pipeline.
4. Replace Pakistan placeholder economics with year-varying fertilizer/crop series where available.
5. Add explicit policy/report outputs for N/P/K split, per-nutrient cost, and seasonal compliance metrics.
6. Add ablations for thesis defense (N vs NPK, season-masked vs unmasked, single-site vs multi-site).

## 10. Minimal Resume Commands for New Thread

```bash
# from repo root
git status --short
python -m compileall cyclesgym experiments/fertilization/train.py experiments/crop_planning/train.py
pytest cyclesgym/tests/test_implementers.py cyclesgym/tests/test_rewarders.py -q
pytest cyclesgym/tests/test_crop_planning.py -q
pytest cyclesgym/tests/test_random_weather.py -q
```

If crop-planning/random-weather tests still fail with `WinError 5`, fix simulator execution permissions first.

## 11. Latest Thesis Enhancement Started

1. Pakistan season-aware crop-planning mapping was added in a backward-compatible way:
   - new utility: `cyclesgym/utils/pakistan_crop_calendar.py`
   - optional env flags: `use_pakistan_crop_calendar`, `crop_calendar_windows`
   - planter now supports crop-specific DOY windows when configured
2. Full implementation notes:
   - `Changes/THESIS_IMPLEMENTATION_01_SEASON_ALIGNMENT.md`

## 12. New-Thread Prompt Seed

Use this in a new Codex thread:

> Read `Changes/THESIS_CONTEXT_HANDOFF.md`, `Changes/BUG_FIX_LOG.md`, and `Changes/THESIS_IMPLEMENTATION_02_PAK_PRICE_LOCALIZATION_NPK_SCAFFOLD.md`. Continue from current modified state. First, make CYCLES executable invocation work (`WinError 5` blocker), rerun full tests, then implement Step 3 (hierarchical crop-planning + fertilization integration with NPK economics) in a backward-compatible way.

## 13. Latest Thesis Enhancement Continued (Step 2)

Step 2 has now been implemented in a backward-compatible way:

1. Pakistan-localized economics scaffolding:
- `cyclesgym/utils/pricing_utils.py`
- Added profile system:
  - `us_legacy` (default)
  - `pakistan_baseline` (opt-in)

2. NPK-ready reward/action scaffolding:
- `cyclesgym/envs/rewarders.py`
- `cyclesgym/envs/implementers.py`
- `cyclesgym/envs/constrainers.py`
- `cyclesgym/envs/corn.py` (new optional `nutrient_action_mode='NPK'`)

3. Added new targeted tests:
- `cyclesgym/tests/test_constrainers.py`
- `cyclesgym/tests/test_pricing_utils.py`
- extended:
  - `cyclesgym/tests/test_rewarders.py`
  - `cyclesgym/tests/test_implementers.py`

4. Step 2 implementation note:
- `Changes/THESIS_IMPLEMENTATION_02_PAK_PRICE_LOCALIZATION_NPK_SCAFFOLD.md`

5. Verification status:
- `pytest cyclesgym/tests/test_rewarders.py cyclesgym/tests/test_implementers.py cyclesgym/tests/test_constrainers.py cyclesgym/tests/test_pricing_utils.py -q`
- Result: `21 passed`, `1 warning`

If opening a new thread, use this updated prompt seed:

> Read `Changes/THESIS_CONTEXT_HANDOFF.md`, `Changes/BUG_FIX_LOG.md`, and `Changes/THESIS_IMPLEMENTATION_02_PAK_PRICE_LOCALIZATION_NPK_SCAFFOLD.md`. Continue with Step 3 (hierarchical integration + Pakistan year-varying fertilizer/crop economics) while preserving backward compatibility and rerunning targeted tests after each change.

## 14. Step 3 Started and Integrated

Step 3 has now been started with code + verification:

1. New hierarchical env:
- `cyclesgym/envs/hierarchical.py`
- `HierarchicalCropPlanningFertilization` combines:
  - yearly crop planning actions,
  - weekly fertilization actions,
  - NPK economics via profile-aware rewarders.

2. Training entrypoint wiring:
- `experiments/crop_planning/train.py`
- new CLI switch:
  - `--hierarchical True`

3. Test-suite execution blockers resolved:
- cross-platform CYCLES invocation fixed in integration tests (uses `CYCLES_EXE`).
- Gymnasium 5-tuple step handling fixed in test and utility paths.
- plotting hang removed from `compare_env()` unless explicitly enabled.
- manual-sim parity restored via explicit legacy input-file config in tests.

4. Verification:
- `pytest cyclesgym/tests/test_crop_planning.py cyclesgym/tests/test_env.py cyclesgym/tests/test_random_weather.py cyclesgym/tests/test_hierarchical_env.py -q`
- Result: `10 passed`
- Step 1/2 regression set also passing:
  - `21 passed`

5. Step 3 implementation note:
- `Changes/THESIS_IMPLEMENTATION_03_HIERARCHICAL_INTEGRATION_AND_TEST_FIXES.md`

Updated prompt seed for next thread:

> Read `Changes/THESIS_CONTEXT_HANDOFF.md`, `Changes/BUG_FIX_LOG.md`, `Changes/THESIS_IMPLEMENTATION_02_PAK_PRICE_LOCALIZATION_NPK_SCAFFOLD.md`, and `Changes/THESIS_IMPLEMENTATION_03_HIERARCHICAL_INTEGRATION_AND_TEST_FIXES.md`. Continue with Step 4 by adding hierarchical experiment reporting (yearly crop decisions, weekly N/P/K actions, per-nutrient cost decomposition, and season-window compliance metrics) while preserving backward compatibility.

## 15. Superseding Final Verification Update (2026-03-07)

This section supersedes earlier notes about unresolved `WinError 5` execution blockers.

1. Integration execution blocker resolved:
   - Tests now invoke CYCLES using `CYCLES_PATH.joinpath(CYCLES_EXE)` instead of hardcoded `./Cycles`.
2. Step 3 integrated into training pipeline:
   - new env `HierarchicalCropPlanningFertilization`
   - opt-in entrypoint wiring in `experiments/crop_planning/train.py` via `--hierarchical True`
3. Full test status:
   - `pytest cyclesgym/tests -q`
   - Result: `53 passed`, warnings only (run on 2026-03-07).
4. Additional compatibility fixes included in this final pass:
   - `cyclesgym/tests/test_policies.py` now uses `gym_compat` imports.
   - `cyclesgym/tests/test_managers.py` uses robust dataframe/string assertions across pandas/CRLF variations.
5. Working-tree hygiene:
   - Restored `cycles/input/weather0.weather` (tracked file).
   - Removed generated test artifacts from output folders.

### New Thread Prompt Seed (Current)

> Read `Changes/THESIS_CONTEXT_HANDOFF.md`, `Changes/BUG_FIX_LOG.md`, `Changes/THESIS_IMPLEMENTATION_01_SEASON_ALIGNMENT.md`, `Changes/THESIS_IMPLEMENTATION_02_PAK_PRICE_LOCALIZATION_NPK_SCAFFOLD.md`, and `Changes/THESIS_IMPLEMENTATION_03_HIERARCHICAL_INTEGRATION_AND_TEST_FIXES.md`. Assume Step 1-3 are integrated and tests are green (`53 passed`). Continue with Step 4: hierarchical reporting/analysis outputs (yearly crop decisions, weekly N/P/K actions, nutrient cost decomposition, season-window compliance metrics), keeping backward compatibility.

## 16. Step 4 Completed (2026-03-07)

Step 4 and associated hardening tasks are now implemented and verified.

1. Reporting layer delivered:
   - `cyclesgym/utils/thesis_reporting.py` callback writes:
     - `weekly_npk_log.csv`
     - `yearly_crop_decisions.csv`
     - `season_window_compliance.csv`
     - `reporting_summary.json`
   - `cyclesgym/envs/hierarchical.py` now emits structured report keys in `info`.
   - `experiments/crop_planning/train.py` auto-attaches reporting callback for hierarchical runs.

2. Data hardening delivered:
   - `scripts/build_pakistan_price_series.py` builds year-varying Pakistan crop/fertilizer series from FAOSTAT + NFDC.
   - `cyclesgym/resources/pricing/pakistan_yearly_series.json` added.
   - `cyclesgym/utils/pricing_utils.py` now loads these year-varying series.
   - Corn silage pricing no longer uses legacy US-ratio placeholder; it now uses a Pakistan-maize-linked proxy series.

3. Thesis-strength experiment pipeline delivered:
   - `experiments/fertilization/train.py` and `experiments/crop_planning/train.py` now emit standardized per-run summary JSON (`--summary-json`).
   - `run_all_2.py` now:
     - injects `--summary-json` per run,
     - supports hierarchical matrix branch,
     - includes standardized RL-vs-baseline/holdout columns in summary CSV.

4. Verification:
   - `pytest cyclesgym/tests -q` -> `57 passed`, warnings only.

### New Thread Prompt Seed (Updated)

> Read `Changes/THESIS_CONTEXT_HANDOFF.md`, `Changes/BUG_FIX_LOG.md`, `Changes/THESIS_IMPLEMENTATION_01_SEASON_ALIGNMENT.md`, `Changes/THESIS_IMPLEMENTATION_02_PAK_PRICE_LOCALIZATION_NPK_SCAFFOLD.md`, `Changes/THESIS_IMPLEMENTATION_03_HIERARCHICAL_INTEGRATION_AND_TEST_FIXES.md`, and `Changes/THESIS_IMPLEMENTATION_04_REPORTING_DATA_HARDENING_AND_MATRIX_STANDARDIZATION.md`. Assume Steps 1-4 are integrated and tests are green (`57 passed`). Continue with Step 5: statistical significance layer (confidence intervals/hypothesis tests), multi-zone transfer experiments, and thesis defense figure pack generation from standardized summary outputs.

## 17. Runtime Hardening Follow-up (2026-03-07)

After Step 4 completion, additional runtime hardening was added without changing thesis semantics:

1. Training entrypoints now support no-tracking execution:
   - `experiments/crop_planning/train.py`
   - `experiments/fertilization/train.py`
   - Added CLI flag: `--without-tracking`
   - Added safe no-op W&B fallback for environments lacking a functional `wandb` install.
   - Disabled SB3 tensorboard logger in no-tracking mode to avoid hard dependency on tensorboard.

2. Backward-compatibility fix in fertilization wrappers:
   - `experiments/fertilization/corn_soil_refined.py`
   - Initialized attributes required by updated `Corn` nutrient-mode internals (e.g., `nutrient_action_mode`, `n_nh4_rate`, etc.).
   - Fixed runtime error in baseline/eval paths:
     - `AttributeError: 'CornSoilCropWeatherObs' object has no attribute 'nutrient_action_mode'`.

3. Verification after hardening:
   - `pytest cyclesgym/tests -q` -> `57 passed, 8 warnings`.

4. Smoke-run note:
   - Full simulation smoke commands are long in this environment and timed out at the 20-minute command cap.
   - Partial Step 4 reporting artifacts were confirmed to be emitted before timeout:
     - `runs/thesis_reports/smoke_hier/weekly_npk_log.csv`
     - `runs/thesis_reports/smoke_hier/yearly_crop_decisions.csv`

## 18. Fertilization NPK + Pakistan Final-Run Readiness (2026-03-07)

This follow-up closes the remaining caveat that fertilization wrappers were effectively N-only and US-legacy-biased by default.

1. Fertilization wrappers now preserve NPK mode and Pakistan pricing end-to-end:
   - `experiments/fertilization/corn_soil_refined.py`
   - Added pass-through for:
     - `nutrient_action_mode`
     - `price_profile`
     - `maxP`, `maxK`, `p_actions`, `k_actions`, `n_nh4_rate`

2. Fertilization trainer defaults now align to thesis Pakistan setup:
   - `experiments/fertilization/train.py`
   - Defaults:
     - `nutrient_action_mode="NPK"`
     - `price_profile="pakistan_baseline"`
   - New CLI options:
     - `--nutrient-action-mode`
     - `--price-profile`
     - `--maxN --maxP --maxK --p-actions --k-actions --n-nh4-rate`
   - Baseline evaluation supports NPK mode by mapping legacy N-only baseline schedules into NPK action vectors.
   - Fixed logical issue in holdout evaluation (`eval_nh`) to evaluate on holdout/test env.

3. Matrix runner now launches fertilization in Pakistan NPK mode by default:
   - `run_all_2.py`
   - Added fertilization matrix options:
     - `--fert-nutrient-action-mode` (default `NPK`)
     - `--fert-price-profile` (default `pakistan_baseline`)
     - `--fert-maxN --fert-maxP --fert-maxK --fert-p-actions --fert-k-actions --fert-n-nh4-rate`

4. Policy helper compatibility fix:
   - `cyclesgym/policies/dummy_policies.py`
   - `OpenLoopPolicy.predict()` now returns correct batched action shapes for vectorized MultiDiscrete envs.

5. Data refresh:
   - Re-ran `python scripts/build_pakistan_price_series.py`.
   - Refreshed:
     - `cyclesgym/resources/pricing/pakistan_yearly_series.json`
   - Live sources used:
     - FAOSTAT Prices bulk zip
     - NFDC fertilizer prices table

6. Verification:
   - `pytest cyclesgym/tests -q` -> `59 passed, 8 warnings`
   - `python run_all_2.py --dry-run --include-hierarchical --include-baseline` -> PASS
   - NPK wrapper smoke check (`CornSoilRefined`, reset + step) -> PASS (`MultiDiscrete([11 11 11])`)

### New Thread Prompt Seed (Current)

> Read `Changes/THESIS_CONTEXT_HANDOFF.md`, `Changes/BUG_FIX_LOG.md`, `Changes/THESIS_IMPLEMENTATION_01_SEASON_ALIGNMENT.md`, `Changes/THESIS_IMPLEMENTATION_02_PAK_PRICE_LOCALIZATION_NPK_SCAFFOLD.md`, `Changes/THESIS_IMPLEMENTATION_03_HIERARCHICAL_INTEGRATION_AND_TEST_FIXES.md`, `Changes/THESIS_IMPLEMENTATION_04_REPORTING_DATA_HARDENING_AND_MATRIX_STANDARDIZATION.md`, and `Changes/THESIS_IMPLEMENTATION_05_FERTILIZATION_NPK_PAKISTAN_FINAL_RUN_READINESS.md`. Assume Steps 1-5 are integrated and tests are green (`59 passed`). Proceed with final experiment execution and thesis figure/statistics generation from standardized summary outputs.
