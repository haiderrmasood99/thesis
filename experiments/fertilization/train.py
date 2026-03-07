import numpy as np
import warnings
warnings.filterwarnings("ignore")
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv, VecNormalize
from stable_baselines3.common.vec_env import VecMonitor
from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.utils import set_random_seed
from cyclesgym.envs.corn import Corn
from cyclesgym.utils.utils import EvalCallbackCustom, _evaluate_policy, JsonlTrainLoggerCallback
from cyclesgym.utils.wandb_utils import WANDB_ENTITY, FERTILIZATION_EXPERIMENT
import gymnasium as gym
from corn_soil_refined import CornSoilRefined, NonAdaptiveCorn
from pathlib import Path
from cyclesgym.utils.paths import PROJECT_PATH, CYCLES_PATH
from cyclesgym.envs.weather_generator import WeatherShuffler
import sys
from datetime import datetime
import json


from cyclesgym.policies.dummy_policies import OpenLoopPolicy
import expert
import argparse
import random
from cyclesgym.managers import WeatherManager

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

PAK_WEATHER_FILE = CYCLES_PATH.joinpath('input', 'Pakistan_Site_final.weather')


def _weather_year_bounds(weather_file):
    manager = WeatherManager(weather_file)
    years = manager.mutables['YEAR'].astype(int).to_numpy()
    return int(years.min()), int(years.max())


PAK_WEATHER_START_YEAR, PAK_WEATHER_END_YEAR = _weather_year_bounds(PAK_WEATHER_FILE)
PAK_DEFAULT_SAMPLING_END_YEAR = max(PAK_WEATHER_START_YEAR, PAK_WEATHER_END_YEAR - 1)


