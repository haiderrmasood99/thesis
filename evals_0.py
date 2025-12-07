from pathlib import Path
import sys
import types
import wandb

# Ensure fertilization modules are importable when run from repo root
REPO_ROOT = Path(__file__).resolve().parent
FERT_PATH = REPO_ROOT / 'experiments' / 'fertilization'
if str(FERT_PATH) not in sys.path:
    sys.path.insert(0, str(FERT_PATH))

# Stub wandb.run when not inside an initialized run
if wandb.run is None:
    wandb.run = types.SimpleNamespace(dir=str(REPO_ROOT / 'wandb_stub'))
    Path(wandb.run.dir).mkdir(parents=True, exist_ok=True)

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecNormalize
from experiments.fertilization.train import Train

config = dict(
    n_process=1, fixed_weather=True, seed=0,
    soil_env=True, n_actions=11,
    start_year=1980, end_year=1980,
    sampling_start_year=1980, sampling_end_year=2005,
    n_weather_samples=100, norm_reward=True, with_obs_year=True,
    nonadaptive=False
)
with_obs_year = config['with_obs_year'] and (config['start_year'] != config['end_year'])
trainer = Train(config, with_obs_year)

env = trainer.env_maker(training=False, n_procs=1, soil_env=config['soil_env'],
                        start_year=config['start_year'], end_year=config['end_year'],
                        sampling_start_year=config['sampling_start_year'],
                        sampling_end_year=config['sampling_end_year'],
                        n_weather_samples=config['n_weather_samples'],
                        fixed_weather=config['fixed_weather'],
                        with_obs_year=with_obs_year,
                        nonadaptive=config['nonadaptive'])

stats_path = REPO_ROOT / 'runs' / 'vec_normalize_2606oqqk.pkl'  # adjust if needed
env = VecNormalize.load(stats_path, env)
env.training = False
env.norm_reward = False

model = PPO.load(REPO_ROOT / '0.zip')

obs = env.reset()
ret = 0.0
while True:
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, done, info = env.step(action)
    ret += float(reward)
    if done:
        break

print('Episode return:', ret)
