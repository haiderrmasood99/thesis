# 10. Hierarchical Environment Explained

This document explains the hierarchical branch that is currently reported in the thesis as a failed ablation, not as part of the main benchmark result table.

## What "Hierarchical" Means Here

In this repo, "hierarchical" does **not** mean there are two separate agents talking to each other.

It means one policy makes **two levels of farm decisions inside one environment**:

1. a **year-level crop decision**
2. a **week-level fertilizer decision**

So the agent is trying to answer two questions at once:

- "What crop should I plant this year, and when should I plant it?"
- "How much N, P, and K should I apply this week?"

The environment that does this is:

- `cyclesgym/envs/hierarchical.py`
- class: `HierarchicalCropPlanningFertilization`

The training entry point is:

- `experiments/crop_planning/train.py`

## The Main Idea in Layman's Terms

Think of the system like this:

1. The RL agent writes farming instructions.
2. Those instructions are converted into an operation file.
3. The CYCLES crop simulator reads that file and simulates what would happen on the farm.
4. Python reads the simulator output files.
5. Python turns those outputs into:
   - the **next observation**
   - the **reward**
   - extra reporting information
6. The agent uses that feedback to decide the next action.

So CYCLES is the farm simulator.
The RL code is the decision-maker wrapped around that simulator.

## The Important Files

- `cyclesgym/envs/hierarchical.py`
  - defines the hierarchical environment
- `cyclesgym/envs/common.py`
  - shared reset / file creation / CYCLES execution logic
- `cyclesgym/envs/implementers.py`
  - writes planting and fertilization actions into the operation file
- `cyclesgym/envs/rewarders.py`
  - computes harvest income and fertilizer cost
- `cyclesgym/envs/observers.py`
  - builds the observation returned to the agent
- `cyclesgym/managers/operation.py`
  - reads and writes operation schedules
- `cyclesgym/managers/season.py`
  - reads `season.dat`
- `cyclesgym/managers/soil_n.py`
  - reads `N.dat`
- `cyclesgym/utils/thesis_reporting.py`
  - writes the hierarchical CSV and JSON reporting outputs

## Key Terms

### Episode
One full simulation run from the start year to the end year.

In the current crop-planning training script, the default hierarchical episode spans:

- start year: `2005`
- end year: `2018`

So one episode is roughly **14 years of weekly decisions**.

### Step
One call to `env.step(action)`.

In the hierarchical environment:

- `delta = 7`

So one step is normally **one week**.

### CYCLES Run
One execution of the external `Cycles` simulator binary.

This happens when the environment has changed the farm operations and needs fresh simulated outputs.

### Operation Year
Inside the CYCLES operation file, years are counted from the simulation start, not written as normal calendar years.

So if the episode starts in `2005`, then:

- calendar year `2005` -> operation year `1`
- calendar year `2006` -> operation year `2`
- calendar year `2010` -> operation year `6`

That is why the reporting files include both normal year information and `operation_year`.

### Observation
What the agent sees after each step.

In this environment, the observation is built from:

1. `SoilNObserver`
   - reads soil nitrogen related values from `N.dat`
2. `NToDateObserver(with_year=True)`
   - day of year
   - cumulative nitrogen applied so far
   - year position / remaining-year signal

So the observation is the simulator state summary that the agent uses for the next decision.

### Reward
The score the agent gets after a step.

Here it is:

- **crop revenue**
- **minus fertilizer cost**

### Training Epoch
This is an RL algorithm term, not a farm-simulation term.

For example, PPO may collect many environment steps and then do several gradient-update passes called epochs.

So:

- **environment step** = one simulated week
- **episode** = one full multi-year farm run
- **training epoch** = optimizer work inside PPO/A2C, not a farm week

## What One Action Looks Like

The hierarchical action space is:

```text
MultiDiscrete([n_crops, 14, 10, 10, n_actions, p_actions, k_actions])
```

With the current default thesis settings, that means:

```text
[crop_idx, plant_week_idx, plant_end_idx, plant_max_smc_idx, n_idx, p_idx, k_idx]
```

### Meaning of the 7 action numbers

1. `crop_idx`
   - which crop to plant this year
2. `plant_week_idx`
   - where inside the allowed crop calendar window planting should start
3. `plant_end_idx`
   - how wide the planting window should be
4. `plant_max_smc_idx`
   - planting moisture threshold setting
