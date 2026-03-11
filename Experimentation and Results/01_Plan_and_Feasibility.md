# Plan and Feasibility

## User Goal Interpreted
You asked for a thesis-ready closeout that reflects the completed March 7-11, 2026 experiment campaign, updates the handoff/report docs, and turns the final 113-case matrix into defensible conclusions.

## Execution Plan Used
1. Compare the March 11 W&B export against the matrix generator in `run_experiments_7_3_2026.py`.
2. Deduplicate reruns and verify whether any planned configs are still missing.
3. Aggregate final results by domain, algorithm, adaptation mode, weather mode, and budget.
4. Update the thesis narrative, handoff notes, and defense pack with only the claims supported by the finished matrix.

## What Is Possible Now (Evidence-Backed)
- You can claim full completion of the intended `113`-configuration thesis matrix.
- You can claim that the March 11 export contains `113/113` unique finished configs, with `0` missing and `0` extra when compared against the generator.
- You can report seed-aggregated fertilization conclusions across PPO/A2C fixed/random weather and `1000/3000/5000`-year budgets.
- You can report fertilization baseline-vs-RL evidence: the best baseline return is `750,198.06`, and `11/74` fertilization RL runs exceeded it.
- You can report seed-aggregated crop-planning conclusions for PPO and A2C, plus the single-seed DQN ablations.
- You can report a completed hierarchical failed ablation: all `12` hierarchical runs finished, but all produced strongly negative rewards and should be excluded from the main crop benchmark tables.

## What Is Not Fully Possible Yet
- You still cannot claim field-level ROI or agronomic external validity; the evidence is simulator-based.
- You cannot claim strong DQN crop-planning robustness because the DQN branch is only a seed-0 ablation.
- You cannot claim formal statistical significance until confidence intervals, effect sizes, or tests are added.
- You cannot claim the current hierarchical controller is deployment-ready; the March 11, 2026 analysis shows nutrient-cost blow-up and incomplete calendar coverage in that branch.

## Practical Thesis Framing Constraint
Use phrasing such as:
- "completed 113-case matrix within the current simulator and reward design"
- "best mean over the available three-seed groups"
- "best single-run result"
- "hierarchical branch is a failed ablation documented by cost blow-up and incomplete crop-calendar coverage"
- "field validation remains future work"
