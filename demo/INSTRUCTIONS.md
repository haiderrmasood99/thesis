# Demo Instructions

## Purpose
This demo is designed for pilot/thesis presentation mode using existing trained models.

Default path: **Inference only** (no retraining required).

## What This Demo Includes
1. Streamlit UI for live fertilization inference and results replay.
2. CLI runner for scriptable inference.
3. Curated model presets aligned with best observed scenarios.
4. Thesis-facing evidence linkage to audited experiment artifacts.

## Prerequisites
1. Run commands from repository root:
   - `c:\Users\Haider\Desktop\CYCLES GYM WORKING\thesis_new\thesis`
2. Python environment with project dependencies installed.
3. Existing trained artifacts in:
   - `wandb/run-*/files/model.zip`
   - `runs/vec_normalize_*.pkl` (for fertilization normalization)

## Install Demo UI Dependencies
```powershell
pip install -r demo/requirements.txt
```

## Start Streamlit Demo
```powershell
python -m streamlit run demo/app.py
```

Alternative (PowerShell helper):
```powershell
.\demo\start_demo.ps1
```

## Run CLI Demo (No UI)
```powershell
python demo/run_demo_cli.py --preset fert_robust_random --episodes 3 --deterministic
```

### Useful CLI Flags
1. `--preset`:
   - `fert_robust_random`
   - `fert_peak_fixed`
2. `--episodes 5`
3. `--stochastic` (instead of deterministic)
4. `--start-year 2005 --end-year 2005`
5. `--weather-mode default|fixed|random`
6. `--output demo/output/my_run.json`

## Recommended Demo Flow (Thesis Defense/Pilot)
1. Open Streamlit.
2. In `Live Inference (Fertilization)` choose `fert_robust_random`.
3. Run 3 deterministic episodes first.
4. Show:
   - Mean Total Reward
   - Mean Total N (kg/ha)
   - First-episode fertilizer schedule chart
5. Switch to `Experiment Results Explorer`:
   - Show grouped fertilization and crop results.
   - Show failure signatures and matrix coverage caveat.
6. Conclude with deployment recommendation:
   - `PPO + adaptive + random_weather` for practical robustness.

## Inference vs Retraining

### Inference Mode (Current Demo)
- Uses existing `model.zip` and saved normalization stats.
- Fastest path for pilot and UI demonstration.
- No experiment rerun required.

### Retraining Required Only If
1. You change region/weather dataset (outside Pakistan setup).
2. You change reward economics (fertilizer prices/cost structure).
3. You modify observation/action design.
4. Pilot logs show policy drift or poor generalization.
5. You need full statistical thesis completeness across the planned matrix.

## Troubleshooting
1. `FileNotFoundError` for model:
   - Ensure selected preset run folder exists in `wandb/`.
2. Stats not loaded:
   - Demo can still run, but normalization mismatch may reduce reliability.
3. Slow rollout:
   - Use fewer episodes (`1-3`) for live presentation.
4. Streamlit command not found:
   - Use `python -m streamlit run demo/app.py`.
5. `ModuleNotFoundError: numpy._core` during stats load:
   - Demo now retries with a compatibility shim and can continue without stats.
   - For best consistency, keep NumPy versions aligned between training and inference environments.
6. Process exits without summary:
   - Inspect `demo/output/cli_trace.log` and `demo/output/inference_trace.log`.
   - Tracing is now written automatically by CLI.

## Files You Will Use Most
1. `demo/app.py`
2. `demo/run_demo_cli.py`
3. `demo/model_presets.json`
4. `demo/THESIS_DEMO_JUSTIFICATION.md`
