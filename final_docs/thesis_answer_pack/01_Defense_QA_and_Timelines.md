# 1) Commands, Timelines, and Defense Q&A (0 to 9)

This document answers your exact question list with evidence from code and existing run artifacts.

## A. Complete Experimentation Commands (From Zero)

### Phase 1: Setup

```powershell
conda env create -f environment.yml
conda activate cyclesgym
pip install -e .
pip install -e .[SOLVERS]
python install_cycles.py
```

### Phase 2: Optional W&B Separation (New project per thesis cycle)

This repo now supports environment-variable overrides for project names.

```powershell
$env:WANDB_ENTITY = "your_wandb_entity"
$env:WANDB_PROJECT_FERTILIZATION = "thesis_fertilization_v2"
$env:WANDB_PROJECT_CROP_PLANNING = "thesis_crop_planning_v2"
```

If you want both domains in one new project:

```powershell
$env:WANDB_PROJECT = "thesis_full_v2"
```

### Phase 3: Smoke Tests

```powershell
python experiments/fertilization/train.py --total-years 25 --n-process 1 --eval-freq 1000 --method PPO
python experiments/crop_planning/train.py --method PPO --fixed_weather True --non_adaptive False --seed 0
```

### Phase 4: Full Core Matrix (thesis baseline matrix)

```powershell
python run_all_2.py --dry-run
python run_all_2.py
```

### Phase 5: Algorithm/Baseline Extensions

```powershell
python run_all_2.py --include-dqn --include-baseline
```

### Phase 6: Post-Run Diagnostics

```powershell
python experiments/fertilization/analyze_logs.py
python plot_thesis_figures.py
```

### Phase 7: Economics Data Refresh (optional, if you want latest reconstructed series)

```powershell
python scripts/build_pakistan_price_series.py
```

## B. Time Estimates from Old Runs

### Evidence window

- Audited run window: `2026-02-23` to `2026-02-25`
- Total run folders: `64`
- Successful: `44`
- Failed traceback: `16`
- No-summary: `4`

### Runtime medians from successful runs (`runtime_sec`)

- Crop planning PPO: `~930.5s` (about `15.5m`)
- Crop planning A2C: `~943.5s` (about `15.7m`)
- Crop planning DQN: `~890s` (about `14.8m`) with very small sample
- Fertilization PPO:
  - `1000 years`: `~1509s` (about `25.2m`)
  - `3000 years`: `~2450.5s` (about `40.8m`)
  - `5000 years`: `~3351s` (about `55.9m`)
- Fertilization A2C (`5000 years`): `~3064s` (about `51.1m`) tiny sample
- Fertilization DQN (`5000 years`): `~4494s` (about `74.9m`) tiny sample

### Total timeline estimate (sequential execution on one machine)

1. Setup + verification: `0.5 to 1.5 hours`
2. Full `run_all_2` default 96 planned configs: `~61.3 hours`
3. Remaining uncovered configs only (62): `~39.1 hours`
4. DQN + baseline add-on matrix: `~3.4 hours` extra
5. Plots/tables/report writing pass: `8 to 16 hours` (manual effort)

Practical full rerun + reporting estimate: `~3.5 to 4.5 days` wall time if run continuously.

## C. Direct Answers to Questions 0 to 9

## 0) Overall flow + detailed flow diagrams

See:
- `final_docs/thesis_answer_pack/00_Flow_Diagrams.md`

It contains:
1. End-to-end architecture flow
2. Fertilization step-by-step sequence
3. Crop-planning/hierarchical loop
4. Full experimentation pipeline

## 1) What effect soil and weather have on crop

### Soil effect in current code

1. Soil enters via soil files (default Pakistan soil) and soil nitrogen outputs.
2. Crop-planning observations include soil-N signals (`SoilNObserver`).
3. Fertilization variants can include richer soil/crop/weather observations (`CornSoilRefined`).
4. There is no completed multi-soil ablation in audited runs, so quantified soil sensitivity is still pending.

### Weather effect in current evidence

Observed weather regime changes performance materially:

