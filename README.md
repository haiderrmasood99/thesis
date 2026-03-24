# CyclesGym Thesis Repo

This repository contains the runtime code, frozen final evidence packs, and thesis workspace for the Pakistan-focused CyclesGym thesis experiments.

Start with [docs/README.md](docs/README.md).

## Canonical Final Evidence (Use This)

The authoritative completed evidence sets are:

- `artifacts/final_successful_runs/final_113/`
- `artifacts/final_successful_runs/final_113/reporting/`
- `artifacts/final_successful_runs/final_42_ablation/`
- `artifacts/final_successful_runs/final_42_ablation/reporting/low_hanging_ablation/`

Current canonical counts:

- final matrix rows: `113`
- ablation rows: `42`

## Important Note About Older LaTeX Status Snapshot

Some extracted LaTeX status tables under `Refrence Material/Latex/extracted_latex/` still reflect an older provisional snapshot.
For final thesis reporting and defense claims, use the completed frozen `final_113` and `final_42_ablation` packs above.

## Core Layout

- `cycles/`: CYCLES simulator binaries and localized input files
- `cyclesgym/`: Python package code
- `experiments/`: training and inference entrypoints
- `run_experiments_7_3_2026.py`: consolidated experiment runner
- `docs/`: active project documentation
- `Refrence Material/`: reference PDFs/PPTX and LaTeX source exports
- `artifacts/final_successful_runs/`: frozen completed evidence packs

## Installation

```bash
conda create -yn cyclesgym python=3.8
conda activate cyclesgym
pip install -e .
pip install -e .[SOLVERS]
```

## Runtime Outputs

Active local runtime outputs appear under:

- `wandb/`
- `runs/experiment_summaries/`
- `runs/train_logs/`
- `runs/thesis_reports/`
- `runs/vec_normalize_*.pkl`

These are useful for execution/debugging. Final thesis claims should cite frozen completed packs under `artifacts/final_successful_runs/`.
