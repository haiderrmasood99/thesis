# Thesis Answer Pack

This folder is a defense-ready answer pack for:

- complete experimentation commands and file entrypoints
- run-time estimates from the final March 2026 campaign
- unresolved work and research gaps
- detailed answers to questions `0` to `9`
- contribution roadmap for master's-level work

## Files

1. `00_Flow_Diagrams.md`  
   Overall and detailed Mermaid/UML-style flows.
2. `01_Defense_QA_and_Timelines.md`  
   Direct answers to all requested questions, with command runbooks.

## Quick Start (From Scratch)

```powershell
conda env create -f environment.yml
conda activate cyclesgym
pip install -e .
pip install -e '.[SOLVERS]'
python install_cycles.py
```

### Set a Separate W&B Project (Optional, Recommended)

```powershell
$env:WANDB_ENTITY = "your_wandb_entity"
$env:WANDB_PROJECT_FERTILIZATION = "thesis_fertilization_v2"
$env:WANDB_PROJECT_CROP_PLANNING = "thesis_crop_planning_v2"
```

Then run experiments:

```powershell
python run_experiments_7_3_2026.py --dry-run
python run_experiments_7_3_2026.py
# optional split execution / rerun helpers used in the March 2026 campaign
python 10_3_2026_heira_exp.py
python 10_3_2026_experiments.py --start-index 75
```
