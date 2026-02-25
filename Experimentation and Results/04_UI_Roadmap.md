# UI Roadmap (Next Step)

## Goal
Convert the trained policy artifacts into a lightweight decision-support interface usable by farmers or extension advisors.

## MVP Scope (4-6 weeks)

### Phase 1: Inference API
- Wrap model inference in a small backend service (`FastAPI` or `Flask`).
- Inputs:
  - Farm profile (soil type, available budget, region/weather mode)
  - Season assumptions (expected rainfall scenario)
- Outputs:
  - Recommended fertilizer schedule by week
  - Estimated cost and expected return proxy
  - Confidence/risk flag based on weather mode

### Phase 2: Lightweight Web UI
- Simple forms + result cards + timeline chart.
- Core screens:
  - Scenario input
  - Recommended plan
  - Comparison against baseline plan

### Phase 3: Validation and Guardrails
- Add basic rule constraints (budget cap, max fertilizer per week).
- Show warning when query is out-of-distribution relative to training setup.

## Suggested Tech Stack
- Backend: Python + FastAPI
- Frontend: React + Vite (or Streamlit if speed is priority)
- Storage: Local CSV/SQLite for run history
- Deployment: Docker + single VM

## Product Story for Thesis
1. Offline training creates policy.
2. UI allows farmer to enter season constraints.
3. System returns a cost-aware fertilizer/crop schedule.
4. Farmer compares recommendation with current practice and adjusts.

## What Can Be Demoed Immediately
- Read-only dashboard over existing run artifacts.
- "Replay" of top configurations with charts and summary metrics.
- Single-scenario recommendation from a selected trained checkpoint.

## What Requires Additional Experiment Work
- Full-matrix reruns for stronger reliability claims.
- Multi-seed crop planning confirmation.
- Baseline metric standardization for direct ROI comparisons.
