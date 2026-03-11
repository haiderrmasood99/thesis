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

### Phase 4: Full Thesis Matrix Dry Run

```powershell
python run_experiments_7_3_2026.py --dry-run
```

### Phase 5: Full Thesis Matrix Execution

```powershell
python run_experiments_7_3_2026.py
```

### Phase 6: Optional Split Execution / Reruns

```powershell
python 10_3_2026_heira_exp.py
python 10_3_2026_experiments.py --start-index 75
```

### Phase 7: Post-Run Diagnostics

```powershell
python experiments/fertilization/analyze_logs.py
python plot_thesis_figures.py
```

### Phase 8: Economics Data Refresh (optional, if you want latest reconstructed series)

```powershell
python scripts/build_pakistan_price_series.py
```

## B. Time Estimates From the Final March 2026 Campaign

### Evidence window

- Final campaign window in export: `2026-03-07 21:43 PKT` to `2026-03-11 01:20 PKT`
- Planned matrix: `113`
- Finished unique configs: `113/113`
- Total attempts: `117`
- Initial failed attempts: `4` (all DQN), later rerun successfully

### Runtime medians from final successful runs (`Runtime`, seconds)

- Crop planning PPO: `~873s` (about `14.6m`)
- Crop planning A2C: `~869s` (about `14.5m`)
- Crop planning DQN: `~1232.5s` (about `20.5m`)
- Hierarchical PPO: `~62,819.5s` (about `17.4h`)
- Hierarchical A2C: `~60,832s` (about `16.9h`)
- Fertilization PPO:
  - `1000 years`: `~1855.5s` (about `30.9m`)
  - `3000 years`: `~1645s` (about `27.4m`)
  - `5000 years`: `~2187s` (about `36.5m`)
- Fertilization A2C:
  - `1000 years`: `~1311s` (about `21.9m`)
  - `3000 years`: `~4273.5s` (about `71.2m`)
  - `5000 years`: `~2176.5s` (about `36.3m`)
- Fertilization DQN (`5000 years`): `~6152.5s` (about `102.5m`)

### Total timeline estimate (sequential execution on one machine)

1. Setup + verification: `0.5 to 1.5 hours`
2. Full finished matrix runtime sum: `~262.1 hours` (`~10.9 days`) if run fully sequentially
3. The actual March campaign was shorter because hierarchical cases were parallelized and reruns affected only four DQN jobs
4. Plots/tables/report writing pass: `8 to 16 hours` (manual effort)

Practical takeaway: the matrix is already complete; the next time cost is post-processing and any targeted reruns for redesigned hierarchical experiments.

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

### Weather effect in the final March 2026 matrix

Observed weather regime changes performance materially, but the completed matrix does not support the earlier claim that random-weather PPO is best overall.

1. Fertilization: the strongest mean deterministic and holdout results come from high-budget fixed-weather PPO/A2C groups. Example: `PPO + nonadaptive + fixed_weather + 3000` averages `765,191.6` deterministic return and `747,825.4` holdout.
2. Crop planning: fixed-weather remains competitive, but the adaptive toggle is not consistently superior. The best repeated group is `PPO + nonadaptive + fixed_weather` with mean `eval_det/mean_reward = 21,230.9`, while the best single run is `A2C + adaptive + fixed_weather` at `23,601.6`.
3. Interpretation:
   - fixed-weather gives the strongest in-distribution performance in this final matrix
   - random-weather is still useful as a stress test, but it is not the top thesis claim after the full 113-case campaign

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

### Aggregated values from final successful runs

Fertilization RL (n=74, baseline excluded):

1. `fert_eval_test_det_mean_reward`: mean `403,908.3`, median `439,500.6`, min `-689,305.3`, max `791,255.5`
2. `fert_eval_test_sto_mean_reward`: mean `211,396.3`, median `287,210.2`
3. `fert_deterministic_return`: mean `473,763.0`, median `568,774.9`
4. `fert_stochastic_return_mean`: mean `321,136.4`, median `352,764.9`
5. `fert_pak_holdout_return`: mean `326,427.4`, median `346,988.7`
6. `fert_baseline_best_return`: `750,198.1`

Crop planning, non-hierarchical (n=26):

1. `crop_eval_det_mean_reward`: mean `19,955.4`, median `20,718.4`, max `23,601.6`
2. `crop_eval_sto_mean_reward`: mean `17,226.7`, median `16,993.3`
3. `crop_deterministic_return`: mean `17,023.8`, median `16,473.4`
4. `crop_stochastic_return_mean`: mean `17,021.5`, median `16,555.1`

