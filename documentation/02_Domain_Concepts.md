# 02. Agriculture Domain Concepts for Geeks

If you've never stepped on a farm, don't worry. You don't need to know how to drive a tractor. You just need to understand the **System Dynamics**.

Think of the farm as a **State Machine**.

## 🌍 The "World" (The Simulator)

The engine under the hood is **Cycles**. It is a physics-based model. It doesn't use neural networks; it uses equations derived from biology and physics to calculate:
*   How much water drains through the soil?
*   How much sunlight does the plant absorb?
*   How much biomass (plant weight) is gained today?

### Key Entities

#### 1. 🌦️ Weather
The driving force.
*   **Input**: Daily customized files containing Solar Radiation, Max/Min Temperature, and Precipitation (Rain).
*   **Impact**: Sun & Warmth = Growth. Rain = Water for roots (but too much rain washes away fertilizer!).

#### 2. 🟫 Soil
The detailed container.
*   The soil is divided into **Layers** (e.g., 0-10cm, 10-20cm... down to 2 meters).
*   Each layer holds **Water** and **Nutrients** (Nitrogen, Phosphorus).
*   **Leaching**: When water moves down past the root zone, it takes nutrients with it. This is **BAD**. It pollutes groundwater and wastes money. The AI should minimize this.

#### 3. 🌽 The Crop (The Agent's "Pet")
*   **Planting**: You must put seeds in the ground before they grow. (Some environments handle this automatically).
*   **Stages**: 
    1.  *Pre-emergence* (Seed in dirt).
    2.  *Vegetative* (Growing leaves).
    3.  *Reproductive* (Growing the corn cob).
    4.  *Maturity* (Done, ready for harvest).

## 🔁 The Simulation Loop (The "Step")

In a standard RL game, a step is often 1 frame (1/60th of a second).
In `CyclesGym`, a step is usually **7 Days**.

**Why?**
Plants grow slowly. Making a decision every minute is useless. Making a decision every day is often too granular. Weekly decisions for fertilizer allow the AI to react to weather forecasts without being overwhelmed.

1.  **State ($S_t$)**: "It rained a lot last week, soil is wet, plant is small."
2.  **Action ($A_t$)**: "Apply 50kg of Nitrogen Fertilizer."
3.  **Dynamics**: The simulator runs 7 daily steps.
    *   Day 1: Fertilizer dissolves in top soil.
    *   Day 2: Rain pushes fertilizer deeper.
    *   Day 3: Sun shines, plant roots drink water+fertilizer, plant grows 5cm.
    *   ...
4.  **Reward ($R_t$)**: (Change in Biomass) * Price - (Cost of Fertilizer).
5.  **New State ($S_{t+1}$)**: "Plant is bigger, soil is drier."

---
**Next Step**: Go to `03_Architecture_and_Flows.md` to see how we engineered this loop in Python.
