# 09. Legacy Markdown Mapping

This file maps prior markdown sources to the consolidated `final_docs` structure.

## Mapping: `documents/`

| Legacy File | Consolidated Destination |
|---|---|
| `documents/0_installation.md` | `01_Setup_and_First_Run.md` |
| `documents/1_introduction.md` | `00_Overview.md`, `02_Agriculture_and_RL_Fundamentals.md` |
| `documents/2_interface.md` | `03_Architecture_and_Code_Map.md` |
| `documents/3_logic.md` | `03_Architecture_and_Code_Map.md`, `04_Environment_Flows.md` |
| `documents/3.1_predefined_envs.md` | `04_Environment_Flows.md` |
| `documents/3.2_custom_weather_and_soil.md` | `04_Environment_Flows.md`, `08_Gaps_and_Future_Work.md` |
| `documents/3.3_custom_spaces_and_rewards.md` | `04_Environment_Flows.md`, `05_Training_Algorithms_and_Experimentation.md` |
| `documents/3.4_default_operations.md` | `03_Architecture_and_Code_Map.md`, `04_Environment_Flows.md` |
| `documents/4_examples.md` | `01_Setup_and_First_Run.md`, `06_Inference_Demo_and_Usage.md` |
| `documents/5_experiments.md` | `05_Training_Algorithms_and_Experimentation.md` |
| `documents/6_contributions.md` | `08_Gaps_and_Future_Work.md` |
| `documents/manual.md` | `README.md`, `00_Overview.md` |

## Mapping: `documentation/`

| Legacy File | Consolidated Destination |
|---|---|
| `documentation/01_Introduction.md` | `00_Overview.md`, `01_Setup_and_First_Run.md` |
| `documentation/02_Domain_Concepts.md` | `02_Agriculture_and_RL_Fundamentals.md` |
| `documentation/03_Architecture_and_Flows.md` | `03_Architecture_and_Code_Map.md`, `04_Environment_Flows.md` |
| `documentation/04_Code_Walkthrough.md` | `03_Architecture_and_Code_Map.md` |
| `documentation/05_Real_Life_Example.md` | `02_Agriculture_and_RL_Fundamentals.md`, `04_Environment_Flows.md` |
| `documentation/06_Training_vs_Inference.md` | `05_Training_Algorithms_and_Experimentation.md`, `06_Inference_Demo_and_Usage.md` |

## Mapping: `onboarding_docs/`

| Legacy File | Consolidated Destination |
|---|---|
| `onboarding_docs/00_Implementation_Plan.md` | `00_Overview.md` |
| `onboarding_docs/01_Repo_Overview.md` | `03_Architecture_and_Code_Map.md` |
| `onboarding_docs/02_Domain_Primer_Agriculture.md` | `02_Agriculture_and_RL_Fundamentals.md` |
| `onboarding_docs/03_Simulation_Lifecycle.md` | `03_Architecture_and_Code_Map.md`, `04_Environment_Flows.md` |
| `onboarding_docs/04_Fertilization_Env_Flow.md` | `04_Environment_Flows.md` |
| `onboarding_docs/05_Crop_Planning_Env_Flow.md` | `04_Environment_Flows.md` |
| `onboarding_docs/06_Weather_Generation_Flow.md` | `04_Environment_Flows.md` |
| `onboarding_docs/07_Data_Files_IO.md` | `03_Architecture_and_Code_Map.md` |
| `onboarding_docs/08_Training_Pipeline.md` | `05_Training_Algorithms_and_Experimentation.md` |
| `onboarding_docs/09_Training_vs_Inference_Flows.md` | `05_Training_Algorithms_and_Experimentation.md`, `06_Inference_Demo_and_Usage.md` |
| `onboarding_docs/10_Rewards_and_Economics.md` | `02_Agriculture_and_RL_Fundamentals.md`, `05_Training_Algorithms_and_Experimentation.md` |
| `onboarding_docs/11_Farmer_Usage_Guide.md` | `06_Inference_Demo_and_Usage.md` |
| `onboarding_docs/12_Resource_Allocation_Scope.md` | `00_Overview.md`, `08_Gaps_and_Future_Work.md` |
| `onboarding_docs/README.md` | `README.md` |

## Mapping: `Experimentation and Results/`

| Legacy File | Consolidated Destination |
|---|---|
| `Experimentation and Results/README.md` | `07_Thesis_Defense_Pack.md` |
| `Experimentation and Results/01_Plan_and_Feasibility.md` | `07_Thesis_Defense_Pack.md`, `08_Gaps_and_Future_Work.md` |
| `Experimentation and Results/02_Experiment_Matrix_and_Execution_Audit.md` | `05_Training_Algorithms_and_Experimentation.md`, `07_Thesis_Defense_Pack.md` |
| `Experimentation and Results/03_Results_and_Thesis_Story.md` | `07_Thesis_Defense_Pack.md` |
| `Experimentation and Results/04_UI_Roadmap.md` | `06_Inference_Demo_and_Usage.md`, `08_Gaps_and_Future_Work.md` |

## Mapping: `demo/`

| Legacy File | Consolidated Destination |
|---|---|
| `demo/README.md` | `06_Inference_Demo_and_Usage.md` |
| `demo/INSTRUCTIONS.md` | `01_Setup_and_First_Run.md`, `06_Inference_Demo_and_Usage.md` |
| `demo/THESIS_DEMO_JUSTIFICATION.md` | `06_Inference_Demo_and_Usage.md`, `07_Thesis_Defense_Pack.md` |

## Notes

1. Legacy operational docs under `demo/` and `Experimentation and Results/` are kept because they support active workflows and evidence traceability.
2. Redundant overlapping docs from `documents/`, `documentation/`, and `onboarding_docs/` were consolidated and retired from top-level navigation.
