import numpy as np
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv, VecNormalize
from stable_baselines3.common.vec_env import VecMonitor
from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.utils import set_random_seed
from cyclesgym.utils.utils import EvalCallbackCustom, _evaluate_policy, JsonlTrainLoggerCallback
from cyclesgym.utils.wandb_utils import WANDB_ENTITY, CROP_PLANNING_EXPERIMENT
from cyclesgym.utils.paths import PROJECT_PATH, CYCLES_PATH
from pathlib import Path
import gymnasium as gym
from cyclesgym.envs.corn import Corn
from cyclesgym.envs.crop_planning import CropPlanning, CropPlanningFixedPlanting
from cyclesgym.envs.crop_planning import CropPlanningFixedPlantingRotationObserver
from cyclesgym.envs.hierarchical import HierarchicalCropPlanningFertilization
from cyclesgym.envs.weather_generator import FixedWeatherGenerator, WeatherShuffler
from cyclesgym.policies.dummy_policies import OpenLoopPolicy
from cyclesgym.utils.thesis_reporting import HierarchicalThesisReportCallback
import random
import argparse
from datetime import datetime
import json

try:
    import wandb as _wandb_module
except Exception:
    _wandb_module = None

try:
    from wandb.integration.sb3 import WandbCallback as _WandbCallback
except Exception:
    _WandbCallback = None


class _NoOpWandbConfig(dict):
    def update(self, *args, **kwargs):
        kwargs.pop('allow_val_change', None)
        if args and not isinstance(args[0], dict) and hasattr(args[0], '__dict__'):
            args = (vars(args[0]),) + args[1:]
        return super().update(*args, **kwargs)


class _NoOpWandbRun:
    def __init__(self, run_id: str, run_dir: Path):
        self.id = run_id
        self.dir = str(run_dir)


class _NoOpWandbTable:
    def __init__(self, *args, **kwargs):
        pass

    def add_data(self, *args, **kwargs):
        return None


class _NoOpWandbPlot:
    @staticmethod
    def bar(*args, **kwargs):
        return None


