# Reward Functions and Economics

This repo encodes economic objectives directly in the reward functions.
The main idea: reward = value of harvest minus input costs.

Primary files:
- Reward logic: `cyclesgym/envs/rewarders.py`
- Prices: `cyclesgym/utils/pricing_utils.py`

## Fertilization environment rewards
The fertilization env uses a compound reward:
- `CropRewarder`: harvest revenue
- `NProfitabilityRewarder`: nitrogen cost

In code (conceptual):
```text
reward_t = harvest_value_t - nitrogen_cost_t
```

### Harvest revenue
From `CropRewarder`:
- It checks if a harvest happened between the previous step and current step.
- It reads `season.dat` via `SeasonManager` to find harvest date and yield.
- It multiplies yield by a crop price for that year.

Equation (units):
```text
harvest_value = yield_tonnes_per_ha * price_dollars_per_tonne
```

### Nitrogen cost
From `NProfitabilityRewarder`:
- Nitrogen mass is the action value in kg/ha.
- Price is `N_price_dollars_per_kg` (constant in this repo).

Equation:
```text
nitrogen_cost = N_kg_per_ha * price_dollars_per_kg
reward = harvest_value - nitrogen_cost
```

## Crop planning rewards
Crop planning uses:
- `CropRewarder` for each crop in the rotation.
- Reward is the sum of crop profits across the rotation.

This is still "profit", but at a yearly time step instead of weekly.

## Where prices come from
`cyclesgym/utils/pricing_utils.py` defines:
- Crop prices in dollars per tonne (corn, soybean, corn silage)
- Nitrogen price in dollars per kg
- Crop yield column names (`GRAIN YIELD`, `FORAGE YIELD`)

Prices are fixed and repeated across years in the current setup.

## Limitations (important to know)
- Only nitrogen cost is modeled (no labor, machinery, water, or seed costs).
- Prices are simple averages, not dynamic market forecasts.
- No discounting or risk/variance penalty in the reward.

## How to customize economics
1) Update price dictionaries in `cyclesgym/utils/pricing_utils.py`.
2) Add new rewarders in `cyclesgym/envs/rewarders.py`.
3) Combine rewarders with `compound_rewarder` in the env.

Practical examples:
- Add a water cost term (if irrigation actions are added).
- Add a sustainability penalty (e.g., nitrate leaching).
- Add a risk penalty (variance of yield across years).
