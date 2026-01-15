# Training Pipeline (Experiments)

Primary files:
- `experiments/fertilization/train.py`
- `experiments/crop_planning/train.py`

Typical pipeline:
1) Build envs (train + evaluation)
2) Vectorize and normalize observations/rewards
3) Train RL model (PPO/A2C/DQN)
4) Evaluate periodically
5) Log and save artifacts (W&B)

Flow diagram:
```mermaid
flowchart TD
    A[Config (W&B or args)] --> B[Train.env_maker]
    B --> C[VecEnv + VecNormalize]
    C --> D[SB3 model (PPO/A2C/DQN)]
    D --> E[Training loop]
    E --> F[Eval callbacks]
    E --> G[Save model + stats]
    F --> H[Log metrics to W&B]
```

Real-life analogy:
- Training is like rehearsing a decision policy across many simulated seasons.
- Evaluation tests whether the policy works on "new" weather years.

Code map:
- Env creation: `experiments/fertilization/train.py:Train.env_maker`
- Evaluation: `cyclesgym/utils/utils.py:EvalCallbackCustom`
- Logging: `cyclesgym/utils/wandb_utils.py`