class Train:
    """ Trainer object to wrap model training and handle environment creation, evaluation """

    def __init__(self, experiment_config, with_obs_year) -> None:
        self.config = experiment_config
        self.with_obs_year = with_obs_year
        self.dir = wandb.run.dir
        self.model_dir = Path(self.dir).joinpath('models')
        # rl config is configured from wandb config

    def _nutrient_mode(self) -> str:
        return str(self.config.get('nutrient_action_mode', 'NPK')).upper()

    def _is_npk_mode(self) -> bool:
        return self._nutrient_mode() == 'NPK'

    def _mode_action_sequence(self, n_sequence):
        n_arr = np.asarray(n_sequence, dtype=np.int64)
        if not self._is_npk_mode():
            return n_arr
        zeros = np.zeros_like(n_arr, dtype=np.int64)
        return np.stack([n_arr, zeros, zeros], axis=1)

    def env_maker(self, training = True, n_procs = 1, soil_env = False, start_year = PAK_WEATHER_START_YEAR, end_year = PAK_WEATHER_START_YEAR,
        sampling_start_year=PAK_WEATHER_START_YEAR, sampling_end_year=PAK_DEFAULT_SAMPLING_END_YEAR,
        n_weather_samples=100, fixed_weather = True, with_obs_year=False,
        nonadaptive=False):

        def make_env():
            # creates a function returning the basic env. Used by SubprocVecEnv later to create a
            # vectorized environment
            def _f():
                nutrient_action_mode = self._nutrient_mode()
                max_n = float(self.config.get('maxN', 150.0))
                max_p = float(self.config.get('maxP', 80.0))
                max_k = float(self.config.get('maxK', 60.0))
                p_actions = int(self.config.get('p_actions', self.config.get('n_actions', 11)))
                k_actions = int(self.config.get('k_actions', self.config.get('n_actions', 11)))
                n_nh4_rate = float(self.config.get('n_nh4_rate', 0.75))
                price_profile = str(self.config.get('price_profile', 'pakistan_baseline'))

                if nonadaptive:
                    env = NonAdaptiveCorn(delta=7, maxN=max_n, n_actions=self.config['n_actions'],
                            start_year = start_year, end_year = end_year,
                            sampling_start_year=sampling_start_year,
                            sampling_end_year=sampling_end_year,
                            n_weather_samples=n_weather_samples,
                            fixed_weather=fixed_weather,
                            with_obs_year=with_obs_year,
                            nutrient_action_mode=nutrient_action_mode,
                            maxP=max_p,
                            maxK=max_k,
                            p_actions=p_actions,
                            k_actions=k_actions,
                            n_nh4_rate=n_nh4_rate,
                            price_profile=price_profile)
                else:
                    if soil_env:
                        env = CornSoilRefined(delta=7, maxN=max_n, n_actions=self.config['n_actions'],
                            start_year = start_year, end_year = end_year,
                            sampling_start_year=sampling_start_year,
                            sampling_end_year=sampling_end_year,
                            n_weather_samples=n_weather_samples,
                            fixed_weather=fixed_weather,
                            with_obs_year=with_obs_year,
                            nutrient_action_mode=nutrient_action_mode,
                            maxP=max_p,
                            maxK=max_k,
                            p_actions=p_actions,
                            k_actions=k_actions,
                            n_nh4_rate=n_nh4_rate,
                            price_profile=price_profile)
                    else:
                        if fixed_weather:
                            env = Corn(delta=7, maxN=max_n, n_actions=self.config['n_actions'],
                                nutrient_action_mode=nutrient_action_mode,
                                maxP=max_p,
                                maxK=max_k,
                                p_actions=p_actions,
                                k_actions=k_actions,
                                n_nh4_rate=n_nh4_rate,
                                price_profile=price_profile,
                                start_year = start_year, end_year = end_year)
                        else:
                            target_year_range = np.arange(start_year, end_year + 1)
                            weather_generator_kwargs = dict(
                                n_weather_samples=n_weather_samples,
                                sampling_start_year=sampling_start_year,
                                sampling_end_year=sampling_end_year,
                                target_year_range=target_year_range,
                                base_weather_file=PAK_WEATHER_FILE)
                            env = Corn(delta=7, maxN=max_n, n_actions=self.config['n_actions'],
                                       nutrient_action_mode=nutrient_action_mode,
                                       maxP=max_p,
                                       maxK=max_k,
                                       p_actions=p_actions,
                                       k_actions=k_actions,
                                       n_nh4_rate=n_nh4_rate,
                                       price_profile=price_profile,
                                       start_year=start_year, end_year=end_year,
                                       weather_generator_class=WeatherShuffler,
                                       weather_generator_kwargs=weather_generator_kwargs)

                #env = Monitor(env, 'runs')
                env = gym.wrappers.RecordEpisodeStatistics(env)
                return env
            return _f

        # Windows-safe vector env: use 'spawn' or DummyVecEnv when n_procs=1
        if n_procs and n_procs > 1:
            env = SubprocVecEnv([make_env() for _ in range(n_procs)], start_method='spawn')
        else:
            env = DummyVecEnv([make_env()])

        env = VecMonitor(env, 'runs')

        #only norm the reward if we selected to do so and if we are in training
        norm_reward = (training and self.config['norm_reward'])

        #high clipping values so that they effectively get ignored
        env = VecNormalize(env, norm_obs=True, norm_reward= norm_reward, clip_obs=20000., clip_reward=20000.)

        return env

    def long_env_maker(self, training = True, n_procs = 1, soil_env = False, start_year = PAK_WEATHER_START_YEAR, end_year = PAK_WEATHER_START_YEAR,
        sampling_start_year=PAK_WEATHER_START_YEAR, sampling_end_year=PAK_DEFAULT_SAMPLING_END_YEAR,
        n_weather_samples=100, fixed_weather = True, with_obs_year=False, nonadaptive=False):
        """
        for single year testing we want to have an env that is identical to others but just a longer time horizon
        """
        def f(years):
            return self.env_maker(training = False, soil_env = self.config['soil_env'],
                        start_year = self.config['start_year'], end_year = self.config['end_year']+years-1,
                        sampling_start_year=self.config['sampling_start_year'],
                        sampling_end_year=self.config['sampling_end_year'],
                        n_weather_samples=self.config['n_weather_samples'],
                        fixed_weather = self.config['fixed_weather'],
                        with_obs_year=self.with_obs_year,
                        nonadaptive=self.config['nonadaptive'])
        return f

    def get_envs(self, n_procs, plus_horizon=0):
        """
        Returns some environments given n_procs. Used because I often want the same settings
        but a different n_procs for policy visualization and baseline evaluations
        """
        weather_min_year, weather_max_year = PAK_WEATHER_START_YEAR, PAK_WEATHER_END_YEAR

        sim_start_year = min(max(self.config['start_year'], weather_min_year), weather_max_year)
        sim_end_year = min(max(self.config['end_year'], sim_start_year), weather_max_year)
        sim_end_year_with_horizon = min(sim_end_year + plus_horizon, weather_max_year)

        train_sampling_start_year = min(max(self.config['sampling_start_year'], weather_min_year), weather_max_year)
        train_sampling_end_year = min(max(self.config['sampling_end_year'], train_sampling_start_year), weather_max_year)

        hold_out_sampling_start_year = min(train_sampling_end_year + 1, weather_max_year)
        hold_out_sampling_end_year = weather_max_year
        duration = sim_end_year - sim_start_year 

        # The test environment will automatically have the same observation normalization applied to it by 
        # EvalCallBack
        eval_env_train = self.env_maker(training = False, n_procs=n_procs,
            soil_env = self.config['soil_env'],
            start_year = sim_start_year, end_year = sim_end_year_with_horizon,
            sampling_start_year=train_sampling_start_year,
            sampling_end_year=train_sampling_end_year,
            n_weather_samples=self.config['n_weather_samples'],
            fixed_weather = self.config['fixed_weather'],
            with_obs_year=self.with_obs_year,
            nonadaptive=self.config['nonadaptive'])

        # the out-of-sample weather env
        start_year = hold_out_sampling_start_year
        end_year = min(hold_out_sampling_start_year + duration, hold_out_sampling_end_year)
        test_sampling_start_year = hold_out_sampling_start_year
        test_sampling_end_year = hold_out_sampling_end_year
        test_fixed_weather = False
        if self.config['fixed_weather']:
            # For fixed-weather runs, keep test env fixed as well.
            # Otherwise we force weather shuffling on a 1-year holdout window (2019),
            # which can fail for multi-year one_year_eval horizons.
            end_year = train_sampling_end_year
            start_year = max(weather_min_year, end_year-duration)
            test_sampling_start_year = train_sampling_start_year
            test_sampling_end_year = train_sampling_end_year
            test_fixed_weather = True
        eval_env_test = self.env_maker(training = False, n_procs=n_procs,
            soil_env = self.config['soil_env'],
            start_year = start_year, end_year = min(end_year + plus_horizon, weather_max_year),
            sampling_start_year=test_sampling_start_year,
            sampling_end_year=test_sampling_end_year,
            n_weather_samples=self.config['n_weather_samples'],
            fixed_weather = test_fixed_weather,
            with_obs_year=self.with_obs_year,
            nonadaptive=self.config['nonadaptive'])

        eval_env_train.training = False
        eval_env_train.norm_reward = False
        eval_env_test.training = False
        eval_env_test.norm_reward = False

        return eval_env_train, eval_env_test


    def get_eval_callbacks(self):
        """
        generates all callbacks plus test and train envs
        """
        eval_freq = int(self.config['eval_freq'] / self.config['n_process'])
        eval_env_train, eval_env_test = self.get_envs(n_procs=self.config['n_process'])

        eval_callback_test_det = EvalCallbackCustom(eval_env_test, best_model_save_path=str(self.model_dir.joinpath('best_eval_test_det')),
            log_path=str(self.model_dir.joinpath('eval_test_det')),
            eval_freq=eval_freq, deterministic=True, render=False,
            eval_prefix='eval_test_det')
        eval_callback_test_sto = EvalCallbackCustom(eval_env_test, best_model_save_path=None,
            log_path=str(self.model_dir.joinpath('eval_test_sto')),
            eval_freq=eval_freq, deterministic=False, render=False,
            eval_prefix='eval_test_sto')

        eval_callback_det = EvalCallbackCustom(eval_env_train, best_model_save_path=None,
            log_path=str(self.model_dir.joinpath('eval_train_det')),
            eval_freq=eval_freq, deterministic=True, render=False,
            eval_prefix='eval_train_det')
        eval_callback_sto = EvalCallbackCustom(eval_env_train, best_model_save_path=str(self.model_dir.joinpath('train_sto')),
            log_path=str(self.model_dir.joinpath('eval_train_sto')),
            eval_freq=eval_freq, deterministic=False, render=False,
            eval_prefix='eval_train_sto')

        callback = [WandbCallback(model_save_path=str(self.model_dir), model_save_freq=int(self.config['eval_freq'] / self.config['n_process'])),
            eval_callback_det, eval_callback_sto,
            eval_callback_test_det, eval_callback_test_sto]
        return callback

    def train(self):
        
        train_env = self.env_maker(training = True, n_procs=self.config['n_process'], soil_env = self.config['soil_env'],
         start_year = self.config['start_year'], end_year = self.config['end_year'], 
         sampling_start_year=self.config['sampling_start_year'],
         sampling_end_year=self.config['sampling_end_year'],
         n_weather_samples=self.config['n_weather_samples'],
         fixed_weather = self.config['fixed_weather'],
         with_obs_year=self.with_obs_year,
         nonadaptive=self.config['nonadaptive'])

        train_env.seed(self.config['seed'])

        eval_freq = int(self.config['eval_freq'] / self.config['n_process'])
        duration = self.config['end_year'] - self.config['start_year']
        total_timesteps = self.config["total_years"] * 53
        n_steps = int(self.config['n_steps'] / self.config['n_process'])
        tensorboard_log = None if bool(self.config.get('without_tracking', False)) else self.dir

        if self.config["method"] == "A2C":
            model = A2C('MlpPolicy', train_env, verbose=0, ent_coef=self.config.get('ent_coef', 0.0), tensorboard_log=tensorboard_log)
        elif self.config["method"] == "PPO":
            model = PPO('MlpPolicy', train_env, verbose=0, n_steps= n_steps, ent_coef=self.config.get('ent_coef', 0.0), tensorboard_log=tensorboard_log)
        elif self.config["method"] == "DQN":
            model = DQN('MlpPolicy', train_env, verbose=0, tensorboard_log=tensorboard_log)
        else:
            raise Exception("Not an RL method that has been implemented")


        callback = self.get_eval_callbacks()
        log_path = self.config.get('log_json_path')
        if not log_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = str(PROJECT_PATH.joinpath('runs', 'train_logs', f'fertilization_{ts}.jsonl'))
        callback.append(JsonlTrainLoggerCallback(
            log_path=log_path,
            log_every_steps=int(self.config.get('log_every_steps', 1)),
            log_step_actions=bool(self.config.get('log_step_actions', True)),
            log_step_rewards=bool(self.config.get('log_step_rewards', True)),
            log_rollout=True
        ))
        
        print("Initialization complete. Starting training... Progress bar should appear shortly.")
        model.learn(total_timesteps=total_timesteps, callback=callback, progress_bar=True)
        model.save(str(self.config['run_id'])+'.zip')
        stats_path = Path(self.config['stats_path'])
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        train_env.save(stats_path)
        return model

    def evaluate_log(self, model, eval_env):
        """
        Runs policy deterministically (1 episode) and stochastically (5 episodes)
        logs the fertilization actions taken by the model

        Parameters
        ----------
        model: trained agent
        eval_env

        Returns
        -------
        mean deterministic reward

        """
        # list, list, numpy array, list
        mean_r_det, std_r_det, actions_det, episode_rewards_det, _, _ = _evaluate_policy(model,
                                                                                         env=eval_env,
                                                                                         n_eval_episodes=1,
                                                                                         deterministic=True)

        mean_r_stoc, std_r_stoc, actions_stoc, episode_rewards_stoc, _, _ = _evaluate_policy(model,
                                                                                            env=eval_env,
                                                                                            n_eval_episodes=5,
                                                                                            deterministic=False)

        metrics = {
            'deterministic_return': float(mean_r_det),
            'stochastic_return_mean': float(mean_r_stoc),
            'stochastic_return_std': float(std_r_stoc),
        }
        wandb.log(metrics)

        episode_actions_names = [
            *list(f"det{i + 1}" for i in range(len(actions_det))),
            *list(f"stoc{i + 1}" for i in range(len(actions_stoc)))
        ]
        episode_actions = [*actions_det, *actions_stoc]
        if not episode_actions:
            return metrics

        sample_action = np.asarray(episode_actions[0])

        if sample_action.ndim == 1:
            # Legacy N-only runs.
            T = int(sample_action.shape[0])
            fertilizer_table = wandb.Table(
                columns=['Run', 'Total Fertilizer', *[f'Week{i}' for i in range(T)]]
            )
            for i, acts in enumerate(episode_actions):
                acts_arr = np.asarray(acts)
                data = [[week, fert] for (week, fert) in zip(range(T), acts_arr)]
                table = wandb.Table(data=data, columns=['Week', 'N added'])
                fertilizer_table.add_data(
                    *[episode_actions_names[i], float(np.sum(acts_arr)), *acts_arr.tolist()]
                )
                try:
                    wandb.log({
                        f'train/actions/{episode_actions_names[i]}': wandb.plot.bar(
                            table, 'Week', 'N added',
                            title=f'Training action sequence {episode_actions_names[i]}'
                        )
                    })
                except FileNotFoundError as e:
                    print(f"Warning: Failed to log action sequence {episode_actions_names[i]} due to FileNotFoundError: {e}")
            try:
                wandb.log({'train/fertilizer': fertilizer_table})
            except FileNotFoundError as e:
                print(f"Warning: Failed to log fertilizer table due to FileNotFoundError: {e}")
        elif sample_action.ndim == 2:
            # NPK runs: action shape is [T, C]
            T = int(sample_action.shape[0])
            channels = int(sample_action.shape[1])
            nutrient_names = ['N', 'P', 'K']
            nutrient_names = nutrient_names[:channels] + [f'X{i}' for i in range(max(0, channels - len(nutrient_names)))]

            fertilizer_table = wandb.Table(
                columns=['Run', *[f'Total_{n}' for n in nutrient_names]]
            )

            for i, acts in enumerate(episode_actions):
                acts_arr = np.asarray(acts, dtype=np.int64)
                totals = acts_arr.sum(axis=0).tolist()
                fertilizer_table.add_data(*[episode_actions_names[i], *totals])

                for j, nutrient in enumerate(nutrient_names):
                    data = [[week, int(acts_arr[week, j])] for week in range(T)]
                    table = wandb.Table(data=data, columns=['Week', f'{nutrient} action'])
                    try:
                        wandb.log({
                            f'train/actions/{episode_actions_names[i]}_{nutrient}': wandb.plot.bar(
                                table, 'Week', f'{nutrient} action',
                                title=f'{nutrient} action sequence {episode_actions_names[i]}'
                            )
                        })
                    except FileNotFoundError as e:
                        print(f"Warning: Failed to log {nutrient} sequence for {episode_actions_names[i]} due to FileNotFoundError: {e}")
            try:
                wandb.log({'train/fertilizer_npk': fertilizer_table})
            except FileNotFoundError as e:
                print(f"Warning: Failed to log NPK fertilizer table due to FileNotFoundError: {e}")

        ## create a plot of the reward in each year
        ## create a plot of fertilizer cost in each year
        return metrics

    def eval_openloop(self, action_series, eval_env, name):
        action_series_int = np.array(action_series, dtype=int)
        expert_policy = OpenLoopPolicy(action_series_int)
        r, _ = evaluate_policy(expert_policy,
                                eval_env,
                                n_eval_episodes=100,
                                deterministic=True)
        wandb.log({f'train/baseline/'+name: r})
        return float(r)

    def one_year_eval(self, model):
        """
        An evaluation to test the one year policy on 2,5,10 years
        """
        for long_len in [2, 5]:
            #env = long_env(long_len)
            env, _  = self.get_envs(n_procs = 1, plus_horizon=long_len-1)
            env = VecNormalize.load(self.config['stats_path'], env)
            env.training = False
            env.norm_reward = False
            
            r_det, _ = evaluate_policy(model,
                                env,
                                n_eval_episodes=20,
                                deterministic=True)
            
            r_sto, _ = evaluate_policy(model,
                                env,
                                n_eval_episodes=20,
                                deterministic=False)
            
            name = "long_eval_det"+str(long_len)
            wandb.log({f'eval/'+name: r_det})
            name = "long_eval_sto"+str(long_len)
            wandb.log({f'eval/'+name: r_sto})
        return

    def eval_baselines(self):
        ## evaluate baseline strategies on the train and test envs
        #make an env on 1 process for open loop policies and vis
        eval_env_train, eval_env_test = self.get_envs(n_procs = 1)

        agro_exact_sequence = expert.create_action_sequence(doy=[110, 155], weight=[35, 120],
                                             maxN=self.config['maxN'],
                                             n_actions=self.config['n_actions'],
                                             delta_t=7)

        nonsense_exact_sequence = expert.create_action_sequence(doy=[110, 155, 300], weight=[35, 120, 50],
                                             maxN=self.config['maxN'],
                                             n_actions=self.config['n_actions'],
                                             delta_t=7)

        cycles_exact_sequence = expert.create_action_sequence(doy=110, weight=150,
                                             maxN=self.config['maxN'],
                                             n_actions=self.config['n_actions'],
                                             delta_t=7)

        organic_exact_sequence = expert.create_action_sequence(doy=110, weight=0,
                                             maxN=self.config['maxN'],
                                             n_actions=self.config['n_actions'],
                                             delta_t=7)
        
        n = self.config['end_year'] - self.config['start_year']
        agro_exact_sequence = make_multi_year(agro_exact_sequence, n)
        nonsense_exact_sequence = make_multi_year(nonsense_exact_sequence, n)
        cycles_exact_sequence = make_multi_year(cycles_exact_sequence, n)
        organic_exact_sequence = make_multi_year(organic_exact_sequence, n)
        agro_exact_sequence = self._mode_action_sequence(agro_exact_sequence)
        nonsense_exact_sequence = self._mode_action_sequence(nonsense_exact_sequence)
        cycles_exact_sequence = self._mode_action_sequence(cycles_exact_sequence)
        organic_exact_sequence = self._mode_action_sequence(organic_exact_sequence)
        out = {}
        out["organic_train"] = self.eval_openloop(organic_exact_sequence, eval_env_train, "organic-train")
        out["agro_train"] = self.eval_openloop(agro_exact_sequence, eval_env_train, "agro-train")
        out["cycles_train"] = self.eval_openloop(cycles_exact_sequence, eval_env_train, "cycles-train")
        out["nonsense_train"] = self.eval_openloop(nonsense_exact_sequence, eval_env_train, "nonsense-train")

        out["organic_test"] = self.eval_openloop(organic_exact_sequence, eval_env_test, "organic-test")
        out["agro_test"] = self.eval_openloop(agro_exact_sequence, eval_env_test, "agro-test")
        out["cycles_test"] = self.eval_openloop(cycles_exact_sequence, eval_env_test, "cycles-test")
        out["nonsense_test"] = self.eval_openloop(nonsense_exact_sequence, eval_env_test, "nonsense-test")

        return out

    def write_standardized_summary(self, metrics: dict):
        out_path = self.config.get('summary_json')
        if not out_path:
            out_path = str(
                PROJECT_PATH.joinpath('runs', 'experiment_summaries', 'metrics', f'fertilization_{wandb.run.id}.json')
            )
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'timestamp': datetime.now().isoformat(),
            'run_id': wandb.run.id,
            'domain': 'fertilization',
            'method': str(self.config.get('method')),
            'seed': int(self.config.get('seed', 0)),
            'fixed_weather': bool(self.config.get('fixed_weather', False)),
            'nonadaptive': bool(self.config.get('nonadaptive', False)),
            'total_years': int(self.config.get('total_years', 0)),
            'baseline': bool(self.config.get('baseline', False)),
            'nutrient_action_mode': self._nutrient_mode(),
            'price_profile': str(self.config.get('price_profile', 'pakistan_baseline')),
            'metrics': metrics,
        }
        path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        wandb.log({'summary_json_path': str(path)})
        return str(path)

    def eval_nh(self,model):
        """
        evaluate the model on Pakistan holdout years
        """
        _, eval_env  = self.get_envs(n_procs = 1)
        eval_env = VecNormalize.load(self.config['stats_path'], eval_env)
        eval_env.training = False
        eval_env.norm_reward = False
        
        mean_r, _  = evaluate_policy(model,
           env=eval_env,
           n_eval_episodes=20,
           deterministic=False)
        wandb.log({'pak_holdout_return': mean_r})
        return float(mean_r)


