# Results and Thesis Story

## X, Y, Z Configuration Framing
For thesis storytelling, define:
- `X`: RL algorithm (`PPO`, `A2C`, `DQN`)
- `Y`: adaptation mode (`adaptive` vs `nonadaptive`)
- `Z`: weather regime (`fixed_weather` vs `random_weather`)

Optional fourth dimension used in fertilization: training budget (`total_years`).

## Fertilization: Final Patterns From the Completed Matrix
Primary score used: `deterministic_return`, cross-checked against `eval_test_det/mean_reward`. Holdout robustness is tracked with `pak_holdout_return`.

### Top grouped means

| Method | Adaptation | Weather | Budget | Mean Deterministic Return | Mean Holdout | n |
|---|---|---|---:|---:|---:|---:|
| A2C | nonadaptive | fixed | 5000 | 779,267.4 | 731,804.8 | 3 |
| PPO | nonadaptive | fixed | 3000 | 765,191.6 | 747,825.4 | 3 |
| PPO | nonadaptive | random | 3000 | 750,198.0 | 662,708.2 | 3 |
| PPO | nonadaptive | fixed | 5000 | 740,142.4 | 715,127.9 | 3 |
| PPO | adaptive | fixed | 5000 | 739,107.7 | 722,931.4 | 3 |
| PPO | adaptive | fixed | 3000 | 735,713.8 | 716,101.3 | 3 |

### Key takeaways
- The completed March 11 matrix reverses the earlier partial-audit story: high-budget fixed-weather PPO/A2C groups now dominate both deterministic and holdout means.
- PPO is still the strongest overall fertilization family by coverage and average performance, but `A2C + nonadaptive + fixed_weather + 5000` is the single best repeated group.
- The best baseline return is `750,198.06`; `11` of `74` fertilization RL runs exceeded it.
- DQN is not recommendation-grade here: random-weather DQN was positive (`504,738.25`), but fixed-weather DQN was negative (`-174,609.00`) and both DQN runs required reruns.

## Crop Planning: Final Patterns From the Completed Matrix
Primary score: `eval_det/mean_reward`.

### Best repeated groups

| Method | Adaptation | Weather | Mean `eval_det/mean_reward` | n |
|---|---|---|---:|---:|
| PPO | nonadaptive | fixed | 21,230.9 | 3 |
| PPO | nonadaptive | random | 20,510.2 | 3 |
| A2C | adaptive | fixed | 20,304.8 | 3 |
| PPO | adaptive | fixed | 20,083.2 | 3 |
| A2C | nonadaptive | random | 20,041.1 | 3 |
| A2C | nonadaptive | fixed | 19,641.9 | 3 |

### Key takeaways
- Crop-planning results are more mixed than the old partial audit suggested: PPO and A2C are both competitive in the final matrix.
- The best repeated group is `PPO + nonadaptive + fixed_weather`.
- The best single run is `A2C + adaptive + fixed_weather + seed=2` with `23,601.588`.
- DQN random-weather seed `0` is competitive at `21,185.598`, but it is still only a single-seed ablation and should not drive the thesis claim.
- In crop planning, the adaptive toggle is not a universal win; the algorithm/weather combination matters more than the label by itself.

## Failed Hierarchical Ablation (Excluded From Main Results)
Primary score for the failure analysis: `deterministic_return`, cross-checked against `eval_det/mean_reward`.

| Method | Weather | Mean `eval_det/mean_reward` | n |
|---|---|---:|---:|
| A2C | random | -5,405,994.0 | 3 |
| A2C | fixed | -7,566,062.3 | 3 |
| PPO | fixed | -10,970,184.3 | 3 |
| PPO | random | -11,580,815.7 | 3 |

Interpretation:
- All `12/12` hierarchical runs finished, so this is not a coverage problem.
- All `12/12` hierarchical runs are strongly negative, so the current hierarchical formulation is not thesis-ready as a positive result.
- Mean deterministic return is `-6,225,397.6`, mean nutrient cost is about `8.6M`, and only `38.3%` of yearly decisions in the thesis-report files have a defined calendar window.
- The most defensible causal explanation is a combination of dense weekly fertilizer-cost penalties overwhelming sparse harvest revenue, plus incomplete Pakistan crop-calendar coverage for the tested rotation because soybean has no defined local window in the current mapping.
- The correct thesis position is to report hierarchical control as a failed ablation and a future-work direction, not as part of the main crop benchmark table.

## Thesis Story (Defensible Version)
1. Problem setup:
   - Farmers face weather uncertainty and rising fertilizer cost.
   - Static schedules either waste inputs or miss profitable timing windows.
2. Method:
   - Train RL agents in CYCLES Gym with Pakistan weather, soil, and Pakistan-baseline fertilizer economics.
   - Compare algorithms, adaptation modes, weather regimes, and budgets across a completed 113-case matrix.
3. Key result:
   - Fertilization: PPO is the strongest overall family, with several high-budget fixed-weather PPO runs and one A2C fixed-weather group matching or beating the best baseline.
   - Crop planning: non-hierarchical PPO and A2C are both viable; PPO nonadaptive fixed is the best repeated group, and A2C adaptive fixed is the best single run.
   - Hierarchical: the current coupled controller is a documented failed ablation driven by nutrient-cost blow-up and incomplete crop-calendar coverage, and should not be presented as a success claim.
4. Deployment recommendation:
   - Fertilization: start from non-hierarchical PPO fixed-weather models in the `3000-5000` budget range, and keep `A2C + nonadaptive + fixed_weather + 5000` as a benchmark comparator.
   - Crop planning: use non-hierarchical PPO fixed-weather as the default reference policy and A2C adaptive fixed as a challenger.
   - Do not deploy the current hierarchical controller.
5. Farmer impact:
   - Better fertilizer timing and lower waste under the current simulator assumptions.
   - More evidence-backed crop-planning recommendations than the earlier partial audit allowed.

## Suggested Thesis Claim Language
"Across the completed 113-configuration matrix executed from March 7 to March 11, 2026, PPO delivered the strongest overall fertilization performance, while non-hierarchical PPO and A2C produced competitive crop-planning results. The hierarchical crop-planning-plus-fertilization branch is excluded from the main benchmark claims and reported instead as a failed ablation, because the March analysis shows severe nutrient-cost blow-up and incomplete crop-calendar coverage."

## Important Caveat
The matrix is complete, but significance tests, field validation, and richer economic modeling are still future work.
