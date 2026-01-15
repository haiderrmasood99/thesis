# Fertilization Environment Flow (Corn)

Primary file:
- `cyclesgym/envs/corn.py`

What the agent controls:
- The action is a discrete index that maps to a nitrogen mass (kg/ha).
- The env applies that fertilization to the current date.

Observation components:
- Weather (from `WeatherObserver`)
- Crop state (from `CropObserver`)
- Nitrogen-to-date (from `NToDateObserver`)

Reward components:
- Harvest profit (from `CropRewarder`)
- Fertilizer cost penalty (from `NProfitabilityRewarder`)

Constraints:
- Total N budget
- Max fertilization events
- N leaching constraints

Flow diagram:
```mermaid
flowchart LR
    A[Discrete action a] --> B[_action2mass -> N kg/ha]
    B --> C[FixedRateNFertilizer\nupdate operation file]
    C -->|changed| D[Run Cycles.exe]
    D --> E[Output managers read .dat]
    E --> F[Observers build state]
    E --> G[Rewarders compute reward]
    E --> H[Constrainers compute info]
    F --> I[Return obs]
    G --> I
    H --> I
```

Real-life example:
- You are a farm manager deciding how much nitrogen to apply each week.
- Applying more nitrogen can increase yield but also costs money and can leach into groundwater.
- The env balances "more yield" vs "more cost" using reward functions.

Code map:
- Action mapping: `cyclesgym/envs/corn.py:_action2mass`
- Implementer: `cyclesgym/envs/implementers.py:FixedRateNFertilizer`
- Observers: `cyclesgym/envs/observers.py`
- Rewarders: `cyclesgym/envs/rewarders.py`
- Constraints: `cyclesgym/envs/constrainers.py`
