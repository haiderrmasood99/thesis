# 07. Thesis Defense Pack

## Thesis Title Context

Target claim area:

**Optimizing Agricultural Resource Allocation through Reinforcement Learning: A Cost-Driven Approach to Crop Efficiency Enhancement in Pakistan**

## Defensible Claim Style

Use phrasing like:
- "within the completed 113-case matrix"
- "best repeated group"
- "best single run"
- "under the current simulator and reward design"

Avoid:
- "globally optimal for all farms"
- "field-validated recommendation"

## X/Y/Z Framing

Use a clean configuration language:
- `X`: algorithm (`PPO`, `A2C`, `DQN`)
- `Y`: adaptation mode (`adaptive` vs `nonadaptive`)
- `Z`: weather mode (`fixed_weather` vs `random_weather`)

Optional fourth factor in fertilization:
- training budget (`total_years`)

## Evidence Snapshot (Final March 2026 Audit)

Campaign window documented in repo:
- March 7, 2026 to March 11, 2026 (Pakistan time)

Observed summary values from the final export:
- planned configurations: `113`
- unique finished configurations: `113/113`
- total attempts: `117`
- initial failed attempts: `4`, all rerun successfully
- finished by domain: `75` fertilization, `26` crop planning, `12` hierarchical failed-ablation runs
- fertilization baseline best return: `750,198.06`
- fertilization RL runs exceeding baseline: `11/74`

## Core Storyline You Can Defend

1. Problem:
   resource allocation under weather uncertainty and fertilizer cost pressure
2. Method:
   RL over a CYCLES-based simulator with Pakistan weather, soil, and price assumptions
3. Findings:
   PPO is the strongest overall fertilization family; crop planning is competitive between non-hierarchical PPO and A2C; the hierarchical branch is a failed ablation rather than a benchmark contender
4. Practical recommendation:
   deploy non-hierarchical policies only, with PPO as the main fertilization reference and PPO/A2C as crop-planning candidates
5. Limitation:
   results are simulator-based and still need formal statistics plus external validation

## Likely Committee Questions and Tight Answers

1. Why simulation, not field trial?
   Simulation enables safe, large-scale policy search first; field validation is the next phase, not the evidence base used here.
2. Why believe generalization?
   Fertilization includes holdout-weather evaluation (`pak_holdout_return`), and crop planning was tested across fixed/random weather with three seeds for PPO and A2C.
3. What if the committee asks about hierarchical RL?
   The hierarchical branch was executed completely, but all 12 runs were strongly negative and are excluded from the main result table. The report shows mean nutrient cost of about `8.6M`, only `38.3%` of yearly decisions with defined calendar windows, and a strong negative cost-vs-return correlation (`-0.85`), so the defensible position is failed ablation plus future work.
4. Are the economics realistic?
   They are Pakistan-localized and cost-aware, but still simplified relative to full farm economics.

## Defense Slide Checklist

1. one architecture slide (policy -> env -> simulator -> reward)
2. one matrix-completion slide (`113/113` finished, `4` reruns recovered)
3. one results slide (top fertilization and crop-planning groups)
4. one caveat slide (hierarchical failed ablation due to nutrient-cost blow-up and incomplete calendar coverage, plus no field validation and no significance tests yet)
5. one roadmap slide (statistics package -> constrained hierarchical redesign -> pilot validation)