5. `n_idx`
   - discrete nitrogen level for this week
6. `p_idx`
   - discrete phosphorus level for this week
7. `k_idx`
   - discrete potassium level for this week

### Important detail

The policy outputs all 7 numbers on **every** step.

But the environment only uses them like this:

- the **first 4 crop-planning numbers** are only applied on the **first weekly step of each year**
- the **last 3 fertilizer numbers** are checked on **every weekly step**

So most weeks, the crop part is effectively ignored.

That is the practical meaning of "hierarchical" in this environment.

### Current guardrails for reruns

After the March 11, 2026 audit, the environment was hardened for targeted reruns:

1. yearly crop choices without a defined Pakistan calendar window are sanitized to a crop that does have one
2. weekly fertilizer is blocked outside the active crop-season window
3. yearly nutrient use is clipped by annual N/P/K budgets

These changes are meant to test whether the failed ablation can be stabilized. They do not change the interpretation of the already completed March results.

## How the Discrete Fertilizer Action Becomes Real Mass

The fertilizer indices are converted into kg/ha like this:

```text
N_mass = maxN * n_idx / (n_actions - 1)
P_mass = maxP * p_idx / (p_actions - 1)
K_mass = maxK * k_idx / (k_actions - 1)
```

With the current default thesis settings:

- `maxN = 150`
- `maxP = 80`
- `maxK = 60`
- `n_actions = 11`
- `p_actions = 11`
- `k_actions = 11`

So if `n_idx = 10`, that means the full nitrogen rate:

```text
150 kg/ha
```

In the current guarded version, those values also serve as the default annual N/P/K budget caps for the hierarchical branch unless you explicitly override them.

Then the N amount is split into:

- `N_NH4`
- `N_NO3`

using `n_nh4_rate`.

P is written as:

- `P_INORGANIC`

K is written as:

- `K`

## What Happens at the Start of an Episode

When `reset()` is called, the environment does a lot of setup work.

### Step-by-step reset flow

1. It sets the date to:
   - January 1 of the simulation start year
2. It creates a unique temporary input folder and output folder.
3. It links or copies the crop, soil, and weather files into that temporary input folder.
4. It creates a fresh operation file.
5. It writes a control file that points CYCLES to those temporary files.
6. It runs CYCLES once so the output files exist.
7. It builds file managers for:
   - weather
   - crop outputs
   - `season.dat`
   - `N.dat`
8. It creates:
   - the observer
   - the rewarder
   - the planter implementer
   - the fertilizer implementer
   - the constrainer
9. It clears the set that tracks which years already received a crop plan.
10. It resets planting and fertilization operations so the episode starts clean.
11. If those resets changed the operation file, it runs CYCLES again.
12. It computes the initial observation and returns it.

## What Files Exist During a Hierarchical Episode

At runtime, the important files are:

### Input-side files

- `control.ctrl`
- `operation.operation`
- `crop.crop`
- `soil.soil`
- `weather.weather`

### Output-side files

- crop output `.dat` files for the rotation crops
- `season.dat`
- `N.dat`

### What those outputs are used for

- `season.dat`
  - used for harvest timing and crop revenue
- `N.dat`
  - used for soil-N observation and environmental constraint reporting

## One Single Step, in Plain English

Below is exactly what happens when the agent takes one weekly step.

### 1. The agent sends one 7-part action

Example:

```text
[0, 6, 2, 5, 4, 3, 1]
```

This means something like:

- plant crop number 0 this year
- choose a planting date inside the allowed window
- choose a planting end window
- choose a moisture threshold
- apply some weekly N
- apply some weekly P
- apply some weekly K

### 2. The environment splits the action into two parts

Inside `step()`:

- crop part = first 4 values
- fertilizer part = last 3 values

So logically it becomes:

```text
crop_action = [crop_idx, plant_week_idx, plant_end_idx, plant_max_smc_idx]
fert_action = [n_idx, p_idx, k_idx]
```

### 3. The fertilizer part is converted into real kg/ha

The environment turns the discrete fertilizer bins into real masses:

- N kg/ha
- P kg/ha
- K kg/ha

It also calculates the monetary cost for this week's nutrient decision using the current year's Pakistan price profile.

### 4. The environment checks whether this is the first step of the year

Crop planning is only applied when both conditions are true:

1. that year has not been planned yet
2. the current day-of-year is within the first step window

