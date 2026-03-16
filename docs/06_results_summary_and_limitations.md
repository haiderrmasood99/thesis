# Results Summary and Evidence Positioning

This page summarizes the canonical final reporting outputs generated from:

- `artifacts/final_successful_runs/final_113/`
- `artifacts/final_successful_runs/final_113/reporting/`

It replaces the older archived 64-run snapshot as the active public results summary.

## Final Campaign Snapshot

| Metric | Value |
|---|---:|
| manifest rows in canonical final set | 113 |
| completed rows in canonical reporting | 113 |
| recovered replacement rows | 16 |
| corrected guarded hierarchical rerun rows | 12 |
| recovered DQN rerun rows | 4 |
| inferentially eligible repeated groups | 36 |

## Best Repeated Groups

### Fertilization

- headline metric: `deterministic_return`
- strongest repeated group: `A2C | nonadaptive | fixed_weather | years=5000`
- mean deterministic return: `779267.35`
- 95% CI: `[727686.53, 830848.18]`
- main robustness metric: `pak_holdout_return`

### Non-Hierarchical Crop Planning

- headline metric: `eval_det/mean_reward`
- strongest repeated group: `PPO | nonadaptive | fixed_weather`
- mean `eval_det/mean_reward`: `21230.91`
- 95% CI: `[15225.61, 27236.22]`

### Hierarchical Guarded Reruns

- report separately from the non-hierarchical crop-planning leaderboard
- strongest repeated guarded group: `PPO | fixed_weather | guarded_rerun`
- mean deterministic return: `1861223.08`
- 95% CI: `[1512430.79, 2210015.38]`
- provenance note: these are corrected guarded reruns from 14 March 2026, not the original raw hierarchical run regime

## Statistical Summary

- Fertilization shows the clearest factor-level signal.
  - Type II ANOVA indicates strong method and budget effects, with smaller but significant adaptivity and weather effects.
- Non-hierarchical crop planning shows close overlap among the top repeated groups at the current sample size.
- Guarded hierarchical reruns are best interpreted as a separate guarded branch rather than as part of the main crop leaderboard.
- DQN reruns and the baseline row are descriptive only and are excluded from inferential testing.

## Evidence Boundaries

- results remain simulation-based and are not field validated
- irrigation is not implemented as a learned action
- the crop-planning stack remains centered on the working maize-soy configuration
- recovered guarded hierarchical reruns do not include the original thesis-report directories
- some rows in the frozen set are explicit recovered replacements rather than first-pass originals
- missing `vec_normalize` sidecars still appear in the artifact audit for part of the frozen bundle set

## Reporting Rule

For final reporting, cite the files under `artifacts/final_successful_runs/final_113/reporting/`.

Treat the following as secondary or archival context only:

- `runs/experiment_summaries/`
- `Local Files and Folders/final_docs/`
- `Local Files and Folders/Experimentation and Results/`
