# Thesis Implementation 05: Fertilization NPK + Pakistan Final-Run Readiness

Date: 2026-03-07

## What Was Implemented

1. Fertilization pipeline now supports full NPK action mode end-to-end:
- `experiments/fertilization/corn_soil_refined.py`
  - Added pass-through parameters for:
    - `nutrient_action_mode` (`N` or `NPK`)
    - `maxP`, `maxK`, `p_actions`, `k_actions`
    - `n_nh4_rate`
    - `price_profile`
  - `CornSoilRefined` / `NonAdaptiveCorn` wrappers now preserve NPK action/reward behavior instead of forcing N-only internals.

2. Fertilization training defaults are now Pakistan-aligned and NPK-ready:
- `experiments/fertilization/train.py`
  - Default config now uses:
    - `nutrient_action_mode="NPK"`
    - `price_profile="pakistan_baseline"`
    - `maxN=150`, `maxP=80`, `maxK=60`
  - Added CLI flags:
    - `--nutrient-action-mode {N,NPK}`
    - `--price-profile`
    - `--maxN --maxP --maxK`
    - `--p-actions --k-actions`
    - `--n-nh4-rate`
  - Env creation now passes nutrient mode + Pakistan pricing parameters in all branches (adaptive/nonadaptive, soil env, fixed/random weather).
  - Baseline evaluator now works with NPK mode by mapping N-only baseline sequences into `[N,0,0]`.
  - Standardized summary JSON now records:
    - `nutrient_action_mode`
    - `price_profile`

3. Logical bug fix in holdout evaluation:
- `experiments/fertilization/train.py`
  - `eval_nh()` now uses the holdout/test env (`_, eval_env = self.get_envs(...)`) instead of the train env.

4. Open-loop policy fix for vectorized multi-channel actions:
- `cyclesgym/policies/dummy_policies.py`
  - `OpenLoopPolicy.predict()` now correctly returns batched action shapes for vectorized envs.
  - This prevents wrong action slicing for MultiDiscrete evaluation/baseline runs.

5. Final matrix runner is now fertilization-NPK/Pakistan ready:
- `run_all_2.py`
  - Added fertilization matrix options:
    - `--fert-nutrient-action-mode` (default `NPK`)
    - `--fert-price-profile` (default `pakistan_baseline`)
    - `--fert-maxN --fert-maxP --fert-maxK`
    - `--fert-p-actions --fert-k-actions`
    - `--fert-n-nh4-rate`
  - Fertilization core, DQN ablations, and baseline command builders now pass these options to `experiments/fertilization/train.py`.

6. Data refresh from live online sources completed:
- Re-ran:
  - `python scripts/build_pakistan_price_series.py`
- Updated:
  - `cyclesgym/resources/pricing/pakistan_yearly_series.json`
  - Includes refreshed metadata timestamp and latest reconstructed yearly series.

## Why This Matters (Layman Terms)

Before this update, fertilization training mostly optimized nitrogen only, even though thesis framing is about broader resource allocation and nutrient economics. Now the training stack can optimize N, P, and K decisions together while using Pakistan-specific economics by default, making thesis experiments more realistic and defendable.

## Online Sources Used

1. FAOSTAT Pakistan producer prices (crop yearly series):
- https://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip

2. NFDC Pakistan fertilizer prices (historical product prices):
- https://nfdc.gov.pk/Web-Page%20Updating/prices.htm

## Verification

1. Compile checks:
- `python -m compileall experiments/fertilization/train.py experiments/fertilization/corn_soil_refined.py cyclesgym/policies/dummy_policies.py run_all_2.py cyclesgym/tests/test_policies.py`
- PASS

2. Targeted tests:
- `pytest cyclesgym/tests/test_policies.py cyclesgym/tests/test_pricing_utils.py cyclesgym/tests/test_rewarders.py cyclesgym/tests/test_hierarchical_env.py cyclesgym/tests/test_thesis_reporting.py -q`
- PASS (`17 passed`)

3. Full test suite:
- `pytest cyclesgym/tests -q`
- PASS (`59 passed, 8 warnings`)

4. Dry-run matrix validation:
- `python run_all_2.py --dry-run --include-hierarchical --include-baseline`
- PASS
- Verified fertilization commands now include `--nutrient-action-mode NPK --price-profile pakistan_baseline` and NPK channel hyperparameters.

5. NPK wrapper smoke check:
- Instantiated `CornSoilRefined(..., nutrient_action_mode='NPK', price_profile='pakistan_baseline')`
- Confirmed action space:
  - `MultiDiscrete([11 11 11])`
- Reset + one step executed successfully.
