# Model Management

## Where Saved Models Live

### When W&B Tracking Is Enabled

Checkpoints are written inside the local W&B run folder:

- `wandb/run-.../files/model.zip`
- `wandb/run-.../files/models/.../best_model.zip`

This is the default tracked workflow.

### When `--without-tracking` Is Used

The code falls back to a local offline run folder:

- `runs/offline/<run-id>/models/...`

This keeps the run usable even without a W&B session.

## Other Required Artifacts

A saved model is not enough by itself.
Keep the following together:

- the checkpoint file
- the matching `runs/vec_normalize_*.pkl`
- the corresponding summary JSON
- the runner command or config
- the seed and weather mode

## Recommended Promotion Workflow

Raw run folders are noisy.
This repo now defines a curated promotion target at:

```text
artifacts/final_successful_runs/bundles/
```

The corrected frozen final matrix set now also has a dedicated output path:

```text
artifacts/final_successful_runs/final_113/bundles/
```

For any model you want to preserve long-term, promote it into one bundle per successful run:

```text
artifacts/final_successful_runs/bundles/
  001_fertilization_ppo_adaptive_fixed_weather_years_1000_seed_0/
    bundle_metadata.json
    models/
    runtime/
    summary/
    wandb/
```

The promotion paths are code-defined in `cyclesgym/utils/paths.py`.
Use:

- `scripts/promote_final_matrix_runs.py` for the first-pass curated archive
- `scripts/build_final_113_runs.py` to assemble the corrected final 113 bundle set from the curated archive plus recovered reruns

## Naming Convention

Use names that encode the minimum decision context:

```text
<date>_<domain>_<method>_<seed>_<weather>_<runid>
```

Example:

```text
2026-03-14_fertilization_ppo_seed1_random_zyo19dh1
```

## Tracking: W&B Versus Local Logs

W&B is not the only experiment trace.
The repo also writes local artifacts:

- `runs/train_logs/*.jsonl`: step and rollout logs
- `runs/experiment_summaries/*.csv` and `*.json`: reporting layer
- `runs/thesis_reports/`: hierarchical-specific details
- `runs/vec_normalize_*.pkl`: normalization state

## Retention Policy

- keep every summary CSV and summary JSON until the reporting cycle is finished
- keep only promoted checkpoints long-term
- treat raw `wandb/` and `runs/offline/` folders as working storage, not curated archives
- never cite a model in docs unless you can point to its checkpoint, normalization file, and summary JSON together

## Push Hygiene

The public repo should contain:

- source code
- docs
- lightweight static figures

The public repo should not contain:

- raw training dumps
- raw W&B run trees
- large local log folders
- temporary experiment copies
