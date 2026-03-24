import os
import pandas as pd
import matplotlib.pyplot as plt

# Configuration
csv_path = r"D:\THESIS FINAL EXPERIMENTS\thesis_backup\thesis\artifacts\final_successful_runs\thesis_reporting_pack\final_42_ablation\tables\per_run\013_p2_a2c_fixed_weather_seed0_blockpen0__weekly_npk_log.csv"
output_path = r"D:\THESIS FINAL EXPERIMENTS\thesis_backup\thesis\final_condensed_report\figures\per_run\013_p2_a2c_fixed_weather_seed0_blockpen0__weekly_npk_behavior_HIGHRES.png"

PLOT_COLORS = {
    "n": "#1d4ed8",
    "p": "#ea580c",
    "k": "#16a34a",
    "blocked": "#b91c1c",
}

print("Loading data...")
df = pd.read_csv(csv_path)

# Convert days (num_timesteps) to weeks
df["week"] = df["num_timesteps"] / 7.0

# Plotting at extreme high resolution
print("Generating high-res plot...")
fig, ax = plt.subplots(figsize=(24, 10), dpi=300)

for col, name, color in [("n_kg", "Nitrogen (N)", PLOT_COLORS["n"]), 
                         ("p_kg", "Phosphorus (P)", PLOT_COLORS["p"]), 
                         ("k_kg", "Potassium (K)", PLOT_COLORS["k"])]:
    if col in df.columns:
        ax.plot(df["week"], df[col], linewidth=1.5, label=name, color=color, alpha=0.9)

if "blocked_npk_kg" in df.columns:
    ax.plot(df["week"], df["blocked_npk_kg"], linewidth=1.5, label="Blocked Actions (Penalty)", color=PLOT_COLORS["blocked"], alpha=0.9)

# Formatting
ax.set_title("013_p2_a2c_fixed_weather_seed0_blockpen0 - High Resolution Weekly Behavior", fontsize=20, pad=20)
ax.set_xlabel("Time (Weeks across 1000-Year Simulation)", fontsize=16)
ax.set_ylabel("Applied amount / Blocked attempts (kg)", fontsize=16)

# Add more ticks for the X scale (every 500 weeks)
max_week = int(df["week"].max())
ax.set_xticks(range(0, max_week + 1, max(1, max_week // 30)))
ax.tick_params(axis='x', rotation=45, labelsize=10)
ax.tick_params(axis='y', labelsize=12)

ax.grid(alpha=0.3, color='gray', linestyle='--')
ax.legend(loc="upper right", fontsize=14)

# Save
plt.tight_layout()
fig.savefig(output_path)
print(f"Successfully saved high-res plot to:\n{output_path}")
