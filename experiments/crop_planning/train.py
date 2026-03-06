import numpy as np
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv, VecNormalize
from stable_baselines3.common.vec_env import VecMonitor
from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.utils import set_random_seed
from cyclesgym.utils.utils import EvalCallbackCustom, _evaluate_policy, JsonlTrainLoggerCallback
from cyclesgym.utils.wandb_utils import WANDB_ENTITY, CROP_PLANNING_EXPERIMENT
from cyclesgym.utils.paths import PROJECT_PATH, CYCLES_PATH
from pathlib import Path
import gymnasium as gym
from cyclesgym.envs.corn import Corn
from cyclesgym.envs.crop_planning import CropPlanning, CropPlanningFixedPlanting
from cyclesgym.envs.crop_planning import CropPlanningFixedPlantingRotationObserver
from cyclesgym.envs.weather_generator import FixedWeatherGenerator, WeatherShuffler
import wandb
from wandb.integration.sb3 import WandbCallback
import random
import argparse
from datetime import datetime


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
                env_conf = dict(start_year=start_year, end_year=end_year, soil_file=soil_file,
                                weather_generator_class=weather_generator_class,
                                weather_generator_kwargs=weather_generator_kwargs,
                                rotation_crops=['CornRM.100', 'SoybeanMG.3'])
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

        if self.config["method"] == "A2C":
            model = A2C('MlpPolicy', train_env, verbose=self.config['verbose'], tensorboard_log=dir,
                        device=self.config['device'])
        elif self.config["method"] == "PPO":
            model = PPO('MlpPolicy', train_env, n_steps=self.config['n_steps'], batch_size=self.config['batch_size'],
                        n_epochs=self.config['n_epochs'], verbose=self.config['verbose'], tensorboard_log=dir,
                        device=self.config['device'])
        elif self.config["method"] == "DQN":
            model = DQN('MlpPolicy', train_env, verbose=self.config['verbose'], tensorboard_log=dir,
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
        mean_r_det, _, actions_det, episode_rewards_det, _, _ = _evaluate_policy(model,
                                                                                 env=eval_env,
                                                                                 n_eval_episodes=1,
                                                                                 deterministic=True)
        mean_r_stoc, std_r_stoc, actions_stoc, episode_rewards_stoc, _, _ = _evaluate_policy(model,
                                                                                              env=eval_env,
                                                                                              n_eval_episodes=5,
                                                                                              deterministic=False)
        wandb.log({'deterministic_return': mean_r_det,
                   'stochastic_return_mean': mean_r_stoc,
                   'stochastic_return_std': std_r_stoc,
                   })
        episode_actions_names = [*list(f"det{i + 1}" for i in range(len(actions_det))),
                                 *list(f"stoc{i + 1}" for i in range(len(actions_stoc)))]
        episode_actions = [*actions_det, *actions_stoc]
        T = actions_stoc.shape[1]
        fertilizer_table = wandb.Table(
            columns=['Run', 'Total Fertilizer', *[f'Week{i}' for i in range(T)]])
        for i in range(len(episode_actions)):
            acts = episode_actions[i]
            data = [[week, fert] for (week, fert) in zip(range(T), acts)]
            table = wandb.Table(data=data, columns=['Week', 'N added'])
            fertilizer_table.add_data(
                *[episode_actions_names[i], np.sum(acts), *acts])
            wandb.log({f'train/actions/{episode_actions_names[i]}':
                           wandb.plot.bar(table, 'Week', 'N added',
                                          title=f'Training action sequence {episode_actions_names[i]}')})
        wandb.log({'train/fertilizer': fertilizer_table})
        return mean_r_det


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-fw', '--fixed_weather', default='False',
                        help='Whether to use a fixed weather')
    parser.add_argument('-na', '--non_adaptive', default='False',
                        help='Whether to use a non-adaptive policy (observation space being only a trailing window of'
                             'the crop rotation used so far')
    parser.add_argument('-s', '--seed', type=int, default=0, metavar='N',
                        help='The random seed used for all number generators')
    parser.add_argument('-m', '--method', type=str.upper, default='PPO',
                        choices=['PPO', 'A2C', 'DQN'],
                        help='RL method to train (default: PPO)')

    args = vars(parser.parse_args())

    set_random_seed(args['seed'])
    np.random.seed(args['seed'])
    random.seed(args['seed'])

    if args['non_adaptive'] == 'True':
        env_class = 'CropPlanningFixedPlantingRotationObserver'
        eval_env_class = 'CropPlanningFixedPlantingRotationObserver'
    else:
        env_class = 'CropPlanningFixedPlanting'
        eval_env_class = 'CropPlanningFixedPlanting'

    train_start_year = 2005
    train_end_year = 2018
    eval_start_year = 2019
    eval_end_year = 2019

    if args['fixed_weather'] == 'True':
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
                  log_every_steps=1,
                  log_step_actions=True,
                  log_step_rewards=True)

    config.update(args)

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