def make_multi_year(action_seq, n):
    # n is an int for number of years
    return np.concatenate([action_seq, np.tile(action_seq[1:], n)])


if __name__ == '__main__':
    RANDOM_SEED = 0
    if ('-h' in sys.argv) or ('--help' in sys.argv):
        pass
    elif '--without-tracking' in sys.argv:
        wandb = _NoOpWandb()
        WandbCallback = _NoOpWandbCallback
    elif not _WANDB_TRACKING_AVAILABLE:
        raise ModuleNotFoundError(
            'wandb + wandb.integration.sb3 is required. Install wandb or pass --without-tracking.'
        )
    """
    torch.manual_seed(RANDOM_SEED)
    env.seed(RANDOM_SEED)
    """
    config = dict(total_years = 3000, 
                  eval_freq = 1000, run_id = 0,
                  norm_reward = True,
                  method = "PPO", 
                  ent_coef = 0.0,
                  n_actions = 11, 
                  nutrient_action_mode = "NPK",
                  price_profile = "pakistan_baseline",
                  maxN = 150.0,
                  maxP = 80.0,
                  maxK = 60.0,
                  p_actions = 11,
                  k_actions = 11,
                  n_nh4_rate = 0.75,
                  soil_env=True, 
                  start_year = PAK_WEATHER_START_YEAR,
                  sampling_start_year=PAK_WEATHER_START_YEAR, 
                  sampling_end_year=PAK_DEFAULT_SAMPLING_END_YEAR,
                  n_weather_samples=100, 
                  n_steps = 2048, 
                  with_obs_year = True,
                  log_every_steps = 1,
                  log_step_actions = True,
                  log_step_rewards = True,
                  summary_json = '')
    wandb.init(
    config=config,
    sync_tensorboard=True,
    project=FERTILIZATION_EXPERIMENT,
    entity=WANDB_ENTITY,
    monitor_gym=True,       # automatically upload gym environements' videos
    save_code=True,
    group="group_name",
    dir=PROJECT_PATH
    )

    

    parser = argparse.ArgumentParser()
    parser.add_argument('-np', '--n-process', type=int, default=1, metavar='N',
                         help='input number of processes for training (default: 1)')
    parser.add_argument('-ey', '--end-year', type=int, default=PAK_WEATHER_START_YEAR, metavar='N',
                         help='The final year of simulation (default: 2005)')
    parser.add_argument('-na','--nonadaptive', default=False, action='store_true',
        help='Whether to learn a nonadaptive policy')
    parser.add_argument('-fw','--fixed-weather', default=False, action='store_true',
        help='Whether to use a fixed weather')
    parser.add_argument('-s', '--seed', type=int, default=0, metavar='N',
                         help='The random seed used for all number generators')
    parser.add_argument('-ty', '--total-years', type=int, default=25, metavar='N',
                        help='Total years of training (default: 25)')
    parser.add_argument('-b','--baseline', default=False, action='store_true',
        help='Use to only run the baselines')
    parser.add_argument('-p','--posthoc', default=False, action='store_true',
        help='Parse to read in a set of weights that are evaluated')
    parser.add_argument('-ef', '--eval-freq', type=int, default=1000, metavar='N',
                        help='Evaluation frequency in steps (default: 1000)')
    parser.add_argument('-ec', '--ent-coef', type=float, default=0.0, metavar='N',
                        help='Entropy coefficient for the loss calculation (default: 0.0)')
    parser.add_argument('-m', '--method', type=str.upper, default='PPO',
                        choices=['PPO', 'A2C', 'DQN'],
                        help='RL method to train (default: PPO)')
    parser.add_argument('--nutrient-action-mode', type=str.upper, default='NPK',
                        choices=['N', 'NPK'],
                        help='N-only or NPK fertilization action mode')
    parser.add_argument('--price-profile', default='pakistan_baseline',
                        help='Economics profile to use (e.g. us_legacy, pakistan_baseline)')
    parser.add_argument('--maxN', type=float, default=150.0,
                        help='Max N kg/ha per application')
    parser.add_argument('--maxP', type=float, default=80.0,
                        help='Max P kg/ha per application (NPK mode)')
    parser.add_argument('--maxK', type=float, default=60.0,
                        help='Max K kg/ha per application (NPK mode)')
    parser.add_argument('--p-actions', type=int, default=11,
                        help='Number of discrete bins for P channel (NPK mode)')
    parser.add_argument('--k-actions', type=int, default=11,
                        help='Number of discrete bins for K channel (NPK mode)')
    parser.add_argument('--n-nh4-rate', type=float, default=0.75,
                        help='Fraction of N allocated to NH4 when applying N')
    parser.add_argument('--without-tracking', action='store_true', default=False,
                        help='Disable W&B tracking and run with local no-op logger')
    parser.add_argument('--summary-json', default='',
                        help='Optional path for standardized run summary JSON')

    args = parser.parse_args()

    wandb.config.update(args, allow_val_change=True)

    if wandb.config['posthoc']:
        stats_path = 'data/vec_norms/vec_normalize_1xw45c9p.pkl'
    else:
        stats_path = 'runs/vec_normalize_' + str(wandb.run.id) + '.pkl' 
    
    wandb.config.update({'stats_path': stats_path})

    # make a plain dict copy so it can be safely pickled by SubprocVecEnv
    config = dict(wandb.config)

    # Keep all years within the available Pakistan weather range.
    if config['start_year'] < PAK_WEATHER_START_YEAR:
        config['start_year'] = PAK_WEATHER_START_YEAR
    if config['end_year'] < PAK_WEATHER_START_YEAR:
        config['end_year'] = PAK_WEATHER_START_YEAR
    if config['end_year'] > PAK_WEATHER_END_YEAR:
        config['end_year'] = PAK_WEATHER_END_YEAR
    if config['end_year'] < config['start_year']:
        config['end_year'] = config['start_year']
    if config['sampling_start_year'] < PAK_WEATHER_START_YEAR:
        config['sampling_start_year'] = PAK_WEATHER_START_YEAR
    if config['sampling_end_year'] > PAK_WEATHER_END_YEAR:
        config['sampling_end_year'] = PAK_WEATHER_END_YEAR
    if config['sampling_end_year'] < config['sampling_start_year']:
        config['sampling_end_year'] = config['sampling_start_year']
    config['nutrient_action_mode'] = str(config.get('nutrient_action_mode', 'NPK')).upper()
    if config['nutrient_action_mode'] not in {'N', 'NPK'}:
        config['nutrient_action_mode'] = 'NPK'
    config['p_actions'] = max(2, int(config.get('p_actions', config.get('n_actions', 11))))
    config['k_actions'] = max(2, int(config.get('k_actions', config.get('n_actions', 11))))
    config['n_actions'] = max(2, int(config.get('n_actions', 11)))
    config['maxN'] = max(0.0, float(config.get('maxN', 150.0)))
    config['maxP'] = max(0.0, float(config.get('maxP', 80.0)))
    config['maxK'] = max(0.0, float(config.get('maxK', 60.0)))
    config['n_nh4_rate'] = float(np.clip(float(config.get('n_nh4_rate', 0.75)), 0.0, 1.0))

    set_random_seed(config['seed'])
    np.random.seed(config['seed'])
    random.seed(config['seed'])
    print("status")
    #if we do a 1 year experiment, we don't include obs year (not useful)
    with_obs_year = config['with_obs_year'] and (config['start_year'] != config['end_year'])
    trainer = Train(config, with_obs_year)
    
    #if trying to get baselines...
    if config['baseline']:
        baseline_returns = trainer.eval_baselines()
        baseline_best = max(baseline_returns.values()) if baseline_returns else None
        trainer.write_standardized_summary({
            'baseline_returns': baseline_returns,
            'baseline_best_return': float(baseline_best) if baseline_best is not None else None,
        })
    else:
        if config['posthoc']:
            file = PROJECT_PATH.joinpath('experiments/data/model.zip')
            model = PPO.load(file, device='cpu')
        else:
            model = trainer.train()

        # Load the saved statistics

        _, eval_env_test = trainer.get_envs(n_procs = 1)

        eval_env_test = VecNormalize.load(config['stats_path'], eval_env_test)
        #  do not update moving averages at test time
        eval_env_test.training = False
        # reward normalization is not needed at test time
        eval_env_test.norm_reward = False
        
        metrics = trainer.evaluate_log(model, eval_env_test)
        
        if config['start_year'] == config['end_year']:
            trainer.one_year_eval(model)
        
        metrics['pak_holdout_return'] = trainer.eval_nh(model)
        trainer.write_standardized_summary(metrics)






    
    
