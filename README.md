# CyclesGym Thesis

Research workspace for Pakistan-focused crop-management reinforcement learning experiments built on the CYCLES crop simulator.

This repository contains the thesis codebase, simulation environment adapters, experiment runners, notebooks, dashboard prototype, and final defense presentation assets used while studying RL-based crop planning and fertilization decisions.

## What This Repo Shows

- A Gym/Gymnasium-style interface around the CYCLES crop simulator.
- Fertilization and crop-planning experiment runners.
- Hierarchical and guarded crop-management policy variants.
- Pakistan-specific pricing and crop-calendar utilities.
- Thesis reporting and plotting scripts.
- A React dashboard prototype for exploring thesis outputs.
- Final defense presentation source assets and rendered slides.

## Repository Map

```text
.
|-- cycles/                     # CYCLES simulator binaries and generated/localized input files
|-- cyclesgym/                  # Python package: environments, managers, policies, tests, utilities
|-- experiments/                # Training, inference, baseline, and visualization scripts
|-- notebooks/                  # Small exploratory notebooks for environment setup and training
|-- scripts/                    # Thesis reporting, matrix construction, plotting, and utility scripts
|-- thesis_dashboard/           # React/Vite dashboard prototype
|-- artifacts/
|   `-- final_defence_presentation/  # Defense deck sources, assets, and rendered slide images
|-- environment.yml             # Reproducible Conda environment snapshot
|-- requirements.txt            # Python dependency snapshot
|-- setup.py                    # Editable install for the cyclesgym package
`-- README.md
```

## Current Public Snapshot

This public version is intended as a portfolio and reproducibility snapshot, not a lightweight package distribution.

Large final experiment bundles and local thesis working folders are intentionally ignored by git. Several reporting scripts still reference `artifacts/final_successful_runs/`; those paths are for locally generated or archived evidence packs, not files currently committed to this public checkout.

The most useful committed artifacts for public review are:

- `cyclesgym/` for environment and research-code structure.
- `experiments/` and top-level `run_*.py` files for experiment orchestration.
- `scripts/` for thesis reporting and final matrix utilities.
- `thesis_dashboard/` for the dashboard prototype.
- `artifacts/final_defence_presentation/` for defense visuals and deck-generation assets.

## Installation

The original thesis environment targeted Python 3.8.

Using Conda:

```bash
conda env create -f environment.yml
conda activate cyclesgym
pip install -e .
pip install -e ".[SOLVERS]"
```

Minimal editable install:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

By default, `pip install -e .` may try to install or prepare the CYCLES binary. To skip that post-install step:

```bash
CYCLESGYM_SKIP_CYCLES=1 python -m pip install -e .
```

On Windows PowerShell:

```powershell
$env:CYCLESGYM_SKIP_CYCLES = "1"
python -m pip install -e .
```

## Common Entry Points

```bash
python run_all_experiments.py
python run_all_2.py
python run_hierarchical_guarded_parallel.py
python build_dashboard_data.py
```

Experiment-specific scripts live under:

- `experiments/fertilization/`
- `experiments/crop_planning/`
- `scripts/low_hanging_ablation/`

## Dashboard

The dashboard is a separate React/Vite app:

```bash
cd thesis_dashboard
npm install
npm run dev
```

The dashboard expects public JSON/CSV payloads under `thesis_dashboard/public/data/`. Use `build_dashboard_data.py` after generating or restoring the thesis reporting pack locally.

## Reproducibility Notes

- This repo includes code and selected defense artifacts, but not every generated experiment bundle.
- Runtime outputs should stay in ignored folders such as `runs/`, `wandb/`, and local artifact bundles.
- The CYCLES simulator and some generated inputs can be platform-sensitive.
- Treat the committed environment files as a thesis snapshot, not as a guarantee that every old run can be reproduced on a fresh machine without local artifacts.

## License And Attribution

See [LICENSE](LICENSE). The underlying CYCLES Gym codebase builds on the original `cyclesgym` work by the authors listed in [AUTHORS](AUTHORS), with thesis-specific extensions and experiment/reporting code added for this project.
