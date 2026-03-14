# CyclesGym Thesis Repo

This repository contains the runtime code for the Cycles-based reinforcement learning experiments.
The root has been cleaned to keep only the files needed to install, train, evaluate, and rerun the core experiments.

Start with [`docs/README.md`](docs/README.md) for the push-ready documentation set.

Historical thesis drafts, notebooks, exports, demo assets, and old local outputs were moved into
[`Local Files and Folders/`](Local%20Files%20and%20Folders/).

## Core Layout

- `cycles/`: Cycles simulator binaries and input files
- `cyclesgym/`: Python package code
- `experiments/`: training and inference entrypoints
- `scripts/build_pakistan_price_series.py`: retained data-prep utility
- `run_experiments_7_3_2026.py`: main consolidated experiment runner
- `run_hierarchical_guarded_parallel.py`: hierarchical rerun launcher
- `run_all_2.py`, `run_all_experiments.py`: compatibility wrappers

## Installation

```bash
conda create -yn cyclesgym python=3.8
conda activate cyclesgym
pip install -e .
pip install -e .[SOLVERS]
```

## Runtime Outputs

New local artifacts are written to:

- `wandb/`: W&B local run folders and checkpoint artifacts
- `runs/experiment_summaries/`: aggregated CSV/JSON summaries
- `runs/train_logs/`: JSONL step and rollout logs
- `runs/thesis_reports/`: hierarchical reporting artifacts
- `runs/vec_normalize_*.pkl`: normalization statistics for reload/evaluation

## Archived Material

Use [`Local Files and Folders/README.md`](Local%20Files%20and%20Folders/README.md) for the archived thesis and local-output inventory.
