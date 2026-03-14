# Setup and Usage

## Recommended Environment

```bash
conda create -yn cyclesgym python=3.8
conda activate cyclesgym
pip install -e .
pip install -e .[SOLVERS]
```

If you need to skip the post-install CYCLES binary step:

```bash
set CYCLESGYM_SKIP_CYCLES=1
```

## Quick Sanity Checks

1. Confirm the simulator files exist under `cycles/`.
2. Confirm the package imports:

```bash
python -c "import cyclesgym; print('cyclesgym import ok')"
```

3. Dry-run the consolidated matrix before long jobs:

```bash
python run_experiments_7_3_2026.py --dry-run --seeds 0 --fert-total-years 1000 --no-baseline --no-dqn --without-tracking
```

## Main Usage Commands

### Full Matrix Runner

```bash
python run_experiments_7_3_2026.py
```

Common useful variants:

```bash
python run_experiments_7_3_2026.py --dry-run
python run_experiments_7_3_2026.py --no-hierarchical --no-dqn --no-baseline
python run_experiments_7_3_2026.py --wandb-offline
python run_experiments_7_3_2026.py --without-tracking
```

### Hierarchical Guarded Reruns

```bash
python run_hierarchical_guarded_parallel.py --dry-run --methods PPO --seeds 0 --weather-modes fixed --without-tracking
python run_hierarchical_guarded_parallel.py --methods PPO,A2C --seeds 0,1,2 --weather-modes fixed,random
```

### Compatibility Wrappers

```bash
python run_all_2.py --dry-run
python run_all_experiments.py --dry-run
```

## What Gets Created During A Run

- `wandb/`: tracked run folders and model artifacts when W&B is enabled
- `runs/experiment_summaries/`: CSV and JSON summary outputs
- `runs/train_logs/`: detailed JSONL logs
- `runs/thesis_reports/`: hierarchical reporting outputs
- `runs/vec_normalize_*.pkl`: normalization statistics for evaluation and reuse

## Daily Usage Pattern

1. Dry-run the matrix.
2. Run the selected configuration.
3. Inspect `runs/experiment_summaries/` for summary CSV and JSON outputs.
4. Inspect `wandb/` or `runs/offline/` for checkpoints.
5. Promote only the best model artifacts you intend to keep long-term.

## Current Public Usage Boundary

The cleaned root no longer treats the old demo folder as part of the primary workflow.
The canonical public usage story is installation, matrix execution, reruns, and artifact/report management through the scripts that remain at the root.
