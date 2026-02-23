import numpy as np
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.evaluation import evaluate_policy

# Add project root to path so cyclesgym imports work
import sys
import os
sys.path.append(os.getcwd())

from cyclesgym.envs.corn import Corn
from cyclesgym.envs.weather_generator import WeatherShuffler
from cyclesgym.utils.paths import CYCLES_PATH

def make_env(start_year=1980, end_year=1980):
    env = Corn(delta=7, maxN=150, n_actions=11,
            start_year=start_year, end_year=end_year)
    return env

def main():
    # 1. Load the Environment
    # We use a DummyVecEnv because the model expects a vectorized environment
    env = DummyVecEnv([lambda: make_env(start_year=1980, end_year=1980)])

    # 2. Load Normalization Statistics
    # IMPORTANT: We must load the running averages (mean/std) from training
    # otherwise the agent sees completely different values than it was trained on.
    # Replace 'runs/vec_normalize_xw86rv5i.pkl' with the actual path if different
    stats_path = 'runs/vec_normalize_xw86rv5i.pkl' 
    
    try:
        env = VecNormalize.load(stats_path, env)
        # We want to test/evaluate, so we turn off training (updating stats)
        env.training = False 
        # We usually don't normalize rewards during inference, so we see real raw rewards
        env.norm_reward = False
        print(f"Loaded normalization stats from {stats_path}")
    except FileNotFoundError:
        print(f"Warning: Could not load normalization stats from {stats_path}. Running without normalization.")

    # 3. Load the Trained Agent
    model_path = '0.zip' # or 'experiments/fertilization/0.zip'
    try:
        model = PPO.load(model_path, env=env)
        print(f"Loaded model from {model_path}")
    except FileNotFoundError:
        print(f"Error: Could not find model at {model_path}")
        return

    # 4. Run the Agent
    episodes = 5
    print(f"\nRunning {episodes} episodes...")
    
    for episode in range(1, episodes + 1):
        obs = env.reset()
        done = False
        total_reward = 0
        step = 0
        
        print(f"--- Episode {episode} ---")
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            total_reward += reward[0] # VecEnv returns array of rewards
            
            # Un-normalize action if needed for printing (env does this internally)
            # The Corn env action is an index (0-10) mapping to N amount
            
            # Print steps if you want to see details
            # print(f"Step {step}: Action {action[0]}, Reward {reward[0]:.2f}")
            step += 1
            
        print(f"Episode {episode} finished. Total Reward: {total_reward:.2f}\n")

if __name__ == "__main__":
    main()
