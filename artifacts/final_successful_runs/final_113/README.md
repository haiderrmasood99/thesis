# Final Correct 113 Runs

This folder is the frozen canonical final evidence set assembled from the curated archive plus the recovered reruns.

- total bundles: `113`
- copied from existing curated bundles: `97`
- hierarchical rerun replacements: `12`
- DQN rerun replacements: `4`
- bundles with `model.zip`: `112`
- bundles with checkpoint directories beyond `model.zip`: `96`
- bundles with `vec_normalize` state: `72`
- bundles with hierarchical report directories: `0`

## Layout

- `bundles/`: one folder per final matrix row
- `manifest.csv`: full inventory for the corrected 113 bundles
- `replacement_map.csv`: which rows were swapped to recovered reruns
- `reporting/`: canonical run-level, grouped, statistical, and audit outputs used by the thesis and active docs

## Notes

- The recovered W&B export did not include the repo's original `runs/experiment_summaries/*.json` files for the reruns, so those summary JSON files were reconstructed from the recovered export metadata.
- The recovered rerun exports currently include `model.zip` but not the old `models/.../best_model.zip` checkpoint directories.
- The recovered fertilization DQN reruns do not currently include `vec_normalize_*.pkl` files in the downloaded backup.
- The recovered hierarchical rerun project does not currently include the thesis report directories in the downloaded backup.
- The baseline-only row remains included without a model checkpoint by design.
- replacement rows recorded: `16`

## Reporting Rule

For final reporting, use the files under `reporting/`. This directory is the active source of truth for the final thesis narrative and release-ready documentation.
