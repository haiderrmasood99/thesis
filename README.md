# CyclesGym Thesis Repo

This repository contains the runtime code, frozen artifacts, and thesis workspace for the Pakistan-focused CyclesGym thesis experiments.

Start with [`docs/README.md`](docs/README.md) for the active documentation set.

## Canonical Final Reporting

The authoritative final evidence set is:

- `artifacts/final_successful_runs/final_113/`
- `artifacts/final_successful_runs/final_113/reporting/`

That reporting directory is the single source of truth for:

- `run_level_metrics.csv`
- `grouped_metrics.csv`
- `statistical_tests.csv`
- `artifact_completeness_audit.csv`
- `final_reporting_summary.json`

Use those outputs for final reporting, thesis tables, and defense preparation. Do not treat `runs/experiment_summaries/` as the authoritative final benchmark surface.

## Core Layout

- `cycles/`: CYCLES simulator binaries and localized input files
- `cyclesgym/`: Python package code
- `experiments/`: training and inference entrypoints
- `scripts/build_final_reports.py`: canonical final report builder
- `run_experiments_7_3_2026.py`: main consolidated experiment runner
- `run_hierarchical_guarded_parallel.py`: guarded hierarchical rerun launcher
- `Local Files and Folders/Thesis Main Working/`: LaTeX thesis workspace

## Installation

```bash
conda create -yn cyclesgym python=3.8
conda activate cyclesgym
pip install -e .
pip install -e .[SOLVERS]
```

## Runtime Outputs

Active local runtime outputs still appear under:

- `wandb/`
- `runs/experiment_summaries/`
- `runs/train_logs/`
- `runs/thesis_reports/`
- `runs/vec_normalize_*.pkl`

Those folders are useful for execution and debugging. They are not the canonical final reporting layer.

## Archived Material

Historical thesis drafts, notebooks, exports, demo assets, and older local outputs are kept under [`Local Files and Folders/`](Local%20Files%20and%20Folders/).
