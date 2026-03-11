# 08. Gaps and Future Work

This section identifies what to improve next now that the 113-case thesis matrix has been completed.

## Priority Gaps

| Priority | Gap | Why It Matters | Suggested Work |
|---|---|---|---|
| P0 | Hierarchical controller failed across all 12 runs | Blocks any thesis claim about unified yearly-plus-weekly control | Keep it as a failed ablation in the thesis, then rerun only after enforcing valid crop windows, seasonal fertilizer gating, and annual nutrient budgets |
| P0 | No formal statistical testing on the completed matrix | Descriptive means are useful, but defense questions will push on significance | Add confidence intervals, effect sizes, and hypothesis tests across seeds |
| P0 | Crop-planning baseline comparability is still missing | Hard to quantify uplift versus a heuristic scheduler | Add crop-planning baseline policies and log the same summary metrics as RL runs |
| P1 | DQN is only a single-seed ablation and needed reruns | Not enough evidence to recommend DQN | Stabilize the DQN path and rerun more than seed `0` |
| P1 | Simplified economics (mostly crop value minus nutrient cost) | Can under-represent practical farm decision constraints | Add labor, irrigation, penalty terms, and sensitivity analysis |
| P1 | Limited resource controls (weekly nutrients and yearly crop choice only) | Thesis can be challenged as narrow allocation scope | Add irrigation and richer nutrient/resource actions |
| P2 | No field or expert-in-the-loop validation yet | Simulation-only claims remain externally challengeable | Run pilot validation with agronomist-reviewed scenarios |

## Code-Level Technical Debt Signals

1. crop-planning operation handling still has simplifications around default operations
2. DQN relies on wrapper/evaluation paths that were the only rerun-sensitive part of the matrix
3. hierarchical runs are very expensive and the March failure pattern points to two concrete issues: nutrient-cost blow-up and incomplete crop-calendar coverage
4. reporting is good enough for descriptive analysis but not yet for full statistical reporting

## Agricultural Extension Opportunities

1. Multi-nutrient optimization:
   extend fertilizer controls beyond the current NPK discretization to richer resource tradeoffs.
2. Water management:
   expose irrigation as a decision variable with cost and water-risk terms.
3. Sustainability-aware objectives:
   convert leaching/emission constraints into explicit penalties or constrained-RL objectives.
4. Region transfer:
   repeat the workflow for additional Pakistan agro-climatic zones.

## Defense-Oriented Action Plan

### Next 2 Weeks

1. generate final seed-aggregated tables and plots from the completed matrix
2. add confidence intervals, effect sizes, and significance tests
3. write an explicit negative-result subsection for the hierarchical branch and the DQN reruns

### Next 1-2 Months

1. redesign the hierarchical formulation and rerun its 12-case matrix
2. add crop-planning baselines and richer economics
3. package the best non-hierarchical policies behind an inference API with guardrails

### Post-Thesis

1. pilot validation with domain experts and field constraints
2. extend to irrigation and broader resource-allocation actions
3. integrate richer risk and market models
