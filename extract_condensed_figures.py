import os
import shutil

base_dir = r"D:\THESIS FINAL EXPERIMENTS\thesis_backup\thesis"
src_figures = os.path.join(base_dir, r"final_experiments_report_antigravity\figures")
dest_figures = os.path.join(base_dir, r"final_condensed_report\figures")

os.makedirs(dest_figures, exist_ok=True)
os.makedirs(os.path.join(dest_figures, "per_run"), exist_ok=True)

target_files = [
    # General Comparisons
    "final_113__grouped_comparison.png",
    "final_113__leaderboard_primary_metric.png",
    "final_113__runtime_comparison.png",
    "final_113__uplift_vs_baseline.png",
    "final_42_ablation__point1_entropy_primary_metric.png",
    "final_42_ablation__point2_primary_comparison.png",
    "final_42_ablation__point2_thesis_compliance.png",
    "final_42_ablation__point3_cost_weight_paired_deltas.png",
    "final_42_ablation__point3_cost_weight_primary_metric.png",
]

target_per_run_files = [
    "001_p1_ppo_adaptive_fixed_weather_seed0_ent0__diagnostics_panel.png",
    "013_p2_a2c_fixed_weather_seed0_blockpen0__checkpoint_eval_curves.png",
    "013_p2_a2c_fixed_weather_seed0_blockpen0__weekly_npk_behavior.png",
    "013_p2_a2c_fixed_weather_seed0_blockpen0__crop_decision_timeline.png",
    "003_p1_ppo_adaptive_random_weather_seed0_ent0__episode_length_vs_global_step.png",
    "028_p3_ppo_adaptive_random_weather_seed0_costw0_8__weekly_npk_behavior.png",
    "001_fertilization_ppo_adaptive_fixed_weather_years_1000_seed_0__diagnostics_panel.png"
]

count = 0
for f in target_files:
    src = os.path.join(src_figures, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(dest_figures, f))
        count += 1
    else:
        print(f"Missing: {src}")

for f in target_per_run_files:
    src = os.path.join(src_figures, "per_run", f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(dest_figures, "per_run", f))
        count += 1
    else:
        print(f"Missing: {src}")

print(f"Successfully migrated {count} representative plots to condensed report.")
