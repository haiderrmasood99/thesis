# Thesis Main Working

This workspace is the LaTeX implementation of the NUST thesis for the CyclesGym-PK project.

## Status

- The thesis now builds from the canonical final reporting outputs under `artifacts/final_successful_runs/final_113/reporting/`.
- Chapter 6 is the completed final results chapter, not a provisional placeholder.
- Figures and tables are generated from frozen repo artifacts and official-source-derived data files.

## Build

1. Run `python scripts\build_final_reports.py` from the repo root.
2. Run `python "Local Files and Folders\Thesis Main Working\scripts\build_assets.py"`.
3. Run `powershell -ExecutionPolicy Bypass -File "Local Files and Folders\Thesis Main Working\build.ps1"`.

The generated PDF and logs are written to `build/`.

## Assets

- `scripts/build_assets.py`: generates thesis figures and tables from canonical reporting outputs.
- `bib/refs.bib`: thesis bibliography.
- `notes/source_catalog.md`: source traceability notes.

## Boundary

Do not point the thesis back to provisional `runs/experiment_summaries/` outputs when `final_113/reporting/` already contains the canonical final dataset.
