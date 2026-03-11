# Runs Experiments Report

Generated on 2026-03-11 18:56

## Scope

- Main consolidated source: `run_experiments_7_3_2026_RUNS/wandb_export_2026-03-11T01_53_38.382+05_00.csv`
- Supporting summaries: `runs/experiment_summaries/train_logs_summary.csv`, `runs/experiment_summaries/failure_signature_counts.csv`
- Current failure root-cause evidence: `runs/experiment_summaries/non_hier_10_3_2026_20260309_193918/console.log`
- Performance comparisons below are based on finished runs unless stated otherwise.

## Executive Summary

1. Hierarchical crop planning has been removed from the main comparative results and is now reported only as a failed ablation. Its mean deterministic return is -6,225,398 versus 17,024 for non-hier runs.
2. Crop planning also shows a strong temporal generalization gap. Non-hier runs retain only 8.4% of in-sample deterministic reward on the `new_years` evaluation.
3. The crop `other_loc` deterministic metric is almost certainly misconfigured: 38 of 38 runs match exactly.
4. Fertilization does not show classical overfitting. Instead, 66 of 74 comparable runs score higher on test than train, which is itself suspicious and should be audited.
5. Fertilization budgets below `total_years=3000` are unstable. At `1000` years, 8 of 24 runs have negative test reward and 15 of 24 have negative holdout reward.

## Coverage

The export contains 117 runs in total. 113 finished and 4 failed.

| domain | finished_runs | failed_runs |
| --- | --- | --- |
| fertilization | 75 | 2 |
| crop_planning | 38 | 2 |

![Run state counts](figures/01_run_state_by_domain.png)

## Main Findings

### Fertilization

- Best-performing finished fertilization runs are concentrated at `total_years=3000` or `5000`, with PPO and A2C both reaching the 790k range on `eval_test_det/mean_reward`.
- Among runs with positive test and holdout scores, the median holdout/test ratio is 0.949. Holdout performance is usually close to test performance once the budget is large enough.
- The low-budget regime is the weak point: `1000`-year runs are the only budget where negative rewards are common.
- The train/test direction is unusual. Test scores are often much larger than train scores, so this is not standard overfitting; it looks more like a split-definition or logging mismatch.

![Fertilization budget vs test reward](figures/04_fertilization_budget_vs_test_reward.png)

![Fertilization test vs holdout](figures/05_fertilization_test_vs_holdout.png)

![Fertilization train vs test](figures/06_fertilization_train_vs_test.png)

Top fertilization runs by holdout performance:

| Name | method | adaptive_mode | weather_mode | total_years | seed | eval_test_det/mean_reward | pak_holdout_return | train_test_gap | deterministic_return |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dainty-snowball-77 | A2C | nonadaptive | fixed_weather | 5,000.00 | 2 | 791,255.50 | 794,178.62 | -730,311.13 | 791,255.50 |
| deep-fire-29 | PPO | nonadaptive | fixed_weather | 3,000.00 | 2 | 791,255.50 | 791,130.81 | -730,311.13 | 791,255.50 |
| classic-sponge-69 | A2C | nonadaptive | fixed_weather | 5,000.00 | 0 | 791,255.50 | 790,211.56 | -730,311.13 | 791,255.50 |
| hearty-tree-24 | PPO | adaptive | fixed_weather | 3,000.00 | 1 | 791,255.50 | 786,757.88 | -730,311.13 | 791,255.50 |
| charmed-galaxy-36 | PPO | adaptive | fixed_weather | 5,000.00 | 1 | 791,255.50 | 785,778.38 | -738,086.19 | 791,255.50 |

### Crop Planning (Main Results, Hierarchy Excluded)

- The crop tables and comparisons in this section exclude the hierarchical variant and use only the non-hier policies.
- Non-hier crop runs are much healthier, but their `new_years` performance collapses. Mean in-sample deterministic evaluation is 19,955, while `eval_det_new_years/mean_reward` drops to 1,649.
- The crop deterministic evaluation metrics need caution. `eval_det/mean_reward` correlates only 0.11 with the final deterministic return, so it is not a reliable standalone ranking metric.
- The deterministic `other_loc` metric is effectively identical to in-sample results, so spatial-generalization claims should be avoided until the evaluator is checked.

![Crop in-sample vs new years](figures/08_crop_in_sample_vs_new_years.png)

![Crop other-location identity](figures/09_crop_other_location_identity.png)

