# Simulation Lifecycle (Reset + Step)

Key entry point:
- `cyclesgym/envs/common.py` defines the base class `CyclesEnv`.
- Specific envs like `Corn` and `CropPlanning` extend it.

## Reset flow (what happens at episode start)
`CyclesEnv._common_reset()` builds a complete temporary simulation workspace and runs Cycles once.

```mermaid
sequenceDiagram
    participant RL as RL Agent
    participant Env as CyclesEnv
    participant FS as cycles/input & cycles/output
    participant Cycles as Cycles.exe

    RL->>Env: reset()
    Env->>Env: _create_io_dirs()
    Env->>FS: write control/operation/crop/soil/weather
    Env->>Cycles: run simulation (initial)
    Cycles->>FS: write output .dat files
    Env->>Env: init managers + observers + rewarders
    Env-->>RL: initial observation
```

## Step flow (what happens per action)
`Corn.step()` in `cyclesgym/envs/corn.py` is the best example to read.

```mermaid
flowchart TD
    A[Agent action] --> B[Implementer writes operation changes]
    B -->|if changed| C[Run Cycles.exe]
    C --> D[Update output managers]
    D --> E[Compute observation]
    D --> F[Compute reward]
    D --> G[Compute constraints/info]
    E --> H[Return obs, reward, done, info]
    F --> H
    G --> H
```

## Why Cycles is run during step
Cycles is an external simulator. It does not update state incrementally in memory.
So when an action changes the management plan, the env re-runs Cycles to get new outputs.

## Real-life analogy
Think of it like updating a spreadsheet model:
- You change a few input cells (fertilizer amount).
- The spreadsheet recalculates all outputs (yield, soil N).
- You then read the outputs to decide the next action.
