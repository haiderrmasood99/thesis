import os
import shutil

base_dir = r"D:\THESIS FINAL EXPERIMENTS\thesis_backup\thesis"
src_chapters = os.path.join(base_dir, r"final_experiments_report_antigravity\chapters")
dest_chapters = os.path.join(base_dir, r"final_condensed_report\chapters")

os.makedirs(dest_chapters, exist_ok=True)

mapping = {
    "01_introduction.tex": "01_introduction.tex",
    "02_methods.tex": "02_methodology.tex",
    "03_113_run_study.tex": "03_baseline_evaluations.tex",
    "04_42_run_ablation_study.tex": "04_ablation_dynamics.tex",
    "06_conclusion.tex": "06_conclusion.tex"
}

for src, dest in mapping.items():
    src_path = os.path.join(src_chapters, src)
    if os.path.exists(src_path):
        shutil.copy2(src_path, os.path.join(dest_chapters, dest))
        print(f"Copied {src}")

print("Done copying base chapters.")
