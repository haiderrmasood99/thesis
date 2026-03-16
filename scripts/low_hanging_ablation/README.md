# Low-Hanging Ablation Runners

This folder contains separate runnable launchers for three low-risk thesis ablations, each with built-in parallel subprocess execution and structured outputs.

## Point 1: Entropy Coefficient (Fertilization)

Script:

`python scripts/low_hanging_ablation/run_point1_entropy_ablation.py`

Default sweep:
- methods: `PPO`
- seeds: `0,1,2`
- weather: `fixed,random`
- entropy: `0.0,0.01`

## Point 2: Hierarchical Blocked-Nutrient Penalty

Script:

`python scripts/low_hanging_ablation/run_point2_hierarchical_shaping_ablation.py`

Default sweep:
- methods: `PPO,A2C`
- seeds: `0,1,2`
- weather: `fixed,random`
- blocked penalty: `0.0,0.02,0.05`

## Point 3: Nutrient-Cost Weight (Fertilization)

Script:

`python scripts/low_hanging_ablation/run_point3_nutrient_cost_weight_ablation.py`

Default sweep:
- methods: `PPO`
- seeds: `0,1,2`
- weather: `fixed,random`
- nutrient cost weight: `0.8,1.0,1.2`

## Run All Points Together

Script:

`python scripts/low_hanging_ablation/run_all_low_hanging_points.py`

Useful flags:
- `--point-workers 2` controls parallel workers inside each point script
- `--parallel-points 2` controls how many point scripts run at the same time
- `--without-tracking` runs with local no-op tracking
- `--wandb-project Thesis-Final` sets shared W&B project
- `--dry-run` prints and records planned commands without executing training

## Output Layout

By default, outputs go under:

`artifacts/final_successful_runs/low_hanging_ablation/`

Each point writes:
- `summary_json/*.json` per run (standardized summary)
- `logs/*.log` per subprocess
- `run_summary.csv` with status, timings, and key metrics

Point 2 also writes:
- `thesis_reports/*/` per run (hierarchical reporting artifacts)

