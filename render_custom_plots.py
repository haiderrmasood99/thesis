import os
import pandas as pd
import matplotlib.pyplot as plt

# Configuration
csv_path = r"D:\THESIS FINAL EXPERIMENTS\thesis_backup\thesis\artifacts\final_successful_runs\thesis_reporting_pack\final_42_ablation\tables\per_run\013_p2_a2c_fixed_weather_seed0_blockpen0__weekly_npk_log.csv"
output_path_split = r"D:\THESIS FINAL EXPERIMENTS\thesis_backup\thesis\final_condensed_report\figures\per_run\013_p2_a2c_fixed_weather_seed0_blockpen0__weekly_npk_behavior_SPLIT.png"
output_path_zoomed = r"D:\THESIS FINAL EXPERIMENTS\thesis_backup\thesis\final_condensed_report\figures\per_run\013_p2_a2c_fixed_weather_seed0_blockpen0__weekly_npk_behavior_ZOOMED.png"

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

# ---------------------------------------------------------
# GRAPH 1: SPLIT PANELS (All 1000 years, but separated so they don't overlap)
# ---------------------------------------------------------
print("Generating SPLIT plot...")
fig, axes = plt.subplots(4, 1, figsize=(24, 14), dpi=300, sharex=True)
fig.suptitle("A2C Behavior: Split Variables (1000 Years)", fontsize=22, y=0.96)

plot_data = [
    ("n_kg", "Nitrogen (N) kg/ha", PLOT_COLORS["n"]),
    ("p_kg", "Phosphorus (P) kg/ha", PLOT_COLORS["p"]),
    ("k_kg", "Potassium (K) kg/ha", PLOT_COLORS["k"]),
    ("blocked_npk_kg", "Blocked Attempts (kg)", PLOT_COLORS["blocked"])
]

for i, (col, name, color) in enumerate(plot_data):
    if col in df.columns:
        axes[i].plot(df["week"], df[col], linewidth=1.2, color=color, alpha=0.9)
    axes[i].set_ylabel(name, fontsize=14, color=color, fontweight='bold')
    axes[i].grid(alpha=0.3, linestyle='--')
    axes[i].tick_params(axis='y', labelsize=12)

axes[3].set_xlabel("Time (Weeks across 1000 Years)", fontsize=16)

max_week = int(df["week"].max())
axes[3].set_xticks(range(0, max_week + 1, max(1, max_week // 30)))
axes[3].tick_params(axis='x', rotation=45, labelsize=12)

plt.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(output_path_split)
plt.close(fig)

# ---------------------------------------------------------
# GRAPH 2: ZOOMED IN SCATTER PLOT (First 5 Years Only)
# ---------------------------------------------------------
print("Generating ZOOMED plot...")
df_zoomed = df[df["week"] <= (5 * 52)].copy()  # First 5 years (260 weeks)

fig, axes = plt.subplots(4, 1, figsize=(24, 14), dpi=300, sharex=True)
fig.suptitle("A2C Behavior: Zoomed to First 5 Years (Scatter Format)", fontsize=22, y=0.96)

for i, (col, name, color) in enumerate(plot_data):
    if col in df_zoomed.columns:
        axes[i].scatter(df_zoomed["week"], df_zoomed[col], color=color, alpha=0.9, s=30)
        # also draw a faint line connecting them
        axes[i].plot(df_zoomed["week"], df_zoomed[col], color=color, alpha=0.3, linewidth=1)
    
    axes[i].set_ylabel(name, fontsize=14, color=color, fontweight='bold')
    axes[i].grid(alpha=0.5, linestyle='--')
    axes[i].tick_params(axis='y', labelsize=12)

axes[3].set_xlabel("Time (Weeks 0 to 260)", fontsize=16)

# Marks every 10 weeks
max_zoom_week = int(df_zoomed["week"].max())
if max_zoom_week == 0:
    max_zoom_week = 260
axes[3].set_xticks(range(0, max_zoom_week + 10, 10))
axes[3].tick_params(axis='x', rotation=45, labelsize=12)

plt.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(output_path_zoomed)
plt.close(fig)

print("Successfully saved alternative plots!")