class _NoOpWandb:
    Table = _NoOpWandbTable
    plot = _NoOpWandbPlot()

    def __init__(self):
        self.config = _NoOpWandbConfig()
        self.run = _NoOpWandbRun('offline-uninitialized', PROJECT_PATH.joinpath('runs', 'offline', 'uninitialized'))

    def init(self, config=None, dir=None, **kwargs):
        run_id = datetime.now().strftime('offline_%Y%m%d_%H%M%S')
        run_root = Path(dir) if dir is not None else PROJECT_PATH
        run_dir = run_root.joinpath('runs', 'offline', run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        self.config = _NoOpWandbConfig(dict(config or {}))
        self.run = _NoOpWandbRun(run_id, run_dir)
        return self

    def log(self, *args, **kwargs):
        return None


class _NoOpWandbCallback(BaseCallback):
    def __init__(self, *args, **kwargs):
        super().__init__(verbose=0)

    def _on_step(self):
        return True


_WANDB_TRACKING_AVAILABLE = (
    (_wandb_module is not None)
    and hasattr(_wandb_module, 'init')
    and (_WandbCallback is not None)
)
wandb = _wandb_module if _WANDB_TRACKING_AVAILABLE else _NoOpWandb()
WandbCallback = _WandbCallback if _WANDB_TRACKING_AVAILABLE else _NoOpWandbCallback


class MultiDiscreteToDiscreteActionWrapper(gym.ActionWrapper):
    """Wrap MultiDiscrete action spaces so SB3 DQN can be used."""

    def __init__(self, env):
        super().__init__(env)
        if not isinstance(env.action_space, gym.spaces.MultiDiscrete):
            raise TypeError(f"Expected MultiDiscrete action space, got {type(env.action_space)}")
        self._nvec = np.array(env.action_space.nvec, dtype=np.int64)
        self.action_space = gym.spaces.Discrete(int(np.prod(self._nvec)))

    def action(self, action):
        x = int(action)
        out = np.zeros_like(self._nvec)
        for i in range(len(self._nvec) - 1, -1, -1):
            out[i] = x % self._nvec[i]
            x //= self._nvec[i]
        return out


def _as_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    s = str(value).strip().lower()
    if s in {'true', '1', 'yes', 'y'}:
        return True
    if s in {'false', '0', 'no', 'n'}:
        return False
    return default


def _is_hierarchical_env(env_class_value) -> bool:
    if env_class_value == HierarchicalCropPlanningFertilization:
        return True
    return str(env_class_value) == 'HierarchicalCropPlanningFertilization'


class Train:
    """ Trainer object to wrap model training and handle environment creation, evaluation """

    def __init__(self, experiment_config) -> None:
        self.config = experiment_config
        # rl config is configured from wandb config

    def create_envs(self):
        eval_env_train = self.env_maker(start_year=self.config['train_start_year'],
                                        end_year=self.config['train_end_year'],
                                        training=False,
                                        env_class=self.config['eval_env_class'],
                                        weather_generator_class=FixedWeatherGenerator,
                                        weather_generator_kwargs={
                                            'base_weather_file': CYCLES_PATH.joinpath('input',
                                                                                      'Pakistan_Site_final.weather')})

        eval_env_new_years = self.env_maker(start_year=self.config['eval_start_year'],
                                            end_year=self.config['eval_end_year'],
                                            training=False,
                                            env_class=self.config['eval_env_class'],
                                            weather_generator_class=FixedWeatherGenerator,
                                            weather_generator_kwargs={
                                                'base_weather_file': CYCLES_PATH.joinpath('input',
                                                                                          'Pakistan_Site_final.weather')})


        eval_env_other_loc = self.env_maker(start_year=self.config['train_start_year'],
                                            end_year=self.config['train_end_year'],
                                            training=False,
                                            env_class=self.config['eval_env_class'],
                                            weather_generator_class=FixedWeatherGenerator,
                                            weather_generator_kwargs={
                                                'base_weather_file': CYCLES_PATH.joinpath('input',
                                                                                          'Pakistan_Site_final.weather')})

        eval_env_other_loc_long = self.env_maker(start_year=self.config['train_start_year'],
                                                 end_year=self.config['eval_end_year'] - 1,
                                                 env_class=self.config['eval_env_class'],
                                                 weather_generator_class=FixedWeatherGenerator,
                                                 weather_generator_kwargs={
                                                     'base_weather_file': CYCLES_PATH.joinpath('input',
                                                                                               'Pakistan_Site_final.weather')},
                                                 training=False)

        return [eval_env_train, eval_env_new_years, eval_env_other_loc, eval_env_other_loc_long]

    def env_maker(self, env_class=CropPlanningFixedPlanting, weather_generator_class=FixedWeatherGenerator,
                  weather_generator_kwargs={'base_weather_file': CYCLES_PATH.joinpath('input', 'Pakistan_Site_final.weather')},
                  training=True, n_procs=4, start_year=2005, end_year=2018, soil_file='Pakistan_Soil_final.soil'):
        if not training:
            n_procs = 1

        if isinstance(env_class, str):
            env_class = globals()[env_class]
        if isinstance(weather_generator_class, str):
            weather_generator_class = globals()[weather_generator_class]

        # Convert to Path since pickle converted it to string
        # base_weather_path = weather_generator_kwargs['base_weather_file']
        weather_generator_kwargs['base_weather_file'] = Path(weather_generator_kwargs['base_weather_file'])

        def make_env():
            # creates a function returning the basic env. Used by SubprocVecEnv later to create a
            # vectorized environment
            def _f():
                base_conf = dict(start_year=start_year, end_year=end_year, soil_file=soil_file,
                                 weather_generator_class=weather_generator_class,
                                 weather_generator_kwargs=weather_generator_kwargs,
                                 rotation_crops=['CornRM.100', 'SoybeanMG.3'])
                if env_class == HierarchicalCropPlanningFertilization:
                    env_conf = dict(
                        **base_conf,
                        delta=int(self.config.get('fert_delta', 7)),
                        n_actions=int(self.config.get('fert_n_actions', 11)),
                        maxN=float(self.config.get('maxN', 150)),
                        nutrient_action_mode=str(self.config.get('nutrient_action_mode', 'NPK')).upper(),
                        maxP=float(self.config.get('maxP', 80.0)),
                        maxK=float(self.config.get('maxK', 60.0)),
                        p_actions=int(self.config.get('p_actions', 11)),
                        k_actions=int(self.config.get('k_actions', 11)),
                        price_profile=str(self.config.get('price_profile', 'pakistan_baseline')),
                        use_pakistan_crop_calendar=_as_bool(self.config.get('use_pakistan_crop_calendar', True), default=True),
                    )
                else:
                    env_conf = dict(
                        **base_conf,
                        use_pakistan_crop_calendar=_as_bool(
                            self.config.get('use_pakistan_crop_calendar', False),
                            default=False
                        ),
                    )
                env = env_class(**env_conf)
                if str(self.config.get("method", "PPO")).upper() == "DQN" and isinstance(env.action_space, gym.spaces.MultiDiscrete):
                    env = MultiDiscreteToDiscreteActionWrapper(env)

                env = gym.wrappers.RecordEpisodeStatistics(env)
                return env

            return _f

        if n_procs and n_procs > 1:
            env = SubprocVecEnv([make_env() for _ in range(n_procs)], start_method='spawn')
        else:
            env = DummyVecEnv([make_env()])
        env = VecMonitor(env)
        norm_reward = (training and self.config['norm_reward'])
        env = VecNormalize(env, norm_obs=True, norm_reward=norm_reward, clip_obs=5000., clip_reward=5000.)
        return env

    def create_callback(self, model_dir):
        eval_freq = int(self.config['eval_freq'] / self.config['n_process'])

        [eval_env_train, eval_env_new_years, eval_env_other_loc, eval_env_other_loc_long] = self.create_envs()
        def get_callback(env, suffix, deterministic):
            return EvalCallbackCustom(env, best_model_save_path=str(model_dir.joinpath(suffix)),
                                      log_path=str(model_dir.joinpath(suffix)), eval_freq=eval_freq,
                                      deterministic=deterministic, render=False, eval_prefix=suffix)

        eval_callback_det = get_callback(eval_env_train, 'eval_det', True)
        eval_callback_sto = get_callback(eval_env_train, 'eval_sto', False)

        eval_callback_det_new_years = get_callback(eval_env_new_years, 'eval_det_new_years', True)
        eval_callback_sto_new_years = get_callback(eval_env_new_years, 'eval_sto_new_years', False)

        eval_callback_det_other_loc = get_callback(eval_env_other_loc, 'eval_det_other_loc', True)
        eval_callback_sto_other_loc = get_callback(eval_env_other_loc, 'eval_sto_other_loc', False)

        eval_callback_det_other_loc_long = get_callback(eval_env_other_loc_long, 'eval_det_other_loc_long', True)
        eval_callback_sto_other_loc_long = get_callback(eval_env_other_loc_long, 'eval_sto_other_loc_long', False)

        return [eval_callback_det, eval_callback_sto, eval_callback_det_new_years, eval_callback_sto_new_years,
                eval_callback_det_other_loc, eval_callback_sto_other_loc, eval_callback_det_other_loc_long,
                eval_callback_sto_other_loc_long]

    def train(self):
        train_env = self.env_maker(start_year=self.config['train_start_year'],
                                   end_year=self.config['train_end_year'],
                                   env_class=self.config['env_class'],
                                   training=True, n_procs=self.config['n_process'],
                                   weather_generator_class=self.config['weather_generator_class'],
                                   weather_generator_kwargs=self.config['weather_generator_kwargs'])
        dir = wandb.run.dir
        model_dir = Path(dir).joinpath('models')
        tensorboard_log = None if _as_bool(self.config.get('without_tracking', False), default=False) else dir

        if self.config["method"] == "A2C":
            model = A2C('MlpPolicy', train_env, verbose=self.config['verbose'], tensorboard_log=tensorboard_log,
                        device=self.config['device'])
        elif self.config["method"] == "PPO":
            model = PPO('MlpPolicy', train_env, n_steps=self.config['n_steps'], batch_size=self.config['batch_size'],
                        n_epochs=self.config['n_epochs'], verbose=self.config['verbose'], tensorboard_log=tensorboard_log,
                        device=self.config['device'])
        elif self.config["method"] == "DQN":
            model = DQN('MlpPolicy', train_env, verbose=self.config['verbose'], tensorboard_log=tensorboard_log,
                        device=self.config['device'])
        else:
            raise Exception("Not an RL method that has been implemented")

        # The test environment will automatically have the same observation normalization applied to it by
        # EvalCallBack

        callback = self.create_callback(model_dir)
        log_path = self.config.get('log_json_path')
        if not log_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = str(PROJECT_PATH.joinpath('runs', 'train_logs', f'crop_planning_{ts}.jsonl'))
        callback.append(JsonlTrainLoggerCallback(
            log_path=log_path,
            log_every_steps=int(self.config.get('log_every_steps', 1)),
            log_step_actions=bool(self.config.get('log_step_actions', True)),
            log_step_rewards=bool(self.config.get('log_step_rewards', True)),
            log_rollout=True
        ))

        if _is_hierarchical_env(self.config.get('env_class')) and _as_bool(
            self.config.get('enable_thesis_reporting', True), default=True
        ):
            report_dir = self.config.get('thesis_report_dir')
            if not report_dir:
                report_dir = str(
                    PROJECT_PATH.joinpath('runs', 'thesis_reports', f'hierarchical_{wandb.run.id}')
                )
            callback.append(HierarchicalThesisReportCallback(report_dir=report_dir))
            wandb.config.update({'thesis_report_dir': report_dir}, allow_val_change=True)

        callback = [WandbCallback(model_save_path=str(model_dir),
                                  model_save_freq=int(self.config['eval_freq'] / self.config['n_process']))] + callback
        model.learn(total_timesteps=self.config["total_timesteps"], callback=callback)

        eval_env = self.env_maker(start_year=self.config['train_start_year'],
                                  end_year=self.config['train_end_year'],
                                  training=False,
                                  env_class=self.config['eval_env_class'],
                                  weather_generator_class=self.config['weather_generator_class'],
                                  weather_generator_kwargs=self.config['weather_generator_kwargs'])
        return model, eval_env

    def evaluate_log(self, model, eval_env):
        """
        Evaluate trained model and emit standardized thesis metrics.
        """
        mean_r_det, _, actions_det, _, _, _ = _evaluate_policy(
            model, env=eval_env, n_eval_episodes=1, deterministic=True
        )
        mean_r_stoc, std_r_stoc, actions_stoc, _, _, _ = _evaluate_policy(
            model, env=eval_env, n_eval_episodes=5, deterministic=False
        )

        baseline_returns = self._evaluate_baseline_policies(eval_env=eval_env)
        baseline_best = max(baseline_returns.values()) if baseline_returns else None
        uplift_det = (float(mean_r_det) - float(baseline_best)) if baseline_best is not None else None

        metrics = {
            'deterministic_return': float(mean_r_det),
            'stochastic_return_mean': float(mean_r_stoc),
            'stochastic_return_std': float(std_r_stoc),
            'baseline_returns': baseline_returns,
            'baseline_best_return': float(baseline_best) if baseline_best is not None else None,
            'uplift_vs_best_baseline_det': float(uplift_det) if uplift_det is not None else None,
        }
        wandb.log(metrics)

        # Keep action visualization for scalar action runs.
        actions_stoc_arr = np.asarray(actions_stoc)
        if actions_stoc_arr.ndim == 2:
            episode_actions_names = [*list(f"det{i + 1}" for i in range(len(actions_det))),
                                     *list(f"stoc{i + 1}" for i in range(len(actions_stoc)))]
            episode_actions = [*actions_det, *actions_stoc]
            T = actions_stoc_arr.shape[1]
            action_table = wandb.Table(columns=['Run', 'Total Action', *[f'Step{i}' for i in range(T)]])
            for i, acts in enumerate(episode_actions):
                acts_arr = np.asarray(acts)
                data = [[step_i, float(a)] for (step_i, a) in enumerate(acts_arr)]
                table = wandb.Table(data=data, columns=['Step', 'Action'])
                action_table.add_data(*[episode_actions_names[i], float(np.sum(acts_arr)), *acts_arr.tolist()])
                wandb.log({
                    f'train/actions/{episode_actions_names[i]}': wandb.plot.bar(
                        table, 'Step', 'Action', title=f'Action sequence {episode_actions_names[i]}'
                    )
                })
            wandb.log({'train/actions_table': action_table})

        summary_path = self._write_standardized_summary(metrics)
        wandb.log({'summary_json_path': summary_path})
        return metrics

    def _evaluate_baseline_policies(self, eval_env):
        action_space = eval_env.action_space
        if not isinstance(action_space, gym.spaces.MultiDiscrete):
            return {}

        nvec = np.asarray(action_space.nvec, dtype=np.int64)
        crop_count = int(nvec[0]) if nvec.size > 0 else 1
        crop0 = 0
        crop1 = 1 if crop_count > 1 else 0

        if nvec.size == 2:
            corn = np.array([crop0, 0], dtype=np.int64)
            soy = np.array([crop1, 0], dtype=np.int64)
            policies = {
                'baseline_corn_only': [corn],
                'baseline_soy_only': [soy],
                'baseline_alternate': [corn, soy],
            }
        elif nvec.size == 4:
            corn = np.array([crop0, 0, 0, 0], dtype=np.int64)
            soy = np.array([crop1, 0, 0, 0], dtype=np.int64)
            policies = {
                'baseline_corn_only': [corn],
                'baseline_soy_only': [soy],
                'baseline_alternate': [corn, soy],
            }
        elif nvec.size >= 7:
            corn = np.array([crop0, 0, 0, 0, 0, 0, 0], dtype=np.int64)
            soy = np.array([crop1, 0, 0, 0, 0, 0, 0], dtype=np.int64)
            policies = {
                'baseline_no_fert_corn': [corn],
                'baseline_no_fert_soy': [soy],
            }
        else:
            return {}

        baseline_returns = {}
        for name, sequence in policies.items():
            policy = OpenLoopPolicy(np.array(sequence, dtype=np.int64))
            mean_r, _ = evaluate_policy(policy, eval_env, n_eval_episodes=3, deterministic=True)
            baseline_returns[name] = float(mean_r)
        return baseline_returns

    def _write_standardized_summary(self, metrics: dict):
        out_path = self.config.get('summary_json')
        if not out_path:
            out_path = str(
                PROJECT_PATH.joinpath('runs', 'experiment_summaries', 'metrics', f'crop_planning_{wandb.run.id}.json')
            )
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'timestamp': datetime.now().isoformat(),
            'run_id': wandb.run.id,
            'domain': 'crop_planning',
            'method': str(self.config.get('method')),
            'seed': int(self.config.get('seed', 0)),
            'fixed_weather': _as_bool(self.config.get('fixed_weather', False), default=False),
            'non_adaptive': _as_bool(self.config.get('non_adaptive', False), default=False),
            'hierarchical': _as_bool(self.config.get('hierarchical', False), default=False),
            'price_profile': str(self.config.get('price_profile', 'us_legacy')),
            'metrics': metrics,
        }
        path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        return str(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-fw', '--fixed_weather', default='False',
                        help='Whether to use a fixed weather')
    parser.add_argument('-na', '--non_adaptive', default='False',
                        help='Whether to use a non-adaptive policy (observation space being only a trailing window of'
                             'the crop rotation used so far')
    parser.add_argument('-hm', '--hierarchical', default='False',
                        help='Whether to use the hierarchical crop-planning + fertilization env')
    parser.add_argument('--use_pakistan_crop_calendar', default='False',
                        help='Enable Pakistan crop-calendar windows')
    parser.add_argument('--price_profile', default='pakistan_baseline',
                        help='Economics profile to use (e.g. us_legacy, pakistan_baseline)')
    parser.add_argument('--enable-thesis-reporting', default='True',
                        help='Enable hierarchical thesis CSV/JSON reporting outputs')
    parser.add_argument('--thesis-report-dir', default='',
                        help='Optional custom output folder for hierarchical reporting')
    parser.add_argument('--summary-json', default='',
                        help='Optional path for standardized run summary JSON')
    parser.add_argument('--without-tracking', action='store_true', default=False,
                        help='Disable W&B tracking and run with local no-op logger')
    parser.add_argument('-s', '--seed', type=int, default=0, metavar='N',
                        help='The random seed used for all number generators')
    parser.add_argument('-m', '--method', type=str.upper, default='PPO',
                        choices=['PPO', 'A2C', 'DQN'],
                        help='RL method to train (default: PPO)')

    args = vars(parser.parse_args())

    set_random_seed(args['seed'])
    np.random.seed(args['seed'])
    random.seed(args['seed'])

    if _as_bool(args['hierarchical'], default=False):
        env_class = 'HierarchicalCropPlanningFertilization'
        eval_env_class = 'HierarchicalCropPlanningFertilization'
    elif _as_bool(args['non_adaptive'], default=False):
        env_class = 'CropPlanningFixedPlantingRotationObserver'
        eval_env_class = 'CropPlanningFixedPlantingRotationObserver'
    else:
        env_class = 'CropPlanningFixedPlanting'
        eval_env_class = 'CropPlanningFixedPlanting'

    train_start_year = 2005
    train_end_year = 2018
    eval_start_year = 2019
    eval_end_year = 2019

    if _as_bool(args['fixed_weather'], default=False):
        weather_generator_class = 'FixedWeatherGenerator'
        weather_generator_kwargs = {
            'base_weather_file': CYCLES_PATH.joinpath('input', 'Pakistan_Site_final.weather')}
    else:
        weather_generator_class = 'WeatherShuffler'
        weather_generator_kwargs = dict(n_weather_samples=2,
                                        sampling_start_year=train_start_year,
                                        sampling_end_year=train_end_year,
                                        base_weather_file=CYCLES_PATH.joinpath('input', 'Pakistan_Site_final.weather'),
                                        target_year_range=np.arange(train_start_year, train_end_year + 1))

    config = dict(train_start_year=train_start_year, train_end_year=train_end_year, eval_start_year=eval_start_year, eval_end_year=eval_end_year,
                  total_timesteps=500, eval_freq=100, n_steps=80, batch_size=64, n_epochs=10, run_id=0,
                  norm_reward=True, method="PPO", verbose=1, n_process=1, device='auto',
                  env_class=env_class, eval_env_class=eval_env_class, weather_generator_class=weather_generator_class,
                  weather_generator_kwargs=weather_generator_kwargs,
                  hierarchical='False',
                  use_pakistan_crop_calendar='False',
                  nutrient_action_mode='NPK',
                  price_profile='pakistan_baseline',
                  maxN=150,
                  maxP=80.0,
                  maxK=60.0,
                  fert_n_actions=11,
                  p_actions=11,
                  k_actions=11,
                  fert_delta=7,
                  log_every_steps=1,
                  log_step_actions=True,
                  log_step_rewards=True,
                  enable_thesis_reporting='True',
                  thesis_report_dir='',
                  summary_json='')

    config.update(args)

    if args.get('without_tracking', False):
        wandb = _NoOpWandb()
        WandbCallback = _NoOpWandbCallback
    elif not _WANDB_TRACKING_AVAILABLE:
        raise ModuleNotFoundError(
            'wandb + wandb.integration.sb3 is required. Install wandb or pass --without-tracking.'
        )

    wandb.init(
        config=config,
        sync_tensorboard=True,
        project=CROP_PLANNING_EXPERIMENT,
        entity=WANDB_ENTITY,
        monitor_gym=True,  # automatically upload gym environements' videos
        save_code=True,
        dir=PROJECT_PATH,
    )

    config = wandb.config

    trainer = Train(config)
    model, eval_env = trainer.train()
    trainer.evaluate_log(model, eval_env)
