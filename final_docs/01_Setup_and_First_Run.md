# 01. Setup and First Run

## Environment Setup

Recommended:

```bash
conda create -yn cyclesgym python=3.8
conda activate cyclesgym
pip install -e .
pip install -e .[SOLVERS]
```

Notes:
- `setup.py` includes a post-install step that can install the CYCLES binary.
- If you want to skip automatic binary install, set `CYCLESGYM_SKIP_CYCLES=1`.

## Sanity Check the Simulator

```bash
python install_cycles.py
```

This verifies that CYCLES can run and produce expected output files.

## First Environment Run (Fertilization)

```python
import cyclesgym
from cyclesgym.envs.corn import Corn

env = Corn(delta=7, n_actions=11, maxN=150, start_year=2005, end_year=2005)
obs, info = env.reset()
done = False
total_reward = 0.0

while not done:
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated
    total_reward += reward

print("Episode reward:", total_reward)
```

## First Training Run (Short Smoke Test)

Fertilization:

```bash
python experiments/fertilization/train.py --total-years 25 --n-process 1 --eval-freq 1000 --method PPO
```

Crop planning:

```bash
python experiments/crop_planning/train.py --method PPO --fixed_weather True --non_adaptive False --seed 0
```

## First Inference Demo Run

CLI:

```bash
python demo/run_demo_cli.py --preset fert_robust_random --episodes 3 --deterministic
```

Streamlit:

```bash
python -m streamlit run demo/app.py
```

## Artifacts You Should Expect

1. Trained model checkpoints (`*.zip`, wandb model folders)
2. VecNormalize stats (`runs/vec_normalize_*.pkl`)
3. Training logs (`runs/train_logs/*.jsonl`)
4. Evaluation summaries in W&B run folders
5. Demo output traces (`demo/output/*.log`, JSON output if using `--output`)

## Common Failure Patterns

1. Weather sampling window mismatch causing empty random choices  
   Fix: keep simulation years inside valid weather year bounds.
2. Missing VecNormalize stats at inference  
   Fix: load the same stats file used during training when available.
3. DQN incompatibility for MultiDiscrete crop-planning actions  
   Fix: use the provided MultiDiscrete-to-Discrete wrapper in crop-planning train script.
