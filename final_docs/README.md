# Final Documentation Hub (`final_docs`)

This folder is the single, organized documentation set for the repository and thesis topic:

**Optimizing Agricultural Resource Allocation through Reinforcement Learning: A Cost-Driven Approach to Crop Efficiency Enhancement in Pakistan**

It is written for both:
- readers with no agriculture or RL background
- thesis reviewers who need evidence, scope boundaries, and future work

## Start Here

1. `00_Overview.md`  
   What this repo does, what it does not, and a zero-to-100 learning path.
2. `01_Setup_and_First_Run.md`  
   Install, sanity-check, first simulation, first training run, first demo run.
3. `02_Agriculture_and_RL_Fundamentals.md`  
   Plain-language domain primer plus RL concepts mapped to this codebase.
4. `03_Architecture_and_Code_Map.md`  
   End-to-end architecture, core classes, and file I/O lifecycle.
5. `04_Environment_Flows.md`  
   Fertilization and crop-planning environment internals and workflows.
6. `05_Training_Algorithms_and_Experimentation.md`  
   PPO/A2C/DQN behavior in this repo, evaluation, experiment matrix, failure modes.
7. `06_Inference_Demo_and_Usage.md`  
   Streamlit + CLI inference workflows, outputs, and deployment path.
8. `07_Thesis_Defense_Pack.md`  
   Defensible claims, evidence-backed findings, caveats, and answer patterns.
9. `08_Gaps_and_Future_Work.md`  
   Prioritized technical, agricultural, and research gaps with concrete next steps.
10. `09_Legacy_Markdown_Mapping.md`  
    Mapping of older markdown sources to new consolidated documents.
11. `legacy_markdown_archive/`  
    Archived legacy markdown trees moved from the repo root.

## Fast Paths

- New engineer path: `00` -> `01` -> `02` -> `03` -> `04` -> `05`
- Farmer/advisor path: `00` -> `02` -> `04` -> `06`
- Thesis defense path: `00` -> `05` -> `07` -> `08`

## Current Scope Summary

Implemented resource-allocation decisions:
- weekly nitrogen allocation in fertilization environments
- yearly crop-rotation choices in crop-planning environments

Not yet implemented as direct control decisions:
- irrigation scheduling
- full multi-nutrient optimization (P/K/S in active training flows)
- multi-field land allocation

## Evidence Note

This doc hub integrates prior notes from:
- legacy manuals/onboarding (`documents/`, `documentation/`, `onboarding_docs/`)
- experiment audit (`Experimentation and Results/`)
- demo usage guides (`demo/*.md`)

For traceability, see `09_Legacy_Markdown_Mapping.md`.
