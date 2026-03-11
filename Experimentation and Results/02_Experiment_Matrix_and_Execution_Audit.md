# Experiment Matrix and Execution Audit

## Matrix Definition

| Matrix Component | Description | Planned Configs |
|---|---|---:|
| Fertilization core | PPO/A2C x adaptive/nonadaptive x fixed/random weather x 3 seeds x 3 budgets | 72 |
| Crop-planning core | PPO/A2C x adaptive/nonadaptive x fixed/random weather x 3 seeds | 24 |
| Hierarchical crop-planning failed ablation | PPO/A2C x fixed/random weather x 3 seeds | 12 |
| DQN ablations | Fertilization DQN (2 weather modes) + crop-planning DQN (2 weather modes) | 4 |
| Fertilization baseline | Pakistan-baseline fertilization reference run | 1 |
| Total planned matrix | Defined by `run_experiments_7_3_2026.py` | 113 |

Notes:
- `10_3_2026_experiments.py` executed the non-hierarchical tail of this matrix and the DQN reruns.
- `10_3_2026_heira_exp.py` executed the hierarchical branch in parallel.
- The primary evidence file is `run_experiments_7_3_2026_RUNS/wandb_export_2026-03-11T01_53_38.382+05_00.csv`.

## Observed Run Evidence Window
- Earliest run in export: `2026-03-07 21:43:45 PKT`
- Latest run in export: `2026-03-11 01:20:53 PKT`
- Campaign span: March 7, 2026 to March 11, 2026

## Execution Summary
- Total W&B attempts in export: `117`
- Finished: `113`
- Failed: `4`
- Unique finished configs: `113/113`
- Comparison against the generator: `0` missing, `0` extra

Finished configs by domain:
- Fertilization: `75`
- Crop planning (non-hierarchical): `26`
- Crop planning (hierarchical): `12`

## Rerun Recovery Audit

| Domain | Configuration | Initial Failed Attempt | Successful Rerun |
|---|---|---|---|
| Fertilization | `DQN + adaptive + fixed_weather + years=5000 + seed=0` | `boomerang-mushroom-117` | `mini-castle-122` |
| Fertilization | `DQN + adaptive + random_weather + years=5000 + seed=0` | `jumping-warp-118` | `metal-level-123` |
| Crop planning | `DQN + nonadaptive + fixed_weather + seed=0` | `starry-starman-119` | `spiky-toadette-124` |
| Crop planning | `DQN + nonadaptive + random_weather + seed=0` | `yellow-goomba-120` | `royal-toad-125` |

All four failed attempts happened on March 10, 2026 in the early-morning Pakistan time window and were recovered with successful reruns later the same day.

## Reliability Takeaway
- The final matrix is complete even though the first DQN pass was not one-pass stable.
- PPO and A2C non-hierarchical sweeps completed without missing configurations.
- Hierarchical jobs completed operationally, but they are excluded from the main comparison tables because all `12/12` runs are negative.
- The failed-ablation audit shows mean nutrient cost of about `8.6M`, only `38.3%` of yearly decisions with a defined calendar window, and a strong negative cost-vs-return correlation (`-0.85`).
- The correct audit conclusion is that matrix coverage is complete, while the hierarchical branch failed on formulation quality rather than execution coverage.

## Pakistan Data Confirmation
Code-level evidence indicates Pakistani weather/soil integration:
- Fertilization defaults in `experiments/fertilization/train.py` reference the Pakistan weather window and Pakistan price profile.
- Crop-planning defaults in `experiments/crop_planning/train.py` reference `Pakistan_Site_final.weather` and `Pakistan_Soil_final.soil`.
- The full March campaign used `price_profile=pakistan_baseline` and `nutrient_action_mode=NPK`.

Artifacts used for this audit are in `artifacts/`, and the primary export is in `run_experiments_7_3_2026_RUNS/`.
