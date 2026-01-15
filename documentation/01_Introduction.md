# 01. Introduction to CyclesGym

Welcome to **CyclesGym**! 🚜🤖

If you are reading this, you are probably a data scientist, ML engineer, or a fresh graduate looking to apply **Reinforcement Learning (RL)** to the world of **Agriculture**. This repository is your bridge between the abstract world of AI algorithms and the biological reality of growing crops.

## 🎯 What is this Repo?

**CyclesGym** is a Python library that wraps an advanced crop simulation model called **Cycles** into a standard **OpenAI Gym (now Gymnasium)** interface.

*   **Cycles (The Simulator)**: Think of it as a highly detailed "SimCity" for corn, soybeans, and soil. It simulates how plants grow day by day based on weather, soil, and potential farming actions.
*   **Gym (The Interface)**: The standard way AI agents talk to environments. If you've used `CartPole` or `LunarLander`, you know the drill: `obs, reward, done, info = env.step(action)`.

**The Goal**: We want to train AI agents to manage farms more efficiently—maximizing yield (food) while minimizing environmental impact (nitrogen leaching) and accumulating costs.

## 🛠️ Prerequisites

To succeed with this repo, you should be comfortable with:
1.  **Python**: Intermediate level (classes, inheritance, file I/O).
2.  **Basic ML/RL**: Understanding of *Agent*, *Environment*, *State*, *Action*, and *Reward*.
3.  **Command Line**: Basic navigation.

You **DO NOT** need to be an expert in:
*   Agriculture (we will explain the basics).
*   Soil Physics (the simulator handles this).

## 🚀 Quick Start

### Installation

We recommend using **Anaconda** to keep your dependencies clean.

1.  **Create an Environment**:
    ```bash
    conda create -yn cyclesgym python=3.9
    conda activate cyclesgym
    ```

2.  **Clone the Repo**:
    ```bash
    git clone https://github.com/kora-labs/cyclesgym.git
    cd cyclesgym
    ```

3.  **Install**:
    ```bash
    pip install -e .
    ```

### Your First Simulation

Here is a simple script to verify everything is working. This runs a "Corn" environment where we take random actions (random amount of fertilizer).

```python
import gym
import cyclesgym
import numpy as np

# 1. Create the environment
# 'Corn-v1' is a pre-registered environment for growing Corn
env = gym.make('Corn-v1')

# 2. Reset the environment to start a new "episode" (a growing season)
# obs contains weather and current crop status
obs = env.reset() 

done = False
total_reward = 0

print("Starting Simulation...")

while not done:
    # 3. Take a random action
    # Actions usually represent amount of Nitrogen fertilizer to apply
    action = env.action_space.sample()
    
    # 4. Step the environment
    # The 'step' function runs the simulator forward (usually 1 week)
    obs, reward, done, info = env.step(action)
    
    total_reward += reward

print(f"Simulation Finished! Total Reward: {total_reward}")
env.close()
```

---
**Next Step**: Go to `02_Domain_Concepts.md` to understand what exactly is happening inside that "Black Box" of a simulator.
