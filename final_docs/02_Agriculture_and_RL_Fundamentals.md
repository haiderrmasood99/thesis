# 02. Agriculture and RL Fundamentals

## Agriculture Basics (No Background Assumed)

1. Crop growth depends on weather, soil, nutrients, and management actions.
2. Nitrogen (N) is a key nutrient: too little hurts yield, too much wastes cost and increases losses.
3. Soil is layered; water can move nutrients downward (leaching), reducing plant uptake.
4. A "season" is one crop cycle in a year; a "rotation" is the sequence of crops over years.

## RL Basics Mapped to This Repo

1. State (`obs`): weather + crop + soil/N summaries (depends on env).
2. Action (`action`): management decision (weekly N amount or yearly crop choice).
3. Reward (`reward`): economic objective, mostly harvest value minus input costs.
4. Episode: one simulation horizon (single-year or multi-year, depending on env).
5. Policy: function from state to action, learned by PPO/A2C/DQN.

## Economic Objective

At high level:

```text
reward = harvest_revenue - input_costs
```

In fertilization:
- harvest revenue from `CropRewarder`
- nitrogen cost penalty from `NProfitabilityRewarder`

In crop planning:
- reward is crop-profit signal across yearly choices

## Why Weather Mode Matters

1. Fixed weather: easier optimization, can inflate in-distribution performance.
2. Random/shuffled weather: harder optimization, better robustness signal under uncertainty.

## Agronomy-RL Tradeoff in One Line

```text
More fertilizer can improve yield up to a point, then returns diminish while cost and environmental risk continue.
```

## Glossary for New Readers

- `control.ctrl`: master simulation configuration
- `operation.operation`: management actions (fertilization, planting, etc.)
- `weather.weather`: daily weather time series
- `soil.soil`: soil profile
- `season.dat`: seasonal outcomes including harvest records
- `N.dat`: nitrogen dynamics outputs

## Why This Is Defensible for Thesis Scope

This repo operationalizes resource allocation through:
1. direct fertilizer-allocation control
2. long-horizon crop-allocation control
3. explicit economic reward shaping

That is enough to support a cost-driven RL framing while clearly identifying missing controls as future work.
