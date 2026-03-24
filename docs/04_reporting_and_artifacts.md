# Reporting and Artifacts

## Purpose

This repo has:

1. runtime/debug outputs (`runs/`, `wandb/`)
2. completed frozen final evidence packs (`artifacts/final_successful_runs/`)

## Canonical Completed Packs

- `artifacts/final_successful_runs/final_113/`
- `artifacts/final_successful_runs/final_113/reporting/`
- `artifacts/final_successful_runs/final_42_ablation/`
- `artifacts/final_successful_runs/final_42_ablation/reporting/low_hanging_ablation/`

## Artifact Map

| Path | What it contains | Use |
|---|---|---|
| `runs/experiment_summaries/` | local batch summaries | execution checks |
| `runs/train_logs/` | JSONL runtime logs | debugging |
| `wandb/` | tracked run artifacts | provenance/debugging |
| `artifacts/final_successful_runs/final_113/reporting/` | final matrix run-level/grouped/statistical outputs | primary final matrix citation |
| `artifacts/final_successful_runs/final_42_ablation/reporting/low_hanging_ablation/` | ablation reporting outputs | primary ablation citation |

## Final Reporting Rule

For thesis-final claims, cite reporting outputs from completed frozen packs.

If older extracted LaTeX status tables disagree, treat those tables as older snapshots and use frozen completed packs as canonical.

## Practical Priority

1. final_113 reporting outputs
2. final_42 ablation reporting outputs
3. manifest and replacement maps
4. runtime folders for debugging/provenance detail
