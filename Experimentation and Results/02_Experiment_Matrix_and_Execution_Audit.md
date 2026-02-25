# Experiment Matrix and Execution Audit

## Runner Intent

| Runner | Intended Scope | Planned Commands (Default) |
|---|---|---:|
| `run_all_experiments.py` | Mixed fertilization and crop planning baselines (PPO/A2C/DQN variants + baseline run) | 12 |
| `master_runner_run_all.2.py` | Additional fertilization PPO variants not covered by `run_all_experiments.py` | 8 |
| `run_all_2.py` | Full thesis matrix: fertilization + crop planning over methods, adaptation/weather modes, seeds, and budgets | 96 |

Notes:
- `run_all_2.py` evidence file `run_all_2_summary_dryrun.csv` confirms the 96-command plan.
- `master_runner_run_all.2.py` default excludes seed `0` coverage already handled elsewhere.

## Observed Run Evidence Window
- Earliest audited run: `run-20260223_211845-zyo19dh1`
- Latest audited run: `run-20260225_120700-xw0jtd6e`
- Date span: February 23, 2026 to February 25, 2026

## Execution Summary (From `wandb`)
- Total run folders audited: `64`
- `ok`: `44`
- `failed_traceback`: `16`
- `no_summary`: `4`

By domain:
- Fertilization: `48`
- Crop planning: `12`
- Unknown/incomplete metadata: `4`

## Train Log Audit (`runs/train_logs`)
- JSONL train logs found: `60`
- Logs with explicit `end` event: `49`
- Logs without `end` event: `11`

This aligns with partial/failed runs seen in traceback audit.

## `run_all_2` Coverage vs Plan
- Planned configs (dry-run matrix): `96`
- Observed in run metadata: `34`
- Successful and covered: `34`

Coverage gap summary:
- Missing many seed-0 entries for PPO in fertilization and crop planning.
- A2C coverage is heavily incomplete for the expanded `run_all_2` grid.

## Failure Signature Audit

| Failure Signature | Count | Typical Impact |
|---|---:|---|
| `subproc_eoferror` | 8 | Training process interruption during vectorized rollout |
| `weather_shuffle_empty_choice` | 4 | Weather sampling window issue (`np.random.choice` on empty set) |
| `dqn_eval_get_distribution_missing` | 2 | DQN evaluation path incompatible with policy distribution call |
| `reward_price_missing_year_2020` | 1 | Baseline-like run failed due missing year key in reward pricing |
| `dqn_unsupported_multidiscrete` | 1 | Crop-planning DQN incompatible with MultiDiscrete action space |

## Pakistan Data Confirmation
Code-level evidence indicates Pakistani weather/soil integration:
- Fertilization constants in `experiments/fertilization/train.py` reference `Pakistan_Site_final.weather` and Pakistan year bounds.
- Crop planning defaults in `experiments/crop_planning/train.py` reference `Pakistan_Site_final.weather` and `Pakistan_Soil_final.soil`.

Artifacts used for this audit are in `artifacts/`.
