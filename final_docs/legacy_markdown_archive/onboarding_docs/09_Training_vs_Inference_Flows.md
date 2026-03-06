# Training vs Inference: Fertilization vs Crop Planning

This repo has two main task families:
1) Fertilization control (short-term, within a season).
2) Crop planning / rotation (long-term, across years).

They are separate environments and are usually trained separately.
They share the same simulator (Cycles) and the same data pipeline, but the actions,
state, and reward design are different.

## Are they trained separately?
Yes, in practice they are trained separately.
- Fertilization uses `cyclesgym/envs/corn.py` and scripts in `experiments/fertilization/`.
- Crop planning uses `cyclesgym/envs/crop_planning.py` and scripts in `experiments/crop_planning/`.

Why separate:
- Action spaces are different (weekly N amount vs yearly crop choice).
- Time scales are different (weekly steps vs yearly steps).
- Reward logic is different (fertilizer cost + crop yield vs rotation profit).

## How are they related economically?
Both tasks are framed as economic optimization:
- Fertilization: maximize profit = yield value minus nitrogen cost.
- Crop planning: maximize profit across a crop rotation (sum of harvest value).

In both cases, the reward is the economic signal:
- Fertilization adds a cost term (`NProfitabilityRewarder`).
- Both use `CropRewarder` for harvest revenue.

## Do you use both in a single model at inference?
Not by default.
The repo treats them as different tasks, so inference is different too:
- Fertilization inference: pick N amount each step of a season.
- Crop planning inference: pick crop (and possibly planting params) each year.

If you wanted a combined system in the future, it would look like:
- A higher-level planner chooses the crop for each year.
- A lower-level controller chooses weekly fertilization within that year.
This is a multi-scale decision problem and would need custom glue code.

## Overall flow comparison
```mermaid
flowchart TB
    subgraph Fertilization
        F1[Env: Corn] --> F2[Action: N amount weekly]
        F2 --> F3[Cycles run + outputs]
        F3 --> F4[Reward: yield - N cost]
    end

    subgraph CropPlanning
        C1[Env: CropPlanning] --> C2[Action: crop choice yearly]
        C2 --> C3[Cycles run + outputs]
        C3 --> C4[Reward: rotation profit]
    end
```

## Prices: what they affect (and what they do not)
Short answer: prices affect rewards only, not the simulator physics.

- Crop price is used by `CropRewarder` to convert yield into dollars.
- Fertilizer (N) price is used by `NProfitabilityRewarder` to convert N use into cost.
- These prices do not change crop growth, soil, or weather in Cycles.
- Crop planning uses crop prices (harvest revenue). Fertilization uses crop prices and N prices.

If you want prices to affect anything else (e.g., action constraints or behavior),
you must code it explicitly in rewarders or constrainers.

## Parallel streams vs combined pipeline
Current repo usage is parallel and separate:
```mermaid
flowchart LR
    subgraph StreamA[Fertilization Stream]
        A1[Train fertilization policy] --> A2[Infer weekly N actions]
    end
    subgraph StreamB[Crop Planning Stream]
        B1[Train crop planning policy] --> B2[Infer yearly crop choices]
    end
```

There is no built-in pipeline that runs crop planning first and then fertilization.
If you want a combined decision process, you can build a two-level workflow:

```mermaid
flowchart TD
    H1[Year-level planner] --> H2[Crop choice for year]
    H2 --> L1[Season-level controller]
    L1 --> L2[Weekly N actions]
    L2 --> S1[Cycles simulation outputs]
    S1 --> H1
```

This requires custom glue code and likely a custom environment.

## How to run each stream today
Fertilization (weekly N):
- Train: `experiments/fertilization/train.py`
- Infer: load the trained model and step the `Corn` env.

Crop planning (yearly crop choice):
- Train: `experiments/crop_planning/train.py`
- Infer: load the trained model and step the `CropPlanning` env.

If you want both in sequence:
1) Run crop planning inference to select a rotation.
2) For each year, run a fertilization policy inside a `Corn`-style env for that crop.
This is not provided out of the box and needs an integration script.

## Where to look in code
- Fertilization env: `cyclesgym/envs/corn.py`
- Crop planning env: `cyclesgym/envs/crop_planning.py`
- Fertilization training: `experiments/fertilization/train.py`
- Crop planning training: `experiments/crop_planning/train.py`
- Reward logic: `cyclesgym/envs/rewarders.py`
