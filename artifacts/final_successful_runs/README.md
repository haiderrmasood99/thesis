# Final Successful Runs

This folder contains the curated artifact bundles promoted out of `Local Files and Folders/`.

- successful matrix bundles promoted: `109`
- bundles with checkpoint files moved: `108`
- bundles with `vec_normalize` files moved: `72`
- bundles with hierarchical report folders moved: `12`
- planned matrix rows left out: `4`

## Layout

- `bundles/`: one folder per successful final-matrix run
- `manifest.csv`: promoted bundle inventory
- `missing_runs.csv`: planned rows left out of promotion and why

## Notes

- The baseline-only run is included as a successful bundle even though it has no model checkpoint by design.
- Crop-planning bundles do not include `vec_normalize` files because those files were not produced for those runs in the archive.
- The four left-out rows are the failed DQN ablation slots from the actual matrix completion summary.
