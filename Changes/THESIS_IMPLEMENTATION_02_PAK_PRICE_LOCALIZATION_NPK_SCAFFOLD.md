# Thesis Implementation Update 02: Pakistan Price Localization + NPK Scaffolding

- Date: 2026-03-06 (Asia/Karachi)
- Goal: Add Pakistan-localized economics and make fertilization pipeline NPK-ready, without breaking existing N-only workflows.

## What Was Implemented

1. Price profile system added in `cyclesgym/utils/pricing_utils.py`.
- Introduced named profiles:
  - `us_legacy` (default, preserves previous behavior).
  - `pakistan_baseline` (opt-in thesis profile).
- Added profile access helpers:
  - `get_price_profile(...)`
  - `get_crop_prices(...)`
  - `get_crop_type(...)`
  - `get_nutrient_prices(...)`
- Kept backward-compatible globals:
  - `crop_prices`
  - `crop_type`
  - `N_price_dollars_per_kg`

2. Pakistan crop-price localization (profile `pakistan_baseline`).
- Added Pakistan producer-price series (LCU/tonne) for:
  - maize (`CornRM.90`, `CornRM.100`)
  - soybean (`SoybeanMG.3`, `SoybeanMG.5`)
- Added scaffolding silage estimate (`CornSilageRM.90`) using legacy silage-to-grain ratio until Pakistan silage series is sourced.

3. Pakistan NPK fertilizer-price localization (profile `pakistan_baseline`).
- Added nutrient prices (Rs/kg nutrient) derived from NFDC retail bag prices.
- Added N/P/K nutrient conversion assumptions in code:
  - Urea 46% N
  - DAP 18:46 interpreted with 46% P2O5 and `P2O5 -> P` factor `0.4364`
  - SOP with 50% K2O and `K2O -> K` factor `0.8301`

4. Reward scaffolding upgraded in `cyclesgym/envs/rewarders.py`.
- `CropRewarder` now supports `price_profile=...` (default remains legacy behavior).
- `NProfitabilityRewarder` now supports dict/list/scalar action parsing.
- Added new `NPKProfitabilityRewarder` for combined N+P+K fertilizer cost.
- Added shared action parser for:
  - scalar N
  - list/array `[N, P, K]`
  - dict with keys such as `N`, `P`, `K`, `N_NH4`, `N_NO3`, `P_INORGANIC`.

5. Action/implementation scaffolding upgraded for NPK.
- Added `FixedRateNPKFertilizer` in `cyclesgym/envs/implementers.py`.
  - Splits N into `N_NH4` + `N_NO3` with configurable fixed ratio.
  - Passes P and K as `P_INORGANIC` and `K`.
- Extended `Corn` env (`cyclesgym/envs/corn.py`) with opt-in mode:
  - `nutrient_action_mode='N'` (default, unchanged behavior)
  - `nutrient_action_mode='NPK'` (new)
  - `maxP`, `maxK`, `p_actions`, `k_actions`, `n_nh4_rate`, `price_profile`
- In NPK mode:
  - Action space is `MultiDiscrete([n_actions, p_actions, k_actions])`.
  - Reward path uses `NPKProfitabilityRewarder`.
  - Implementer path uses `FixedRateNPKFertilizer`.

6. Constraint path made NPK-aware in `cyclesgym/envs/constrainers.py`.
- `FertilizationEventConstrainer` and `TotalNitrogenConstrainer` now accept scalar/list/dict action formats.
- Preserved existing `cost_total_n` semantics (nitrogen-only accounting).

## Why This Matters (Layman Terms)

Before this update, the model mostly used a US-style N-only economics view.  
Now, you can keep old behavior for continuity, or switch to a Pakistan-oriented setup and start modeling fertilizer decisions across N, P, and K. This directly supports thesis arguments about cost-driven, locally relevant resource allocation.

## Thesis Relevance

1. Local realism: economics can now be aligned to Pakistan data.
2. Extension-ready: model supports moving from single-nutrient policy to multi-nutrient policy.
3. Safe evolution: default behavior is unchanged, so previous experiments remain reproducible.

## Data Sources and Links Used

1. Pakistan fertilizer retail prices (NFDC, Rs per 50kg bag):
- [NFDC Retail Fertilizer Prices](https://nfdc.gov.pk/Web-Page%20Updating/prices.htm)

2. Pakistan producer crop prices (FAOSTAT Prices dataset, LCU/tonne):
- [FAOSTAT Prices bulk download](https://fenixservices.fao.org/faostat/static/bulkdownloads/Prices_E_All_Data_(Normalized).zip)

## Key Assumptions (Explicit)

1. Nutrient conversion assumptions:
- `P2O5 -> P = 0.4364`
- `K2O -> K = 0.8301`

2. NFDC bag prices used as baseline nutrient-price anchor:
- Table row interpreted as annual baseline (`2021-22`) for scaffolding.

3. Pakistan silage price series is not yet sourced:
- Current `CornSilageRM.90` in Pakistan profile uses legacy silage/grain ratio as a placeholder.

4. Missing-year handling:
- Reward lookup already uses nearest historical fallback (`_lookup_year_value`), so sparse annual series still run safely.

## Integrity / Backward Compatibility Controls

1. Default profile remains `us_legacy`.
2. Default nutrient action mode remains N-only (`nutrient_action_mode='N'`).
3. Existing scripts constructing `Corn(...)` with old args continue to run.
4. Added focused tests instead of changing historical test expectations.

## Verification Performed

1. Compile checks:
- `python -m compileall cyclesgym/utils/pricing_utils.py cyclesgym/envs/rewarders.py cyclesgym/envs/constrainers.py cyclesgym/envs/implementers.py cyclesgym/envs/corn.py cyclesgym/tests/test_rewarders.py cyclesgym/tests/test_implementers.py cyclesgym/tests/test_constrainers.py cyclesgym/tests/test_pricing_utils.py`
- Result: PASS

2. Unit tests:
- `pytest cyclesgym/tests/test_rewarders.py cyclesgym/tests/test_implementers.py cyclesgym/tests/test_constrainers.py cyclesgym/tests/test_pricing_utils.py -q`
- Result: PASS (`21 passed`, `1 warning`)

3. Runtime smoke checks:
- `Corn(..., nutrient_action_mode='NPK', ...)` reset + step executed successfully.
- Legacy `Corn(...)` N-only reset + step executed successfully.

## Example Usage

N-only (legacy behavior unchanged):

```python
env = Corn(delta=7, n_actions=11, maxN=150, start_year=2005, end_year=2005)
```

NPK mode + Pakistan economics profile:

```python
env = Corn(
    delta=7,
    n_actions=11,
    maxN=150,
    nutrient_action_mode='NPK',
    maxP=80,
    maxK=60,
    price_profile='pakistan_baseline',
    start_year=2005,
    end_year=2005,
)
```

## Next Gap to Close

1. Replace placeholder silage pricing with Pakistan-specific silage market series.
2. Add year-varying Pakistan fertilizer nutrient prices (instead of single baseline).
3. Add policy/reporting outputs that break fertilizer decisions into N/P/K cost contributions for thesis tables.