In code, this is:

- `operation_year not in self.planned_operation_years`
- `doy <= self.delta`

Since `delta = 7`, that means crop planning is usually only applied during the first weekly step of that year.

### 5. If it is the first step of the year, the crop plan is written

The planter:

- decodes crop index into a crop name
- maps the planting week index into a real day-of-year
- respects Pakistan crop calendar windows if enabled
- writes or updates the `PLANTING` operation in `operation.operation`

After that:

- `planner_applied = True`
- that year is marked as already planned

### 6. The weekly fertilizer action is written

The fertilizer implementer:

- converts N/P/K into CYCLES nutrient fields
- checks whether today's fertilizer instruction is actually new
- if needed, writes a `FIXED_FERTILIZATION` operation into `operation.operation`

Important detail:

- if the nutrient masses are all zero and there is no existing fertilizer event for that date, it may decide there is nothing new to write
- if the operation file did change, then the environment knows the simulator must be rerun

### 7. The environment decides whether CYCLES must run again

If either of these changed the operation file:

- yearly planting action
- weekly fertilizer action

then the environment calls CYCLES.

If nothing changed, it can skip the simulator rerun for that step.

### 8. CYCLES simulates the updated farm state

When CYCLES runs, it reads:

- control file
- weather file
- soil file
- crop file
- operation file

Then it updates its output files, including:

- `season.dat`
- `N.dat`
- crop output `.dat` files

### 9. The environment moves time forward by one week

After the simulator part:

- `self.date += 7 days`

So the reward and next observation are computed for the **next weekly state**.

### 10. The output managers reload the latest files

After time advances, the environment reloads the simulator outputs.

That means the Python side now has the newest data from:

- `season.dat`
- `N.dat`
- crop `.dat` outputs

### 11. The reward is computed

This is one of the most important parts.

The total reward is:

```text
sum(crop rewards) + fertilizer reward
```

Which means:

```text
harvest revenue - nutrient cost
```

#### Crop reward part

For each crop rewarder:

1. it looks at `season.dat`
2. it checks whether a harvest happened between:
   - previous date
   - current date
3. if harvest happened in that one-week interval, it adds:

```text
yield * crop_price_for_that_year
```

If no harvest happened in that week, crop reward for that step is:

```text
0
```

#### Fertilizer cost part

The NPK rewarder:

1. reads the N/P/K masses from the action
2. looks up the nutrient prices for that year
3. computes:

```text
-(N_cost + P_cost + K_cost)
```

So fertilizer cost is usually an immediate negative reward.

### 12. Constraint values are computed

These are not the main reward, but they are added to `info`.

The environment computes:

- total nitrogen applied
- whether this step had a fertilization event
- leaching
- volatilization
- emission

These come from the action and `N.dat`.

### 13. The next observation is computed

The next observation is built from:

1. soil nitrogen values from `N.dat`
2. day-of-year
3. cumulative nitrogen applied so far
4. year-position signal

So the agent sees a weekly snapshot of:

- where it is in the calendar
- how much fertilizer it has already used
- what the soil nitrogen state looks like

### 14. The environment checks whether the episode is over

The episode ends when:

```text
date.year > simulation_end_year
```

So after the last simulated year is crossed, `done=True`.

## The Most Important Reward Timing Detail

This environment is hard because reward is delayed.

### What the agent feels on most weeks

Most weekly steps do **not** contain harvest income.

So many steps look like:

- fertilizer cost is negative
- harvest reward is zero
- total reward is negative or small

### When positive reward appears

Positive crop revenue appears only on the step whose 7-day interval crosses a harvest date.

So the agent has to learn:

- "If I choose a certain crop now"
- "and fertilize carefully over many weeks"
- "I may only see the big payoff much later"

That long delay is one reason hierarchical training is difficult.

## A Concrete Example: First Step of a New Year

Imagine the episode is currently at:

- date = January 1, 2010

The policy outputs:

```text
[0, 8, 1, 4, 6, 2, 1]
```

### What that means in plain English

1. choose crop index `0`
2. place its planting date somewhere inside that crop's allowed calendar window
3. choose a short planting end window
4. choose a moderate moisture threshold
5. apply a medium nitrogen amount this week
6. apply a small phosphorus amount
7. apply a very small potassium amount

### What the environment does

