# Plan and Feasibility

## User Goal Interpreted
You asked for a thesis-ready story backed by run evidence, showing how CYCLES Gym configurations perform, how farmers benefit, and what to build next for a usable interface.

## Execution Plan Used
1. Extract experiment intent from runner scripts.
2. Audit actual executions from `wandb` run folders and `runs/train_logs`.
3. Build clean, deduplicated result tables by configuration.
4. Separate strong claims (supported) from weak claims (not yet supported).
5. Convert findings into a narrative suitable for thesis chapters and future productization.

## What Is Possible Now (Evidence-Backed)
- You can claim comparative performance trends across algorithm, adaptation mode, weather mode, and selected training budgets.
- You can claim that Pakistan weather/soil files are part of the training/evaluation setup.
- You can present concrete best-performing observed configurations for:
  - Fertilization policy learning
  - Crop planning policy learning
- You can report operational reliability risks based on repeated traceback signatures.
- You can define a practical MVP UI roadmap grounded in existing model outputs.

## What Is Not Fully Possible Yet
- You cannot claim full `run_all_2` matrix completion: only `34/96` planned configurations are evidenced as successful.
- You cannot claim strong cross-seed stability for crop planning: available successful runs are effectively seed-limited.
- You cannot provide robust baseline-vs-RL deltas from current logs because baseline runs do not include complete comparable metrics in summary files.
- You cannot claim real-world field ROI from these logs alone; results are simulation-based and require pilot validation.

## Practical Thesis Framing Constraint
Use phrasing such as:
- "Observed best configuration under available experiments"
- "Evidence suggests"
- "Requires full-matrix rerun for final statistical confirmation"

This keeps claims defensible while still telling a strong story.
