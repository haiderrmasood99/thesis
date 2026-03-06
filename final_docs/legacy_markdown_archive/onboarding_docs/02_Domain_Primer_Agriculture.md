# Domain Primer: Agriculture + Simulation Basics

You do not need to be an agronomist to follow this repo. The core idea is:
we simulate crops year by year and let an RL agent make management decisions.

## Core concepts (plain language)
- Crop: the plant you grow (corn, soybean, wheat).
- Season: the growing period from planting to harvest within a year.
- Rotation: sequence of crops across years (e.g., corn then soy).
- Soil: the medium that stores water and nutrients.
- Fertilizer (N): added nitrogen to help growth (expensive and can leach).
- Weather: daily temperature, rain, radiation (drives growth).
- Yield: how much crop you harvest.
- Profit: yield value minus costs (e.g., fertilizer cost).

## Why nitrogen (N) matters
Nitrogen is like "fuel" for crop growth.
Too little = low yield. Too much = waste, cost, and environmental loss.
This is why many RL tasks in this repo choose fertilization decisions.

## Real-life analogy
Imagine you manage a greenhouse:
- You decide how much nutrient solution to add each week.
- The plant growth depends on weather (sunlight) and nutrients.
- You earn money if you harvest more, but you pay for nutrients.
Cycles is the "plant growth calculator" for that greenhouse.

## Simulation vs real world
In reality: you can't fast-forward time or run 1,000 seasons.
In simulation: you can run many seasons quickly to learn better decisions.
This is why simulators are used in RL for agriculture research.

## Agriculture terms you will see in files
- `control.ctrl`: the master configuration for a simulation run.
- `operation.operation`: management actions (planting, fertilization, irrigation).
- `weather.weather`: daily weather records.
- `soil.soil`: soil profile and properties.
- `crop.crop`: crop parameters.

If these terms feel unfamiliar, just remember:
the Python code writes these files, runs the simulator, then reads the outputs.