1. It sees this is the first weekly step of a new year.
2. It writes the crop choice into the planting operation for that year.
3. It writes the week's fertilizer event for that day.
4. It reruns CYCLES.
5. It advances the date by 7 days.
6. It reloads `season.dat` and `N.dat`.
7. It computes:
   - crop revenue for that week, usually `0` because harvest has not happened yet
   - negative fertilizer cost for the N/P/K that was applied
8. It returns the new observation for January 8, 2010.

So in plain English:

- the agent planned the year's crop
- applied the first week's fertilizer
- the simulator updated the farm
- the agent probably got a negative reward that week because it spent money before earning harvest income

## A Concrete Example: A Normal Mid-Season Weekly Step

Now imagine the date is:

- July 15, 2010

The policy still outputs 7 values, but the first 4 crop-planning values no longer matter for that year.

So the environment does this:

1. ignores the crop-planning part because the year is already planned
2. reads only the N/P/K part for this week
3. updates fertilizer operations if needed
4. reruns CYCLES if the operation file changed
5. advances one week
6. computes reward

This means:

- yearly crop planning happens rarely
- fertilizer control happens every week

That is why this is a multi-timescale environment.

## What Comes Back to the Agent After One Step

After one successful step, the agent gets:

1. `obs`
   - the next state
2. `reward`
   - crop revenue minus fertilizer cost for that step interval
3. `done`
   - whether the episode is finished
4. `info`
   - detailed reporting values

Important `info` fields include:

- whether planner was applied this step
- current date, year, and day-of-year
- N/P/K amounts applied
- N/P/K costs
- crop name chosen for that year
- planting day-of-year
- whether planting obeyed the calendar window
- leaching / volatilization / emission / fertilization-event counts

## What Gets Logged During Training

When hierarchical training is enabled with thesis reporting, the callback writes:

- `weekly_npk_log.csv`
- `yearly_crop_decisions.csv`
- `season_window_compliance.csv`
- `reporting_summary.json`

### Meaning of these files

#### `weekly_npk_log.csv`
One row per weekly step, including:

- date
- N/P/K applied
- cost
- reward
- whether the planner fired
- whether fertilizer was blocked outside the active crop window
- whether annual nutrient caps clipped the requested action

#### `yearly_crop_decisions.csv`
One row only when a yearly crop decision is actually applied.

It now also records whether the requested crop had to be sanitized because no defined calendar window existed for it.

#### `season_window_compliance.csv`
Tracks whether planting decisions stayed inside the configured crop calendar windows.

#### `reporting_summary.json`
Totals such as:

- total N/P/K applied
- total cost
- total yearly decisions
- compliance rate

## Why This Environment Is Hard to Learn

The hierarchical environment combines three difficult things:

1. **Two timescales**
   - yearly crop choice
   - weekly fertilizer control
2. **Delayed reward**
   - fertilizer cost happens now
   - harvest payoff may happen much later
3. **External simulator dependency**
   - every meaningful change may require a fresh CYCLES run

So the policy is not just learning "what to do this week."
It is also learning "how this week's weekly decisions interact with a crop plan chosen months earlier."

## Simple Mental Model

If you want to explain this to someone with no RL background, say:

> At the start of each year, the agent picks the crop and planting setup. Every week after that, it decides how much fertilizer to apply. Those decisions are written into the farm schedule, the CYCLES simulator runs the farm forward, and the code reads the resulting soil and season outputs. Reward is then updated as crop income minus fertilizer cost, and the next weekly state is sent back to the agent.

## One-Sentence Summary of Reset, Step, and Episode

- **Reset:** build temporary farm files, run CYCLES once, and return the starting state.
- **Step:** write this week's management decision, rerun CYCLES if needed, reload outputs, compute reward, and move one week forward.
- **Episode:** repeat weekly steps from the first day of the start year until the simulation passes the end year.

## Final Practical Note

The final March 2026 experiment matrix showed that this hierarchical branch **finished operationally** but **failed as an empirical ablation**.

So the current hierarchical environment is best understood as:

- a working technical integration of yearly crop planning plus weekly fertilization
- but not yet a successful policy formulation
- specifically, the March 11, 2026 analysis found nutrient-cost blow-up and incomplete crop-calendar coverage in the tested rotation

That is why it should be presented as a strong engineering prototype and a research direction, not as the final best-performing controller. The new guardrails are for targeted reruns only.
