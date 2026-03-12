# Thesis Main Working

This workspace is the LaTeX implementation of the NUST thesis for the CyclesGym-PK project.

## Status
- Official NUST template structure has been adapted into a modular multi-file LaTeX project.
- Figures and tables are generated from repo artifacts and official-source-derived data files.
- Chapters 1-5 and 7 are drafted around implemented repo scope.
- Chapter 6 is intentionally factual and provisional until the fresh broad latest-NPK matrix is executed.

## Build
1. Run `powershell -ExecutionPolicy Bypass -File .\build.ps1`
2. The generated PDF and logs are written to `build/`.

## Assets
- `scripts/build_assets.py`: generates figures and tables.
- `scripts/run_smoke_subset.ps1`: launches a small real-run subset for validation.
- `bib/refs.bib`: thesis bibliography.
- `notes/source_catalog.md`: source traceability notes.

## Important boundary
Do not rewrite Chapter 6 as final comparative evidence until the fresh latest-NPK campaign completes and the generated tables are refreshed from completed summary JSON outputs.