![Crop eval metric vs final return](figures/10_crop_eval_metric_vs_final_return.png)

Top non-hier crop runs by deterministic return:

| Name | method | adaptive_mode | weather_mode | seed | eval_det/mean_reward | eval_det_new_years/mean_reward | deterministic_return | stochastic_return_mean | uplift_vs_best_baseline_det |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| easy-snow-80 | PPO | adaptive | fixed_weather | 0 | 20,968.56 | 1,889.83 | 24,573.22 | 16,661.74 | 3,979.92 |
| 8-bit-yoshi-113 | A2C | adaptive | fixed_weather | 2 | 23,601.59 | 703.26 | 24,521.69 | 20,796.81 | 3,928.38 |
| worldly-cloud-105 | A2C | adaptive | fixed_weather | 0 | 18,263.10 | 1,746.96 | 22,760.56 | 16,219.77 | 2,167.25 |
| stilted-firebrand-101 | PPO | adaptive | fixed_weather | 2 | 20,967.65 | 795.41 | 22,586.69 | 15,791.87 | 1,993.38 |
| retro-rosalina-115 | A2C | adaptive | random_weather | 2 | 20,927.90 | 795.41 | 22,106.99 | 20,218.64 | 1,491.55 |

## Failed Hierarchical Ablation

The hierarchical crop variant is excluded from the main results because it is not a valid competitive model in its current form. It is better interpreted as a failed ablation that revealed design problems in the hierarchical setup.

- All 12 finished hierarchical runs have negative deterministic return.
- Mean nutrient cost across the 12 reports is 8,598,707.
- Only 38.3% of yearly decisions have a defined calendar window in the thesis report files.
- The correlation between total nutrient cost and deterministic return is -0.85, which strongly supports cost blow-up as a primary failure mode.

Academic interpretation:

- The ablation fails because the low-level weekly fertilizer controller is too unconstrained relative to the sparse crop-revenue signal.
- The high-level crop planner is also operating with incomplete agronomic guidance, since many yearly decisions do not even have a defined calendar window in the generated thesis-report files.
- For this reason, the hierarchical variant should be discussed as a negative result and future-work item, not as an empirical baseline.

Rerun status:

- The environment has now been hardened for follow-up experiments with crop-window sanitization, seasonal fertilizer gating, and annual nutrient budgets.
- Those code changes are intended only for targeted reruns; they do not change the interpretation of the completed March 7-11, 2026 matrix reported here.

![Crop hierarchical vs non-hierarchical](figures/07_crop_hierarchical_vs_nonhierarchical.png)

![Hierarchical cost vs return](figures/11_hierarchical_cost_vs_return.png)

![Hierarchical defined-window rate](figures/12_hierarchical_defined_window_rate.png)

Failed-ablation reasons:

| reason | evidence | interpretation |
| --- | --- | --- |
| Dense fertilizer cost dominates sparse crop revenue | Mean hierarchical nutrient cost is 8,598,707, and cost-return correlation is -0.85. | The policy is spending far more on weekly fertilizer than it recovers at harvest. |
| Calendar coverage is incomplete for many yearly decisions | Only 38.3% of yearly decisions even have a defined calendar window in the thesis reports. | The high-level planner is operating with incomplete agronomic guidance, especially when soybean is chosen. |
| Hierarchical PPO is especially unstable | PPO hierarchical runs average -8,769,051 vs -3,681,744 for A2C. | The larger action burden appears to hurt PPO more severely under the current reward design. |

Run-level failed-ablation summary:

| Name | method | weather_mode | seed | deterministic_return | stochastic_return_mean | total_cost | total_n_kg | total_p_kg | total_k_kg | overall_compliance_rate | defined_window_rate | corn_rows | soy_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| driven-capybara-90 | PPO | fixed_weather | 1 | -10,895,760.00 | -11,763,116.00 | 9,726,299.17 | 41,850.00 | 22,368.00 | 17,076.00 | 0.64 | 0.64 | 7 | 4 |
| vivid-pine-88 | PPO | random_weather | 2 | -10,661,081.00 | -11,739,142.00 | 9,525,776.52 | 42,675.00 | 21,888.00 | 16,482.00 | 0.36 | 0.36 | 4 | 7 |
| giddy-dust-84 | PPO | fixed_weather | 2 | -9,527,365.00 | -11,760,288.00 | 9,631,739.12 | 43,755.00 | 21,904.00 | 16,788.00 | 0.27 | 0.27 | 3 | 8 |
| icy-cherry-84 | PPO | fixed_weather | 0 | -7,333,589.50 | -11,638,354.00 | 9,731,114.18 | 42,045.00 | 22,280.00 | 16,944.00 | 0.09 | 0.09 | 1 | 10 |
| distinctive-breeze-84 | PPO | random_weather | 1 | -7,266,629.00 | -11,745,526.00 | 9,607,416.31 | 41,310.00 | 22,184.00 | 17,178.00 | 0.55 | 0.55 | 6 | 5 |
| faithful-oath-84 | A2C | fixed_weather | 1 | -6,975,334.00 | -11,110,008.00 | 7,770,453.96 | 34,815.00 | 19,664.00 | 15,126.00 | 0.60 | 0.60 | 6 | 4 |

