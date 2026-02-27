# Demo Folder

This folder contains an inference-first demo for the thesis project:

"Optimizing Agricultural Resource Allocation through Reinforcement Learning: A Cost-Driven Approach to Crop Efficiency Enhancement."

## Contents
- `app.py`: Streamlit UI for pilot/demo usage.
- `run_demo_cli.py`: Terminal-only inference runner.
- `inference_engine.py`: Shared inference logic.
- `model_presets.json`: Curated model presets from audited runs.
- `INSTRUCTIONS.md`: Detailed setup and usage guide.
- `THESIS_DEMO_JUSTIFICATION.md`: Thesis-facing explanation of how the demo supports the problem statement.
- `requirements.txt`: Extra dependencies for the demo UI.
- `start_demo.ps1`: Convenience launcher for Windows PowerShell.

## Quick Start
From repository root:

```powershell
python -m streamlit run demo/app.py
```

Or terminal demo:

```powershell
python demo/run_demo_cli.py --preset fert_robust_random --episodes 3 --deterministic
```
