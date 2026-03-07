# Thesis Answer Pack

This folder is a defense-ready answer pack for:

- complete experimentation commands and file entrypoints
- run-time estimates from historical runs
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
python run_all_2.py --dry-run
python run_all_2.py
python run_all_2.py --include-dqn --include-baseline
```