## Suspicious Items To Mention Explicitly

| finding | severity | value | why_it_matters |
| --- | --- | --- | --- |
| Crop hierarchical collapse | high | 12/12 hierarchical crop runs finished with negative deterministic return; mean -6,225,398 vs 17,024 for non-hier runs. | This is a catastrophic regression, not normal variance. |
| Crop temporal generalization gap | high | Non-hier crop runs average 1,649 on new years vs 19,955 in-sample (8.4% retention). | This is consistent with strong overfitting to the seen weather years. |
| Crop other-location metric identity | high | 38/38 deterministic other-location scores are exactly equal to in-sample scores. | Spatial generalization claims are not trustworthy until this evaluator is audited. |
| Crop metric mismatch | medium | Pearson correlation between eval_det/mean_reward and deterministic_return is 0.11. | The short evaluation metric is a weak proxy for the final return used in the thesis story. |
| Fertilization inverse train-test gap | medium | 66/74 comparable fertilization runs scored higher on test than train; mean gap -394,301. | This is the opposite of classical overfitting and suggests a split or logging definition issue. |
| Fertilization low-budget instability | medium | At total_years=1000, 8/24 runs have negative test reward and 15/24 have negative holdout reward. At total_years=3000 all 24 runs stay positive, and at 5000 only 1/26 is negative. | The 1000-year budget looks under-trained and should not be used for headline claims. |
| Current DQN failures are technical | medium | Fertilization DQN fails because Stable-Baselines3 DQN rejects the MultiDiscrete action space; crop DQN fails because wandb.log receives a PosixPath object. | DQN comparisons are incomplete because the failures are implementation issues, not just poor scores. |
| Training logs miss explicit end events | low | Historical train log summaries show 10/48 fertilization logs and 1/12 crop logs without an explicit end event. | Instrumentation is mostly usable, but end-of-run logging is not fully reliable. |

## Failure Analysis

All four failed runs in the current March export are DQN runs, but the failure modes are implementation issues rather than simple low reward:

| domain | method | failed_runs | root_cause | evidence_file | evidence_line |
| --- | --- | --- | --- | --- | --- |
| fertilization | DQN | 2 | DQN does not support the MultiDiscrete([11, 11, 11]) action space. | runs\experiment_summaries\non_hier_10_3_2026_20260309_193918\console.log | 40774 |
| crop_planning | DQN | 2 | Run reaches evaluation and then crashes when wandb.log receives a PosixPath. | runs\experiment_summaries\non_hier_10_3_2026_20260309_193918\console.log | 42793 |

The historical failure signature summary is still useful for context:

![Historical failure signatures](figures/03_failure_signature_counts.png)

## Logging Quality

The raw training logs are usable but not perfect. Some files stop without an explicit end event, especially on fertilization runs.

![Training log completion](figures/02_training_log_completion.png)

## Recommended Thesis Framing

1. Present fertilization `3000` and `5000`-year PPO/A2C results as the credible training regime, and describe `1000` years as under-trained.
2. Do not claim classical overfitting for fertilization. Instead, report an unexpected train/test inversion and state that the split semantics need audit.
3. Report crop non-hier performance, but explicitly say temporal generalization to unseen years is weak.
4. Do not use crop `other_loc` deterministic results as evidence of spatial transfer until the evaluation path is verified.
5. Present the hierarchical crop variant only as a failed ablation with documented causes, not as part of the main crop benchmark table.
6. If a follow-up hierarchical rerun is shown, label it explicitly as post-hoc stabilization work rather than mixing it into the completed March benchmark claims.
