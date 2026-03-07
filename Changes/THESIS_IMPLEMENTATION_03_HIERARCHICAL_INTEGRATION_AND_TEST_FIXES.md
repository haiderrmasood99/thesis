# Thesis Implementation Update 03: Hierarchical Crop Planning + NPK Fertilization Integration

- Date: 2026-03-07 (Asia/Karachi)
- Goal: Start Step 3 by integrating yearly crop planning and within-year fertilization (NPK economics) in one RL environment, and fix CYCLES test invocation so integration tests pass on Windows.

## What Was Implemented

1. Added new hierarchical environment:
- `cyclesgym/envs/hierarchical.py`
- Class: `HierarchicalCropPlanningFertilization`
- Core behavior:
  - Action has two levels in one policy:
    - yearly planning channels: crop + planting window
    - weekly fertilization channels: N or NPK
  - Planning action is applied once at start of each simulation year.
  - Fertilization action is applied every step.
  - Reward combines:
    - crop profitability for all rotation crops
    - fertilizer cost reward (`N` or `NPK`) using selected price profile
  - Constraint outputs preserved (`cost_total_n`, leaching/emissions/event count).

2. Exported hierarchical env in package entrypoint:
- `cyclesgym/envs/__init__.py`

3. Wired hierarchical mode into training entrypoint (opt-in):
- `experiments/crop_planning/train.py`
- Added env import and CLI flag:
  - `--hierarchical True`
- Added hierarchical config knobs:
  - `nutrient_action_mode`, `price_profile`, `maxN`, `maxP`, `maxK`,
  - `fert_n_actions`, `p_actions`, `k_actions`, `fert_delta`,
  - `use_pakistan_crop_calendar`.
- Backward compatibility:
  - Existing crop-planning training flow remains default unless `--hierarchical True`.

4. Added hierarchical smoke tests:
- `cyclesgym/tests/test_hierarchical_env.py`
- Verifies:
  - reset/step works,
  - planner applied on first yearly step,
  - planner not re-applied on second step in same year.

## CYCLES Invocation Fixes for Integration Tests

1. Replaced hardcoded `./Cycles` calls in tests with platform-aware executable path:
- `cyclesgym/tests/test_crop_planning.py`
- `cyclesgym/tests/test_env.py`
- `cyclesgym/tests/test_random_weather.py`
- Uses: `CYCLES_PATH.joinpath(CYCLES_EXE)` from `cyclesgym/utils/paths.py`.

2. Added Gymnasium-compatible step handling in tests and utility runner:
- `cyclesgym/tests/test_crop_planning.py`
- `cyclesgym/tests/test_env.py`
- `cyclesgym/tests/test_random_weather.py`
- `cyclesgym/utils/utils.py` (`run_env`) now handles 4- and 5-tuple step returns.

3. Removed test hang blocker in env comparison:
- `cyclesgym/utils/utils.py` (`compare_env`)
- plotting is now opt-in only via env var:
  - `CYCLESGYM_PLOT_COMPARE=1`
- prevents blocking `plt.show()` during CI/test runs.

4. Restored control-file parity in integration tests:
- Some tests compare against legacy `GenericCrops/RockSprings` controls.
- Added explicit test env parameters + extensibility hooks:
  - `crop_file` parameter added to:
    - `cyclesgym/envs/corn.py`
    - `cyclesgym/envs/crop_planning.py`
- Tests now explicitly use matching legacy files when doing manual-vs-env comparisons.

## Why This Matters (Layman Terms)

Before this step, crop choice and fertilizer policy were separate.  
Now we have a single environment where the RL agent can decide what to plant for the year and how much fertilizer to apply week by week, while charging costs with NPK-aware economics. This is much closer to real farm decision making.

Also, the integration tests were failing on Windows because of executable invocation and API-format mismatches; those blockers are now fixed.

## Thesis Relevance

1. Directly supports the thesis objective of joint resource allocation.
2. Enables experiments where crop planning and fertilization policy are co-optimized.
3. Preserves scientific integrity via backward-compatible defaults and passing regression tests.

## Verification Performed

1. Compile checks:
- `python -m compileall cyclesgym/envs/hierarchical.py cyclesgym/envs/__init__.py experiments/crop_planning/train.py cyclesgym/tests/test_hierarchical_env.py cyclesgym/tests/test_crop_planning.py cyclesgym/tests/test_env.py cyclesgym/tests/test_random_weather.py`
- Result: PASS

2. Integration tests (previous blockers):
- `pytest cyclesgym/tests/test_crop_planning.py cyclesgym/tests/test_env.py cyclesgym/tests/test_random_weather.py cyclesgym/tests/test_hierarchical_env.py -q`
- Result: PASS (`10 passed`)

3. Prior Step 1/2 regression set:
- `pytest cyclesgym/tests/test_rewarders.py cyclesgym/tests/test_implementers.py cyclesgym/tests/test_constrainers.py cyclesgym/tests/test_pricing_utils.py -q`
- Result: PASS (`21 passed`)

4. Full `cyclesgym/tests` suite:
- `pytest cyclesgym/tests -q`
- Result: PASS (`53 passed`, warnings only)

5. Additional full-suite compatibility hardening:
- `cyclesgym/tests/test_policies.py`
  - switched to `cyclesgym.utils.gym_compat` imports to avoid legacy `gym` dependency mismatch.
- `cyclesgym/tests/test_managers.py`
  - updated strict dataframe/string assertions to be robust across pandas dtype inference and Windows CRLF formatting.

## Usage Example

Hierarchical training mode:

```bash
python experiments/crop_planning/train.py --hierarchical True --method PPO
```

## Next Step

1. Add experiment tracking/report outputs specific to hierarchical runs:
- yearly crop decisions,
- weekly N/P/K applications,
- per-nutrient cost decomposition,
- season-window compliance metrics.
