# 08. Gaps and Future Work

This section identifies what to improve next if the goal is a stronger thesis defense and a more deployment-ready system.

## Priority Gaps

| Priority | Gap | Why It Matters | Suggested Work |
|---|---|---|---|
| P0 | Incomplete experiment matrix coverage | Limits strength of "best configuration" claims | Complete full `run_all_2` matrix and regenerate summary tables |
| P0 | Limited multi-seed robustness for crop planning | Weak confidence intervals and reproducibility | Run >=3 seeds per key crop-planning configuration |
| P0 | Baseline comparability not fully standardized | Hard to quantify RL uplift cleanly | Log identical metrics for RL and baseline policies |
| P1 | Simplified economics (mostly crop value minus N cost) | Can under-represent practical farm decision constraints | Add labor/input/irrigation/penalty terms and sensitivity analysis |
| P1 | Limited resource controls (N and crop choice only) | Thesis can be challenged as narrow allocation scope | Add irrigation and multi-nutrient (P/K/S) action spaces |
| P1 | Error-prone operational edges (weather windows, vectorized subprocess failures) | Reduces reliability in large experiment sweeps | Add stronger config validation and fault-tolerant execution wrappers |
| P2 | No field or expert-in-the-loop validation yet | Simulation-only results can be challenged externally | Run pilot validation with agronomist-reviewed scenarios |
| P2 | Sparse statistical testing/reporting | Hard to prove significance beyond descriptive trends | Add confidence intervals, hypothesis tests, effect sizes |

## Code-Level Technical Debt Signals (From TODOs and Behavior)

1. crop-planning operation file handling has TODOs and simplifications
2. operation manager keying can collide for same-day layered operations
3. interfaces between abstract classes and implementations are inconsistent in places
4. some evaluation and compatibility paths required targeted patches (DQN, distribution assumptions)

These are manageable but should be documented as engineering hardening tasks.

## Agricultural Extension Opportunities

1. Multi-nutrient optimization:
   extend fertilizer controls beyond N to P/K/S.
2. Water management:
   expose irrigation as decision variable with cost and water-risk terms.
3. Sustainability-aware objectives:
   convert leaching/emission constraints into explicit penalties or constrained-RL objectives.
4. Region transfer:
   repeat workflow for additional Pakistan agro-climatic zones.

## Defense-Oriented Action Plan

### Next 2 Weeks

1. finish missing key matrix runs
2. create final seed-aggregated tables and plots
3. standardize baseline-vs-RL metric schema

### Next 1-2 Months

1. add one new controlled resource (irrigation or P/K)
2. run ablation on reward/economic assumptions
3. package inference API with guardrails and OOD warnings

### Post-Thesis

1. pilot validation with domain experts and field constraints
2. extend to hierarchical planning (yearly crop + weekly inputs)
3. integrate richer risk/market models
