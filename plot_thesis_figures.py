import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
try:
    import gymnasium as gym
except ImportError:
    import gym
import cyclesgym
from cyclesgym.envs.corn import Corn
from stable_baselines3 import PPO
from cyclesgym.utils.paths import PROJECT_PATH, FIGURES_PATH
import glob
import os

import sys
# Add experiments to path to allow importing specialized environments
sys.path.append(str(PROJECT_PATH.joinpath('experiments', 'fertilization')))

try:
    from corn_soil_refined import CornSoilRefined
except ImportError:
    print("Could not import CornSoilRefined. Make sure 'experiments/fertilization' is in path.")
    raise

def plot_training_curve(log_dir="runs"):
    """
    Scans for monitor.csv files in log_dir and plots the moving average of rewards.
    """
    print(f"Searching for training logs in {log_dir}...")
    monitor_files = glob.glob(os.path.join(log_dir, "*.monitor.csv"))
    
    if not monitor_files:
        print("No training logs found. Run a training session first!")
        return

    plt.figure(figsize=(10, 6))
    
    for file in monitor_files:
        try:
            # Read skip first 1 line (metadata)
            df = pd.read_csv(file, skiprows=1)
            
            # Boxcar average for smoothing
            window_size = 50
            if len(df) > window_size:
                df['reward_smooth'] = df['r'].rolling(window=window_size).mean()
                plt.plot(df['l'].cumsum(), df['reward_smooth'], label=os.path.basename(file))
            else:
                 plt.plot(df['l'].cumsum(), df['r'], label=os.path.basename(file), alpha=0.5)

        except Exception as e:
            print(f"Could not read {file}: {e}")

    plt.xlabel('Total Timesteps')
    plt.ylabel('Episode Reward (Smoothed)')
    plt.title('Agent Training Progress (Cumulative Reward)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_path = FIGURES_PATH.joinpath('thesis_training_curve.png')
    plt.savefig(output_path)
    print(f"Saved training curve to {output_path}")
    plt.close()

def plot_agent_policy(model_path=None):
    """
    Loads a trained model and runs one season to visualize decisions.
    """
    print("Visualizing Agent Policy...")
    
    # 1. Create Environment (Matching train.py defaults: CornSoilRefined)
    # n_actions=11, maxN=150, start/end=1980, with_obs_year=False (since single year)
    env = CornSoilRefined(delta=7, n_actions=11, maxN=150, 
                         start_year=1980, end_year=1980,
                         sampling_start_year=1980, sampling_end_year=2005,
                         n_weather_samples=100, fixed_weather=False,
                         with_obs_year=False)

    
    # 2. Load Agent
    if model_path and os.path.exists(model_path):
        print(f"Loading model from {model_path}")
        model = PPO.load(model_path)
    else:
        print("No valid model path provided. Running with UNTRAINED random agent for demonstration.")
        model = None

    # 3. Run Episode
    obs = env.reset()
    if isinstance(obs, tuple):
        obs = obs[0]
        
    done = False
    
    # Track data
    weeks = []
    actions = []
    
    week_counter = 0
    while not done:
        if model:
            action, _ = model.predict(obs)
        else:
            action = env.action_space.sample() # Random action
            
        step_result = env.step(action)
        
        # Handle Gymnasium (5 values) vs Gym (4 values)
        if len(step_result) == 5:
            obs, reward, terminated, truncated, info = step_result
            done = terminated or truncated
        else:
            obs, reward, done, info = step_result
            
        if isinstance(obs, tuple):
             obs = obs[0]

        # Convert discrete action to actual Nitrogen amount (env-specific logic)
        # N = maxN * action / (n_actions - 1)
        actual_n = 150 * action / 10.0
        
        weeks.append(week_counter)
        actions.append(actual_n)
        week_counter += 1

    # 4. Plot
    plt.figure(figsize=(10, 5))
    plt.bar(weeks, actions, color='green', alpha=0.7, label='Nitrogen Applied')
    
    plt.xlabel('Week of Season')
    plt.ylabel('Nitrogen (kg/ha)')
    plt.title('Agent Decision Making: Nitrogen Application Schedule')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    
    output_path = FIGURES_PATH.joinpath('thesis_policy_example.png')
    plt.savefig(output_path)
    print(f"Saved policy visualization to {output_path}")
    plt.close()

if __name__ == "__main__":
    # 1. Plot Training Curve from 'runs' directory
    plot_training_curve(log_dir="runs")
    
    # 2. Plot Policy (Try to find a model, or default to random)
    # Check for any .zip models in current dir or runs/
    possible_models = glob.glob("*.zip") + glob.glob("runs/*.zip")
    model_to_load = possible_models[0] if possible_models else None
    
    plot_agent_policy(model_path=model_to_load)
