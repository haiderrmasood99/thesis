# Model Management

## Where Models Are Saved

### With W&B tracking

- `wandb/run-.../files/model.zip`
- `wandb/run-.../files/models/.../best_model.zip`

### With `--without-tracking`

- `runs/offline/<run-id>/models/...`

## Minimum Bundle Needed For Any Defensible Result

A model checkpoint must be paired with:

- matching normalization stats (`runs/vec_normalize_*.pkl` if used)
- summary JSON/CSV evidence
- command/config details
- seed and weather mode
- timestamped run identity

## Promotion Rule

Do not keep only raw run folders as long-term evidence. Promote meaningful runs into structured artifact folders with metadata and summaries.

## Naming Convention

Use names that encode context:

```text
<date>_<domain>_<method>_<seed>_<weather>_<runid>
```

Example:

```text
2026-03-14_fertilization_ppo_seed1_random_zyo19dh1
```

## Thesis-Evidence Boundary

For current thesis writing, model files alone are insufficient. Claims must reference both model artifacts and corresponding completed summary outputs.

## Retention Policy

Keep:

- code
- docs
- curated promoted artifacts with metadata

Avoid treating raw run dumps as canonical long-term evidence.