1. Fertilization PPO (5000 years): random-weather grouped means are often higher than fixed-weather grouped means in this audit snapshot.
2. Crop planning PPO adaptive: fixed-weather (`21683.79`) vs random-weather (`17403.996`) shows about `+24.6%` for fixed-weather in current observed runs.
3. Interpretation:
   - fixed-weather can optimize in-distribution performance
   - random-weather is typically better for robustness/generalization claims

## 2) Train/test mean rewards, avg returns, and related RL values

### Metric definitions used in this repo

1. `eval_* / mean_reward`:
   periodic callback evaluation mean episodic reward.
2. `deterministic_return`:
   1-episode deterministic policy evaluation.
3. `stochastic_return_mean` and `stochastic_return_std`:
   5-episode stochastic policy evaluation mean/std.
4. `pak_holdout_return`:
   fertilization holdout-weather evaluation return.
5. `mean_ep_length`:
   mean episode length during callback evaluation.

### Aggregated values from old successful runs

Fertilization (n=32 where metric available):

1. `fert_eval_test_det_mean_reward`: mean `1116.927`, median `1186.085`, min `787.842`, max `1387.053`
2. `fert_eval_test_sto_mean_reward`: mean `1079.488`, median `1100.525`
3. `fert_deterministic_return`: mean `1016.931`, median `1186.085`
4. `fert_stochastic_return_mean`: mean `1000.771`, median `1095.317`
5. `fert_pak_holdout_return`: mean `938.114`, median `1061.673`

Crop planning (n=11):

1. `crop_eval_det_mean_reward`: mean `19540.85`, median `18848.514`, max `21683.79`
2. `crop_eval_sto_mean_reward`: mean `18200.29`, median `18872.559`

## 3) Fertilizers used and what changed after updates

### What fertilizers are represented

1. N-only mode:
   action controls total N and splits to `N_NH4` and `N_NO3` by configured ratio.
2. NPK mode:
   action controls N, P, K channels.
   - N split: `N_NH4` + `N_NO3`
   - P mapped to `P_INORGANIC`
   - K mapped to `K`

### What changed in new codebase

1. Fertilization training now exposes nutrient mode and nutrient bounds:
   `--nutrient-action-mode`, `--maxN`, `--maxP`, `--maxK`, `--p-actions`, `--k-actions`, `--n-nh4-rate`.
2. Price profile is configurable (`--price-profile`, default Pakistan baseline).
3. Hierarchical environment logs per-step nutrient quantities and costs in detail for thesis reporting CSV/JSON.

## 4) Number of episodes, steps, and definitions

### Definitions

1. `step`: one environment transition caused by one action.
2. `episode`: from `reset()` until `done=True` for that environment.
3. `total_timesteps` (SB3): total collected transition steps across training.

### Fertilization

1. Step size is `delta=7` days (weekly decision).
2. Training uses `total_timesteps = total_years * 53`.
3. Default one-year simulation implies roughly 53 steps per episode.
4. If `end_year > start_year`, episode spans multiple years.

### Crop planning

1. Step size is `delta=365` days (year-level decision).
2. Default train range is `2005-2018` so one episode is about 14 steps.
3. Default `total_timesteps` is `500`.

## 5) What marks start and end of step/episode

### Episode start

1. `reset()` sets simulation date to Jan 1 of `start_year`.
2. Environment prepares input/output files and runs initial CYCLES pass.
3. Initial observation is returned.

### Step start

1. Agent sends action.
2. Action is translated into operation updates (fertilizer/planting).
3. Simulator reruns when operations changed.

### Step end

1. Date advances by `delta`.
2. Reward/constraints/observation computed.
3. `done` is set when `date.year > SIMULATION_END_YEAR`.

### Episode end

1. First step where the done condition is true.
2. Next call should be `reset()` for a new episode.

## 6) Will this model overfit? How to prevent it?

Yes, it can overfit, especially in fixed-weather settings and low-seed experiments.

Current anti-overfitting mechanisms already present:

