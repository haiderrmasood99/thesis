# Experimentation and Results

Status: secondary reference archive. The active final-report surfaces are now:

- `docs/`
- `artifacts/final_successful_runs/final_113/reporting/`
- `Local Files and Folders/Thesis Main Working/`

## Scope
This folder documents the finalized March 7-11, 2026 thesis campaign for:

"Optimizing Agricultural Resource Allocation through Reinforcement Learning: A Cost-Driven Approach to Crop Efficiency Enhancement."

The matrix is defined by `run_experiments_7_3_2026.py` and the final evidence export is:
- `run_experiments_7_3_2026_RUNS/wandb_export_2026-03-11T01_53_38.382+05_00.csv`

Supporting execution scripts used in this campaign:
- `10_3_2026_experiments.py`
- `10_3_2026_heira_exp.py`

## What Is Included
- `01_Plan_and_Feasibility.md`: What is now claimable from the completed matrix and what still remains out of scope.
- `02_Experiment_Matrix_and_Execution_Audit.md`: Matrix definition, completion proof, and rerun audit.
- `03_Results_and_Thesis_Story.md`: Final quantitative findings and thesis story with X/Y/Z framing.
- `04_UI_Roadmap.md`: Practical next-step UI plan for end-user adoption.
- `artifacts/`: CSV evidence extracted from logs and `wandb` metadata.

## Quick Findings
- Planned matrix: `113` configs
- Finished unique configs: `113/113`
- Total attempts recorded in export: `117`
- Initial failed attempts: `4`, all rerun successfully
- Finished by domain: `75` fertilization, `26` crop planning, `12` hierarchical failed-ablation runs
- Main conclusion: PPO is strongest overall for fertilization; crop planning is competitive between PPO and A2C; the hierarchical branch is excluded from main comparisons and reported as a failed ablation caused by nutrient-cost blow-up and incomplete crop-calendar coverage

## Data Provenance
Pakistan-based inputs are explicitly wired in training code and configs:
- Weather file: `cycles/input/Pakistan_Site_final.weather`
- Soil file: `cycles/input/Pakistan_Soil_final.soil`
- Fertilization economics profile: `pakistan_baseline`
- Fertilization reporting includes holdout evaluation via `pak_holdout_return`
