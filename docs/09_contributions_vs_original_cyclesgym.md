# Contributions vs Original CyclesGym

This page summarizes the contribution delta between the original CyclesGym snapshot stored under `original_cycles_gym/cyclesgym/` and the thesis repository state in this workspace.

## Package-Level Delta

A direct file comparison of the package tree shows the current `cyclesgym/` package contains nine net additions over the original baseline snapshot:

- `envs/hierarchical.py`
- `resources/pricing/pakistan_yearly_series.json`
- `utils/gym_compat.py`
- `utils/pakistan_crop_calendar.py`
- `utils/thesis_reporting.py`
- `tests/test_constrainers.py`
- `tests/test_hierarchical_env.py`
- `tests/test_pricing_utils.py`
- `tests/test_thesis_reporting.py`

Those additions matter because they are not cosmetic. They add a hierarchical environment branch, Pakistan-specific localization assets, reporting helpers, compatibility helpers, and regression tests around the new thesis-facing logic.

## Repository-Level Delta

Compared with the original baseline snapshot, the thesis repo also adds a wider experiment and reporting layer around the package:

- `run_experiments_7_3_2026.py` for consolidated matrix execution
- `run_hierarchical_guarded_parallel.py` for corrected guarded hierarchical reruns
- `scripts/build_final_reports.py` for canonical reporting generation
- `docs/` as the active public documentation surface
- `artifacts/final_successful_runs/final_113/reporting/` as the frozen final evidence surface
- `cycles/` and localized data assets that wire the thesis stack to Pakistan-oriented simulator inputs

## What Value Was Added

| Area | Original CyclesGym baseline | Thesis repo contribution |
|---|---|---|
| Localization | generic simulator-facing package code | Pakistan-oriented weather, soil, crop-calendar, and yearly price integration |
| Decision scope | fertilization and crop planning environments only | guarded hierarchical planning branch plus thesis-specific control/report hooks |
| Economic realism | generic pricing utilities | yearly Pakistan crop and nutrient price series used in reward computation |
| Reporting | experiment outputs and W&B tracking | canonical frozen reporting pipeline with run-level, grouped, statistical, and audit outputs |
| Reproducibility | package docs and experiment scripts | thesis rebuild workflow from frozen evidence to tables, figures, and PDF |
| Verification | baseline environment tests | added tests for hierarchical env behavior, pricing utilities, constrainers, and thesis reporting |

## Safe Defense Framing

Use this wording in the defense:

> The thesis does not just rerun the original CyclesGym code. It extends the base repository into a Pakistan-oriented research stack with localized data inputs, NPK-aware economics, a hierarchical planning branch, a frozen 113-run evidence set, and a canonical reporting pipeline that rebuilds the thesis from auditable artifacts.

## Where To Point The Committee

- package code additions: `cyclesgym/`
- consolidated runners: `run_experiments_7_3_2026.py` and `run_hierarchical_guarded_parallel.py`
- canonical reporting layer: `artifacts/final_successful_runs/final_113/reporting/`
- public documentation: `docs/`