Hierarchical crop planning failed ablation (n=12):

1. `hier_eval_det_mean_reward`: mean `-8,880,765.2`
2. `hier_deterministic_return`: mean `-6,225,397.6`
3. Mean nutrient cost across the run-level thesis reports is about `8.6M`
4. Only `38.3%` of yearly decisions had a defined crop-calendar window in the report files
5. Interpretation: the current hierarchical formulation should be reported as a failed ablation caused by nutrient-cost blow-up and incomplete crop-calendar coverage, not as a competitive benchmark

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
2. Compare fixed and random weather explicitly; do not assume random-weather is automatically better.
3. Add early-stop selection based on holdout curves where available.
4. Add statistical confidence intervals and significance tests.
5. Add soil/weather OOD stress tests.

## 7) Config summary of all training runs

### Planned matrix (`run_experiments_7_3_2026.py`)

1. Planned configs: `113`
2. Finished unique configs: `113`
3. Missing configs: `0`
4. Extra configs versus the generator: `0`

### Final run status summary (March 11 export)

1. `117` total attempts
2. `113` finished
3. `4` failed first attempts
4. all `4` failed attempts were rerun successfully, so final coverage is complete

### Finished by domain

1. Fertilization: `75`
2. Crop planning (non-hierarchical): `26`
3. Crop planning (hierarchical): `12`

### Rerun-sensitive cases

1. Fertilization DQN fixed-weather seed `0`
2. Fertilization DQN random-weather seed `0`
3. Crop-planning DQN fixed-weather seed `0`
4. Crop-planning DQN random-weather seed `0`

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

Current final evidence from the completed matrix:

1. Fertilization:
   - PPO has the strongest overall portfolio and the best average performance across the largest number of successful runs.
   - A2C is competitive in one major pocket: `A2C + nonadaptive + fixed_weather + 5000` has the best mean group return (`779,267.4`).
   - DQN is not recommendation-grade: random-weather DQN is positive, fixed-weather DQN is negative, and both required reruns.
2. Crop planning:
   - `PPO + nonadaptive + fixed_weather` has the best repeated-group mean (`21,230.9`).
   - `A2C + adaptive + fixed_weather` has the best single run (`23,601.6`) and is a credible challenger.
   - DQN random-weather seed `0` is competitive (`21,185.6`) but is still only a single-seed ablation.
3. Hierarchical:
   - PPO and A2C both perform very poorly; all 12 hierarchical runs are strongly negative.
   - Treat this branch as a failed ablation. The March analysis links the collapse to dense weekly nutrient cost, sparse harvest reward, and incomplete calendar coverage for soybean in the tested rotation.

Defense-safe statement:

Within the completed 113-case matrix, PPO is the safest overall recommendation for fertilization, PPO/A2C are both defensible for non-hierarchical crop planning, and the hierarchical branch should be presented only as a failed ablation rather than as a success claim.

## D. What Is Still Left (High Priority)

1. Add confidence intervals, effect sizes, and hypothesis tests on the completed matrix.
2. Standardize crop-planning baseline-vs-RL metric schema for cleaner uplift claims.
3. Redesign the hierarchical controller and rerun its 12-case branch.
4. Strengthen economics beyond crop value minus fertilizer cost.
5. Add broader resource controls (irrigation and multi-nutrient constraints).
6. Make the DQN ablations one-pass stable without manual reruns.

## E. What You Can Do for Legit Master's Contributions

1. Statistics package on top of the completed matrix:
   deliver CI/error bars, effect sizes, and hypothesis tests for the 113 finished configs.
2. Reliability engineering:
   make the DQN ablations one-pass stable without manual reruns.
3. Soil/weather generalization thesis chapter:
   run explicit soil-file and weather-window ablations.
4. Economics research contribution:
   add risk-aware objective terms and sensitivity analysis.
5. Algorithmic contribution:
   benchmark PPO/A2C/DQN with consistent seeds and budgets in the stabilized matrix.
6. Hierarchical redesign contribution:
   fix reward decomposition and credit assignment, enforce valid crop windows and annual nutrient caps, then rerun the 12-case hierarchical branch.
7. Reproducibility package:
   one-command pipeline producing report tables/figures from the final export.
8. Domain validation:
   define expert-reviewed scenario tests and compare policy decisions qualitatively.
