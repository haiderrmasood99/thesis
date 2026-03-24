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

## Sanity Checks

1. Confirm simulator files exist under `cycles/`.
2. Confirm package import:

```bash
python -c "import cyclesgym; print('cyclesgym import ok')"
```

3. Dry-run the main matrix first:

```bash
python run_experiments_7_3_2026.py --dry-run --seeds 0 --fert-total-years 1000 --no-baseline --no-dqn --without-tracking
```

## Main Commands

### Broad Matrix

```bash
python run_experiments_7_3_2026.py
```

Useful variants:

```bash
python run_experiments_7_3_2026.py --dry-run
python run_experiments_7_3_2026.py --no-hierarchical --no-dqn --no-baseline
python run_experiments_7_3_2026.py --without-tracking
```

### Guarded Hierarchical Runs

```bash
python run_hierarchical_guarded_parallel.py --dry-run --methods PPO --seeds 0 --weather-modes fixed --without-tracking
python run_hierarchical_guarded_parallel.py --methods PPO,A2C --seeds 0,1,2 --weather-modes fixed,random
```

## Runtime Outputs

- `runs/experiment_summaries/`: local summary CSV/JSON outputs
- `runs/train_logs/`: detailed training logs
- `runs/thesis_reports/`: hierarchical reporting outputs (when enabled)
- `runs/vec_normalize_*.pkl`: normalization statistics
- `wandb/` or `runs/offline/`: checkpoints and tracking artifacts

## Recommended Daily Pattern

1. Dry-run the command set.
2. Execute selected jobs.
3. Validate generated summaries.
4. Track failures/retries explicitly.
5. Promote or archive models only with matching metadata.

## Thesis-Aligned Usage Rule

When writing thesis claims, do not treat dry-run definitions as completed evidence. Use completed run artifacts only, and separate historical context from latest-campaign claims.
