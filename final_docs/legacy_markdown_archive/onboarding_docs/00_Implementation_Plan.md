# Implementation Plan (Fresh-Grad Onboarding)

Target reader: fresh graduate with intermediate Python and basic ML knowledge, no agriculture or simulator background.

Goals:
- Explain what this repo does, in plain language.
- Map the main flows (simulation lifecycle, fertilizer env, crop planning, training).
- Provide real-life analogies for agriculture/simulation concepts.
- Make it easy to find code entry points for deeper study.

Scope to cover:
- Core library: `cyclesgym/` (envs, managers, utils, policies)
- Simulator: `cycles/` (Cycles executable, input/output files)
- Experiments: `experiments/` (training pipelines)
- Notebooks: `notebooks/` (examples)

Deliverables (in `onboarding_docs/`):
1) Repo overview and architecture map
2) Domain primer (agri + simulation basics)
3) Simulation lifecycle (reset/step) flow
4) Fertilization environment flow
5) Crop planning environment flow
6) Weather generation flow
7) Data files and I/O map
8) Training pipeline flow (stable-baselines3 + W&B)
9) Index README to navigate everything

Process:
- Read the main env classes and managers to map data/control flow.
- Extract key file paths and responsibilities from `cyclesgym/utils/paths.py`.
- Build Mermaid diagrams for each flow.
- Add real-life analogies and a minimal "mental model" for agriculture.
- Cross-link docs and keep each file short and focused.

Success criteria:
- A new reader can explain (in their own words) how an RL action ends up changing a Cycles simulation and producing a reward.
- A new reader can find where to modify observations, rewards, and actions.
- A new reader can run or inspect the training pipeline without guessing hidden steps.