1. Weather randomization (`WeatherShuffler`) for domain randomization.
2. Holdout-weather evaluation (`pak_holdout_return`, test eval callbacks).
3. Deterministic and stochastic evaluation branches.
4. VecNormalize state normalization.
5. Entropy regularization option (`--ent-coef`).

What to add for stronger defense:

1. Enforce minimum 3 seeds for every main config before claims.
2. Prefer random-weather training for deployment robustness.
3. Add early-stop selection based on holdout curves.
4. Add statistical confidence intervals and significance tests.
5. Add soil/weather OOD stress tests.

## 7) Config summary of all training runs

### Planned matrix (`run_all_2` default)

1. Planned configs: `96`
2. Successful covered configs in audited evidence: `34`
3. Missing configs: `62`

### Missing by domain/method

1. Fertilization A2C: `35` missing
2. Fertilization PPO: `8` missing
3. Crop planning A2C: `11` missing
4. Crop planning PPO: `8` missing

### Run status summary (audited folders)

1. `64` total
2. `44` ok
3. `16` failed tracebacks
4. `4` no-summary

### Most frequent failures

1. `subproc_eoferror` (8)
2. `weather_shuffle_empty_choice` (4)
3. `dqn_eval_get_distribution_missing` (2)
4. `reward_price_missing_year_2020` (1)
5. `dqn_unsupported_multidiscrete` (1)

## 8) Fertilizer costs and economic impact

### Reward economics used

1. Crop revenue: harvested yield * crop price (year-aware lookup).
2. Fertilizer penalty: negative nutrient mass * nutrient price (year-aware lookup).
3. Total reward is compound sum (crop term + nutrient cost term).

### Example Pakistan nutrient prices (Rs/kg nutrient)

1. 2005: N `20.35`, P `99.73`, K `47.99`
2. 2010: N `35.04`, P `225.86`, K `114.20`
3. 2020: N `80.43`, P `354.48`, K `207.16`
4. 2025: N `83.17`, P `819.65`, K `372.34`

Economic implication:

1. As nutrient prices rise, high-input policies are penalized more.
2. Policies that keep yield while reducing excess nutrient input become increasingly preferred.
3. This directly supports the thesis angle of cost-driven optimization.

## 9) PPO vs DQN vs other algorithms

Current observed evidence (not full matrix complete):

1. Fertilization:
   - PPO has the strongest and most repeated successful results.
   - DQN has fewer stable successful runs and lower top observed score.
   - A2C has very limited successful coverage in audited set.
2. Crop planning:
   - PPO adaptive fixed-weather has best observed score.
   - DQN required MultiDiscrete wrapper support path.
   - A2C performed competitively in a small number of runs.

Defense-safe statement:

PPO is best supported by current evidence volume and consistency, while DQN/A2C conclusions remain weaker due sparse coverage and failure concentration.

## D. What Is Still Left (High Priority)

1. Complete missing `62` planned configs.
2. Expand crop-planning multi-seed robustness (>=3 seeds per key config).
3. Standardize baseline-vs-RL metric schema for cleaner uplift claims.
4. Strengthen economics beyond crop value minus fertilizer cost.
5. Add broader resource controls (irrigation and multi-nutrient constraints).
6. Hardening for known failure signatures in large sweeps.

## E. What You Can Do for Legit Master's Contributions

1. Complete matrix + statistics package:
   deliver full 96+ configs, CI/error bars, hypothesis tests.
2. Reliability engineering:
   fix the top 3 crash signatures and prove lower failure rate.
3. Soil/weather generalization thesis chapter:
   run explicit soil-file and weather-window ablations.
4. Economics research contribution:
   add risk-aware objective terms and sensitivity analysis.
5. Algorithmic contribution:
   benchmark PPO/A2C/DQN with consistent seeds and budgets, include tuning protocol.
6. Hierarchical policy extension:
   improve and evaluate yearly crop + weekly fertilization coupling.
7. Reproducibility package:
   one-command pipeline producing report tables/figures from raw runs.
8. Domain validation:
   define expert-reviewed scenario tests and compare policy decisions qualitatively.
