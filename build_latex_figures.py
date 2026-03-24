import os
import shutil
import glob
from collections import defaultdict

def main():
    base_dir = r"D:\THESIS FINAL EXPERIMENTS\thesis_backup\thesis"
    src1 = os.path.join(base_dir, r"artifacts\final_successful_runs\thesis_reporting_pack\final_113\figures\per_run")
    src2 = os.path.join(base_dir, r"artifacts\final_successful_runs\thesis_reporting_pack\final_42_ablation\figures\per_run")
    dest_dir = os.path.join(base_dir, r"final_experiments_report_antigravity\figures\per_run")
    
    os.makedirs(dest_dir, exist_ok=True)
    
    all_pngs = []
    
    for src in [src1, src2]:
        if not os.path.exists(src):
            print(f"Directory not found: {src}")
            continue
        for f in os.listdir(src):
            if f.endswith('.png'):
                shutil.copy2(os.path.join(src, f), os.path.join(dest_dir, f))
                all_pngs.append(f)
                
    # Group by run
    runs = defaultdict(list)
    for p in all_pngs:
        if "__" in p:
            run_id = p.split("__")[0]
            runs[run_id].append(p)
            
    # Sort runs by index (e.g., 001_, 002_)
    sorted_runs = sorted(runs.keys())
    
    latex_lines = []
    
    # We will split it into sections for 113-run study and 42-run study based on the run names or just create a massive dump.
    latex_lines.append(r"\section{Complete Per-Run Graphs Portfolio}")
    latex_lines.append(r"The following sections present the comprehensive per-run metrics and graphics generated across both the 113-experiment benchmark and the 42-run ablation study. Due to the volume of runs, each run is allocated its own subsection detailing the respective plots.")
    latex_lines.append("")
    
    for run in sorted_runs:
        run_title = run.replace("_", " ").title()
        latex_lines.append(rf"\subsection{{Run: {run_title}}}")
        
        # Sort files to have a consistent order
        plots = sorted(runs[run])
        
        for plot in plots:
            plot_type = plot.split("__")[1].replace(".png", "").replace("_", " ").title()
            # use posix path for latex
            latex_path = f"figures/per_run/{plot}"
            latex_lines.append(r"\begin{figure}[H]")
            latex_lines.append(r"    \centering")
            latex_lines.append(rf"    \includegraphics[width=0.8\textwidth]{{{latex_path}}}")
            latex_lines.append(rf"    \caption{{{run_title} - {plot_type}}}")
            latex_lines.append(r"\end{figure}")
            latex_lines.append("")
            
        latex_lines.append(r"\clearpage")
        
    out_latex_path = os.path.join(base_dir, r"final_experiments_report_antigravity\chapters\05_generated_plots.tex")
    with open(out_latex_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(latex_lines))
        
    print(f"Done! Copied {len(all_pngs)} PNGs and generated {out_latex_path}")

if __name__ == "__main__":
    main()
