# 07. Thesis Defense Pack

## Thesis Title Context

Target claim area:

**Optimizing Agricultural Resource Allocation through Reinforcement Learning: A Cost-Driven Approach to Crop Efficiency Enhancement in Pakistan**

## Defensible Claim Style

Use phrasing like:
- "best observed under audited runs"
- "evidence suggests"
- "within the current experiment coverage"

Avoid:
- "globally optimal across all configurations" (unless full matrix is executed and statistically validated)

## X/Y/Z Framing

Use a clean configuration language:
- `X`: algorithm (`PPO`, `A2C`, `DQN`)
- `Y`: adaptation mode (`adaptive` vs `nonadaptive`)
- `Z`: weather mode (`fixed_weather` vs `random_weather`)

Optional fourth factor in fertilization:
- training budget (`total_years`)

## Evidence Snapshot (From Existing Audit Docs)

Audit window documented in repo:
- February 23, 2026 to February 25, 2026

Observed summary values reported in existing markdown:
- run folders audited: 64
- successful with summary: 44
- failed with traceback: 16
- no-summary metadata: 4
- `run_all_2` planned configurations: 96
- successful covered configurations observed: 34

## Core Storyline You Can Defend

1. Problem:
   resource allocation under weather uncertainty and fertilizer cost pressure
2. Method:
   RL over CYCLES-based simulator with economic reward shaping
3. Findings:
   PPO-based settings lead observed performance in current evidence
4. Practical recommendation:
   fertilization deployment prefers robust random-weather PPO settings for holdout behavior
5. Limitation:
   full design-space coverage and stronger multi-seed robustness remain pending

## Likely Committee Questions and Tight Answers

1. Why simulation, not field trial?  
   Simulation enables large-scale policy learning safely; field validation is planned next phase.
2. Why believe generalization?  
   Held-out weather evaluation is included, but full robustness requires expanded matrix completion.
3. Is this only fertilizer optimization?  
   Current code directly optimizes weekly N and yearly crop choice; irrigation and other resources are identified extensions.
4. Are economics realistic?  
   Current rewards are simplified and transparent; richer pricing/risk models are a declared future step.

## Defense Slide Checklist

1. one architecture slide (policy -> env -> simulator -> reward)
2. one environment slide (fertilization vs crop-planning actions/observations)
3. one evidence slide (audited run counts + top observed configurations)
4. one caveat slide (coverage gaps + what is needed for full closure)
5. one roadmap slide (pilot inference UI -> full validation)
