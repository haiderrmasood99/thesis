# Architecture and Workflows

## End-to-End Runtime Architecture

```mermaid
flowchart LR
    Agent[SB3 policy] --> Env[cyclesgym.envs.*]
    Env --> Impl[Implementer / operation updates]
    Env --> Cycles[Cycles.exe]
    Cycles --> Out[cycles/output/<sim_id>/...]
    Out --> Managers[managers/*.py parsers]
    Managers --> Obs[Observation builders]
    Managers --> Rew[Reward logic]
    Obs --> Env
    Rew --> Env
```

## Main Components

| Area | Key Files | Responsibility |
|---|---|---|
| simulator paths | `cyclesgym/utils/paths.py` | project-root and simulator path resolution |
| fertilization env | `cyclesgym/envs/corn.py` | weekly fertilization decisions |
| crop-planning env | `cyclesgym/envs/crop_planning.py` | yearly crop decisions |
| hierarchical env | `cyclesgym/envs/hierarchical.py` | yearly planning + weekly fertilization |
| weather generation | `cyclesgym/envs/weather_generator.py` | fixed/random weather modes |
| training scripts | `experiments/fertilization/train.py`, `experiments/crop_planning/train.py` | SB3 train/eval workflow |
| matrix runners | `run_experiments_7_3_2026.py`, `run_hierarchical_guarded_parallel.py` | orchestration |

## Simulation Lifecycle

```mermaid
sequenceDiagram
    participant A as Agent
    participant E as Environment
    participant F as Filesystem
    participant C as Cycles.exe

    A->>E: reset()
    E->>F: prepare simulation files
    E->>C: run simulator
    C->>F: write outputs
    E-->>A: initial observation

    A->>E: step(action)
    E->>F: update operation/control files
    E->>C: run simulator
    C->>F: update outputs
    E->>E: parse outputs + compute reward
    E-->>A: obs, reward, done, info
```

## Reporting-Critical Design

The thesis stack deliberately preserves more than scalar reward:

- nutrient-wise costs (`N`, `P`, `K`)
- yearly crop decision traces
- compliance/report fields in `info`
- per-run summary JSON outputs

This is essential for defense interpretability.

## Geographic Defaults

Current defaults are Pakistan-oriented (weather, soil, price profiles). Claims should remain scoped to this configured simulation context.

## Current Methodological Position

Architecture is implementation-complete for the targeted thesis scope, and final comparative claims are backed by completed frozen runs (`final_113` and `final_42_ablation`).
