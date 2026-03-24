# Noob's Guide To The Whole Work

## 0) Read This First (One-Minute Version)

This thesis project is an RL-based agricultural simulation workflow built on top of CyclesGym and CYCLES.

For final defense and final thesis claims, the canonical evidence is:

- `artifacts/final_successful_runs/final_113/` (final matrix, 113 runs)
- `artifacts/final_successful_runs/final_42_ablation/` (low-hanging ablation, 42 runs)

Both sets are completed and frozen. Use them for final comparisons.

## 1) What This Project Is Trying To Solve

The project studies how reinforcement learning can optimize agricultural decisions in simulation:

- which crop strategy to choose (planning)
- how much fertilizer to apply over time (fertilization)
- how to combine both decisions (hierarchical setup)

The thesis focuses on a Pakistan-oriented simulation setup (weather/soil/pricing localization) and evidence-driven reporting.

## 2) What Was Built (In Plain Language)

Core implemented pieces:

- Pakistan-adapted simulation defaults (weather/soil/pricing inputs)
- fertilization RL workflow
- crop-planning RL workflow
- hierarchical environment that links planning and fertilization behavior
- NPK-aware reward/reporting signals for explainable outcomes
- reporting pipeline to convert run artifacts into thesis-ready summaries

Supporting engineering:

- experiment runners for matrix-style campaigns
- training/evaluation scripts
- artifact manifests and reporting exports
- thesis LaTeX + defense slide generation support

## 3) Final Evidence Status (Important)

### 3.1 Canonical completed sets

- Final matrix: `113` runs in `final_113`
- Ablation set: `42` runs in `final_42_ablation`

### 3.2 Why old files may disagree

Some older extracted LaTeX status snapshots were generated before final reconciliation and may still show a pending state.

Rule:

- If snapshot text conflicts with frozen final packs, trust frozen final packs.

### 3.3 Where to cite from

Primary reporting paths:

- `artifacts/final_successful_runs/final_113/reporting/`
- `artifacts/final_successful_runs/final_42_ablation/reporting/low_hanging_ablation/`

## 4) Folder Map For Noobs

Top-level areas you will care about most:

- `cycles/`: simulator inputs/binaries and localized resources
- `cyclesgym/`: environment and reward/manager code
- `experiments/`: train/eval entrypoints
- `run_experiments_7_3_2026.py`: matrix orchestration entrypoint
- `artifacts/final_successful_runs/`: frozen final evidence packs
- `docs/`: active project docs used for final narrative
- `Refrence Material/`: proposal/final defense references and thesis LaTeX materials
- `demo/`: farmer-facing local MVP over saved artifacts

## 5) What The 113 And 42 Sets Mean

### 5.1 `final_113`

This is the thesis final matrix evidence set.

- row coverage target: 113
- includes curated originals plus recovered replacements where needed
- includes canonical reporting outputs used by thesis claims

Interpretation:

- this is the main "final comparison" backbone
- run-level and grouped summaries from this set are thesis-grade citation material

### 5.2 `final_42_ablation`

This is focused ablation evidence used to explain design choices and sensitivity.

Interpretation:

- this supports "why this design" arguments
- use it for targeted comparison, not as a replacement for full matrix evidence

## 6) What Worked (Outcome-by-Outcome)

### 6.1 System integration worked

- RL agent -> environment -> simulator -> parser -> reward loop is operational.
- End-to-end training/evaluation workflow produces artifacts and summaries.

What that means:

- the thesis is not only conceptual; it has executable end-to-end implementation.

### 6.2 Localization worked

- Pakistan-oriented weather/soil/pricing context was integrated into the experiment flow.

What that means:

- outcomes are framed for the intended local simulation context, not a generic global placeholder.

### 6.3 NPK-aware reporting worked

- reporting captures nutrient-related details and structured run evidence.

What that means:

- defense can explain not just "reward increased" but what changed in nutrient/cost behavior.

### 6.4 Hierarchical workflow worked

- hierarchical planning + fertilization structure exists and is represented in final artifacts.

What that means:

- contribution goes beyond a single flat policy setup.

### 6.5 Evidence freezing and reporting discipline worked

- final run sets were frozen into canonical folders with reporting outputs.

What that means:

- claims can be tied to stable files, improving reproducibility and auditability.

## 7) What Did Not Work / Still Limited

These are not hidden; they are explicit boundaries:

- evidence is simulation-based (no field validation yet)
- irrigation-as-a-learned-action is outside active final evidence flow
- some crop/scenario extensions (for example deeper rice-focused campaigns) are future work
- broad reruns can be computationally expensive and time-heavy

What that means:

- the thesis can defend implemented simulation contributions strongly
- it should not claim real-world deployment or agronomic field validation

## 8) What The Old Phrase Means

Phrase:

`Fresh 113-job campaign is pending for final comparative chapter`

Correct interpretation now:

- this was true for an older intermediate snapshot
- it is not the final canonical status now
- final canonical status is completed frozen 113 + 42 sets

So when presenting final thesis results, do not keep using that sentence as current status.

## 9) How To Verify Status Yourself (Noob Checklist)

1. Open these folders and confirm they exist:
   - `artifacts/final_successful_runs/final_113/`
   - `artifacts/final_successful_runs/final_42_ablation/`
2. Check these files exist:
   - `final_113/manifest.csv`
   - `final_113/reporting/run_level_metrics.csv`
   - `final_42_ablation/manifest.csv`
3. Use reporting folders as source for tables/claims.
4. If another file says "pending," treat it as older snapshot text unless backed by newer frozen evidence.

## 10) Defense-Safe Claim Pattern

Use this structure in slides and viva answers:

1. "This claim comes from frozen final evidence packs."
2. "Matrix evidence is from 113 completed runs; ablation evidence is from 42 completed runs."
3. "All conclusions are simulation-bounded and reproducible from reporting outputs."

## 11) Beginner Workflow To Reproduce Understanding

1. Read:
   - `docs/README.md`
   - `docs/01_overview_and_scope.md`
   - `docs/04_reporting_and_artifacts.md`
   - `docs/06_results_summary_and_limitations.md`
2. Inspect canonical pack READMEs:
   - `artifacts/final_successful_runs/final_113/README.md`
   - `artifacts/final_successful_runs/final_42_ablation/README.md`
3. Inspect reporting outputs in both packs.
4. Only then open thesis LaTeX/extracted notes for narrative alignment.

## 12) Mistakes Noobs Usually Make

- using raw runtime folders (`runs/`, `wandb/`) as final citation source
- trusting old extracted status text over frozen final packs
- mixing historical context plots with canonical final metrics without labeling
- overstating to field-level applicability

## 13) Quick FAQ

### Is the final campaign completed?

Yes, for final thesis evidence it is completed as frozen packs:

- `final_113` (113)
- `final_42_ablation` (42)

### Is this real-farm validated?

No. It is simulation evidence.

### What should I use in final chapter tables?

Use reporting outputs under canonical frozen packs.

### Can old pending text appear somewhere?

Yes, in older extracted snapshots. Treat those as stale context, not canonical final status.

## 14) Final One-Liner

This work is a completed, simulation-based RL thesis pipeline with frozen final evidence (113 + 42), strong reproducibility discipline, and clearly stated real-world validation limits.
