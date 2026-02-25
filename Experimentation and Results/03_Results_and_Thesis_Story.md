# Results and Thesis Story

## X, Y, Z Configuration Framing
For thesis storytelling, define:
- `X`: RL algorithm (`PPO`, `A2C`, `DQN`)
- `Y`: Adaptation mode (`adaptive` vs `nonadaptive`)
- `Z`: Weather regime (`fixed_weather` vs `random_weather`)

Optional fourth dimension used in fertilization: training budget (`total_years`).

## Fertilization: Best Observed Patterns
Primary score used: `eval_test_det/mean_reward` (fallback: `deterministic_return`).

### Top observed runs
1. `PPO + adaptive + fixed_weather + seed0 + total_years=5000` -> `1387.053`
2. `PPO + nonadaptive + fixed_weather + seed0 + total_years=5000` -> `1385.914`
3. Random-weather PPO variants (multiple seeds/budgets) repeatedly around `1186.0851`

### Grouped trend (latest successful per unique config)

| X (method) | Y (nonadaptive) | Z (fixed_weather) | Budget | Mean Score | n |
|---|---|---|---:|---:|---:|
| PPO | false | false | 5000 | 1186.0851 | 3 |
| PPO | true | false | 5000 | 1186.0851 | 4 |
| A2C | false | false | 5000 | 1186.0851 | 1 |
| PPO | true | true | 5000 | 1150.8797 | 3 |
| PPO | false | true | 5000 | 1076.8593 | 3 |
| DQN | false | false | 5000 | 1000.0851 | 1 |

### Holdout robustness insight (`pak_holdout_return`)
- `PPO + adaptive + random_weather + 5000` mean holdout is strongest among repeatedly successful groups (`~1131.07`).
- `PPO + adaptive + fixed_weather + 5000` shows high variance and one severe negative holdout run.

Interpretation:
- Fixed-weather can win peak in-distribution score.
- Random-weather is more defensible for generalization to unseen years (cost-driven deployment logic).

## Crop Planning: Best Observed Patterns
Primary score: `eval_det/mean_reward`.

| X (method) | Y (nonadaptive) | Z (fixed_weather) | Mean Score | n |
|---|---|---|---:|---:|
| PPO | false | true | 21683.79 | 1 |
| A2C | false | true | 21292.441 | 1 |
| DQN | true | false | 19553.072 | 1 |
| PPO | true | true | 18848.514 | 1 |
| PPO | true | false | 18469.4 | 1 |
| PPO | false | false | 17403.996 | 1 |

Observed effect sizes:
- PPO adaptive fixed vs PPO adaptive random: about `+24.6%`
- PPO adaptive fixed vs PPO nonadaptive fixed: about `+15.0%`

Limitation:
- Crop findings are not multi-seed robust yet in current evidence.

## Thesis Story (Defensible Version)
1. Problem setup:
   - Farmers face uncertain weather and rising fertilizer cost.
   - Static schedules over- or under-apply inputs and waste budget.
2. Method:
   - Train RL agents in CYCLES Gym using Pakistan weather/soil setup.
   - Compare X/Y/Z configurations under cost-sensitive reward design.
3. Key result:
   - Fertilization: PPO-based policies dominate observed alternatives.
   - Crop planning: PPO adaptive fixed-weather is strongest in observed runs.
4. Deployment recommendation:
   - For fertilization in uncertain seasons: prefer `PPO + adaptive + random_weather` (robust holdout behavior).
   - For stable site planning workflows: use `PPO + adaptive + fixed_weather` for crop planning.
5. Farmer impact:
   - Lower over-application risk, more consistent nutrient allocation, better season-level decision quality.

## Suggested Thesis Claim Language
"Across the audited experimental runs (February 23-25, 2026), PPO-based policies produced the strongest and most consistent performance in CYCLES Gym. For fertilization, random-weather PPO settings provided better holdout robustness, while crop planning benefited most from adaptive fixed-weather PPO in the available runs."

## Important Caveat
Do not claim final global optimum across the full `run_all_2` design space until the missing `62` planned configurations are executed and evaluated.
