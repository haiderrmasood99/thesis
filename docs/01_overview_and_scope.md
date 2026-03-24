# Overview and Scope

## Project Goal

Build a Pakistan-adapted, cost-aware reinforcement learning workflow on top of CyclesGym and present finalized thesis evidence with reproducible reporting.

## Completed Final Evidence Scope

The project includes two completed frozen evidence sets:

- final matrix set: `113` runs
- low-hanging ablation set: `42` runs

Both are preserved under `artifacts/final_successful_runs/`.

## What The Repo Actively Supports

- fertilization training/evaluation workflows
- crop-planning and hierarchical workflows
- consolidated matrix orchestration
- standardized reporting and artifact audits
- thesis-facing documentation and defense materials

## Scope Boundaries (Still True)

- evidence remains simulation-based
- no field validation claim
- irrigation-as-learned-action remains outside active completed evidence

## Layout

| Path | Purpose |
|---|---|
| `cycles/` | simulator binaries and localized inputs |
| `cyclesgym/` | env/reward/manager/util code |
| `experiments/` | train/eval scripts |
| `artifacts/final_successful_runs/` | completed frozen final evidence |
| `docs/` | active documentation |

## Evidence Priority

For final claims and defense tables, cite completed frozen packs first, then supporting runtime/provenance artifacts.
