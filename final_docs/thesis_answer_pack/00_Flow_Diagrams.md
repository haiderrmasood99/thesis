# 0) Overall and Detailed Flow Diagrams

## A. Overall Updated System Flow

```mermaid
flowchart LR
    A["CLI Runner (`run_all_2.py`)"] --> B["Train Script<br/>fertilization or crop planning"]
    B --> C["Env Factory (`env_maker`)"]
    C --> D["CYCLES Env (`Corn` / `CropPlanning` / `Hierarchical...`)"]
    D --> E["Action Implementers<br/>fertilizer + planting"]
    E --> F["CYCLES Simulator"]
    F --> G["Output Managers<br/>crop/season/soil/weather"]
    G --> H["Observer + Rewarder + Constrainer"]
    H --> I["SB3 Model<br/>PPO/A2C/DQN"]
    I --> J["Eval Callbacks<br/>train/test det/sto"]
    J --> K["W&B + JSONL Logs + Summary JSON/CSV"]
```

## B. Fertilization Step-Level Flow (Detailed)

```mermaid
sequenceDiagram
    participant Agent as RL Agent
    participant Env as Corn Environment
    participant Impl as Fertilizer Implementer
    participant Sim as CYCLES.exe
    participant Out as Output Managers

    Agent->>Env: step(action_idx or [N,P,K]_idx)
    Env->>Env: map discrete action -> kg/ha nutrient masses
    Env->>Impl: implement_action(date, nutrient_action)
    Impl-->>Env: rerun_cycles? (bool)
    alt operation changed or reinit boundary
        Env->>Sim: run simulation
        Sim-->>Out: write crop/season/N outputs
        Out-->>Env: parsed daily/season data
    end
    Env->>Env: date += delta (7 days)
    Env->>Env: reward = crop revenue - nutrient cost
    Env->>Env: constraints = total N, event count, leaching...
    Env-->>Agent: obs, reward, done, info
```

## C. Crop Planning + Hierarchical Decision Flow

```mermaid
flowchart TD
    A["Episode reset at Jan-01 start_year"] --> B["Year starts"]
    B --> C["High-level crop plan action (yearly)"]
    C --> D["Rotation planter writes planting ops"]
    D --> E["Weekly fertilizer actions (hierarchical) or yearly-only action (crop planning)"]
    E --> F["CYCLES rerun if operation changed"]
    F --> G["Parse season + soil outputs"]
    G --> H["Compute reward and next observation"]
    H --> I{"date.year > end_year?"}
    I -->|No| E
    I -->|Yes| J["Episode ends"]
```

## D. Full Experimentation Pipeline

```mermaid
flowchart TD
    A["Setup env + install CYCLES"] --> B["Smoke test single runs"]
    B --> C["Plan matrix (`run_all_2.py --dry-run`)"]
    C --> D["Execute matrix runs"]
    D --> E["Summaries (`runs/experiment_summaries/*.csv`)"]
    E --> F["Analyze coverage + failures"]
    F --> G["Generate thesis figures/tables"]
    G --> H["Write final report and defense claims"]
```
