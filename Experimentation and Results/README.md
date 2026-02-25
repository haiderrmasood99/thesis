# Experimentation and Results

## Scope
This folder documents experiment evidence for the thesis topic:

"Optimizing Agricultural Resource Allocation through Reinforcement Learning: A Cost-Driven Approach to Crop Efficiency Enhancement."

The audit covers runs executed between February 23, 2026 and February 25, 2026 using:
- `master_runner_run_all.2.py`
- `run_all_experiments.py`
- `run_all_2.py`

## What Is Included
- `01_Plan_and_Feasibility.md`: What is possible to claim now vs what is not yet defensible.
- `02_Experiment_Matrix_and_Execution_Audit.md`: Runner intent, execution coverage, and failure audit.
- `03_Results_and_Thesis_Story.md`: Quantitative findings and thesis story with X/Y/Z configuration framing.
- `04_UI_Roadmap.md`: Practical next-step UI plan for end-user adoption.
- `artifacts/`: CSV evidence extracted from logs and `wandb` metadata.

## Quick Findings
- Total `wandb` run folders audited: `64`
- Successful runs with summary: `44`
- Failed runs with traceback: `16`
- Runs without summary metadata: `4`
- `run_all_2` planned matrix (dry-run evidence): `96` configs
- `run_all_2` configs observed and successful in logs: `34`

## Data Provenance
Pakistan-based inputs are explicitly wired in training code and configs:
- Weather file: `cycles/input/Pakistan_Site_final.weather`
- Soil file: `cycles/input/Pakistan_Soil_final.soil`
- Fertilization weather window in code: 2005-2019, with training sampling through 2018 and holdout evaluation logging via `pak_holdout_return`.
