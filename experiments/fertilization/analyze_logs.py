import numpy as np
import glob
import os

def analyze_latest_run():
    # Find all evaluation files from wandb runs
    search_pattern = "wandb/run-*/files/models/eval_test_det/evaluations.npz"
    files = glob.glob(search_pattern)
    
    if not files:
        print("No evaluation logs found. Make sure you have completed at least one evaluation phase during training.")
        return

    # Get the latest modified file
    latest_file = max(files, key=os.path.getmtime)
    print(f"==== Local Training Diagnostic ====")
    print(f"Analyzing log file: {latest_file}\n")

    # Load the evaluation data
    data = np.load(latest_file)
    timesteps = data['timesteps']
    results = data['results']
    
    if len(results) == 0:
        print("Log file is empty. Evaluation did not complete.")
        return

    # Calculate mean reward per evaluation step
    mean_rewards = results.mean(axis=1)
    
    # 1. Basic Stats
    max_reward = np.max(mean_rewards)
    max_step_idx = np.argmax(mean_rewards)
    max_timestep = timesteps[max_step_idx]
    final_reward = mean_rewards[-1]
    
    print("--- 1. Reward Summary ---")
    print(f"Maximum Eval Reward: {max_reward:.2f} (achieved at step {max_timestep})")
    print(f"Final Eval Reward:   {final_reward:.2f} (at step {timesteps[-1]})\n")

    # 2. Stability / Overfitting Check
    print("--- 2. Stability Diagnosis ---")
    drop_percentage = ((max_reward - final_reward) / abs(max_reward)) * 100 if max_reward != 0 else 0
    
    if drop_percentage > 10:
        print(f"WARNING: Your eval reward dropped by {drop_percentage:.1f}% from its peak at the end of training.")
        print("   This is a strong sign of overfitting to the training environment or training instability.")
        print("   -> Recommendation 1: Stop training early. We have updated your script to automatically save the 'best' model now!")
        print("   -> Recommendation 2: Try increasing the entropy coefficient slightly (e.g., run with `--ent-coef 0.01`) to encourage more exploration.")
    elif drop_percentage < 0:
        print("EXCELLENT: Your final reward is the best reward! The agent was continually improving.")
    else:
        print(f"STABLE: Your eval reward fluctuated by only {drop_percentage:.1f}% from its peak. Training appears stable.")

    # 3. Quick Check for "Collapse"
    if len(mean_rewards) > 3:
        last_three_avg = np.mean(mean_rewards[-3:])
        first_three_avg = np.mean(mean_rewards[:3])
        if last_three_avg < first_three_avg:
             print("\nCRITICAL: The agent ended up worse than when it started. The policy likely collapsed.")
             print("   -> Check if the learning rate is too high, or if `--ent-coef` is needed.")
             
    print("\n===================================")
    print("Check 'best_eval_test_det' in the models directory to use the best performing agent.")

if __name__ == "__main__":
    analyze_latest_run()
