# Resource Allocation Scope (Current vs Minimal Extensions)

Thesis focus: "Optimizing Agricultural Resource Allocation through RL for Yield Improvement."
This repo already covers some resource decisions, but not all. Below is a clear scope map.

## What is allocated today (in code)

### 1) Nitrogen fertilizer (primary resource allocation)
- Environment: `cyclesgym/envs/corn.py`
- Action: discrete weekly N amount (kg/ha) mapped by `_action2mass`.
- Implementer writes `FIXED_FERTILIZATION` in the operation file via
  `cyclesgym/envs/implementers.py:FixedRateNFertilizer`.
- Economics: reward includes nitrogen cost (see `cyclesgym/envs/rewarders.py`).

This is the most direct "resource allocation" in the current code.

### 2) Crop choice (land use/rotation planning)
- Environment: `cyclesgym/envs/crop_planning.py`
- Action: yearly crop selection (rotation).
- This is not a resource like fertilizer or water, but it is a management allocation
  that strongly affects resource use and profit.

### 3) Planting window parameters (management constraints)
- In crop planning, the action also includes planting window bounds and a soil
  moisture threshold for planting (DOY, END_DOY, MAX_SMC).
- These are management decisions, not a "resource," but they affect yields.

## What is NOT allocated (exogenous inputs)

- Weather (rainfall, temperature, radiation) comes from `*.weather` files and is
  fixed or shuffled. You cannot allocate rainfall.
- Soil properties (`*.soil`) are fixed per run.
- Crop genetic parameters (`*.crop`) are fixed per run.

These are inputs to the simulator, not decisions.

## Economics in the current code

- Crop prices and N prices affect rewards only.
- They do not affect the simulator physics (growth, soil, weather).
- Relevant files:
  - `cyclesgym/utils/pricing_utils.py`
  - `cyclesgym/envs/rewarders.py`

## Minimal-effort extensions that still make sense

These fit your thesis theme and align with how the repo is built.

### A) Add other fertilizer nutrients (P, K, S)
Why it makes sense:
- `Fertilizer` already supports multiple nutrients.
- You can define an env that controls P or K mass similarly to N.

What changes:
- Create a new env class or extend `Corn` to use `Fertilizer` with
  `affected_nutrients=['P_INORGANIC']` (or others).
- Add price terms in rewarders (like `NProfitabilityRewarder`).

### B) Add an environmental penalty (leaching or emissions)
Why it makes sense:
- Constraints for leaching and emissions already exist in
  `cyclesgym/envs/constrainers.py`.
- You can turn these into reward penalties without changing Cycles.

What changes:
- Add a rewarder that reads the same outputs and subtracts a cost.

### C) Add irrigation as a controlled input (if irrigation is enabled in Cycles)
Why it makes sense:
- Water from rainfall is exogenous, but irrigation is a management decision.
- Cycles supports irrigation operations, but this repo does not expose them yet.

What changes:
- Create a new implementer that writes `FIXED_IRRIGATION` operations.
- Add an action space for irrigation amount and a cost term in reward.

This is moderate effort, but still consistent with the design.

## What is NOT a minimal change

These are bigger changes and require more than small edits:
- Multi-field land allocation (area across multiple fields).
- Dynamic market modeling (prices changing within episodes).
- Replacing Cycles with a different simulator.

## Summary (for your thesis scope)
Current code already optimizes:
- Nitrogen fertilizer allocation (weekly).
- Crop rotation choices (yearly).

Minimal, logical extensions:
- Add other nutrient allocation (P/K/S).
- Add cost/penalty terms tied to existing outputs.
- Add irrigation control if you provide irrigation config in Cycles inputs.
