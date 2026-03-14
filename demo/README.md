# Farmer-First Pakistan Demo

This folder contains the new local MVP app for the thesis demo. It is separate from the archived `Local Files and Folders/demo` prototype and uses audited bundles from `artifacts/final_successful_runs`.

## What It Does

- farmer-first guided assistant for maize
- soybean seasonal reference mode with lighter-support wording
- FastAPI backend with local RL bundle inference and budget/moisture guardrails
- React + Vite frontend with English UI and Urdu hints

## Folder Layout

- `demo/backend/`: FastAPI app, bundle registry, runtime adapter, tests
- `demo/frontend/`: React + Vite SPA, Vitest tests
- `demo/docs/`: user, architecture, API, limitations, and thesis demo notes
- `demo/docs/demo-explained.md`: full technical and user-flow deep dive, combo logic, and guardrails
- `demo/start_demo.ps1`: Windows launcher for backend and frontend

## Windows Local Setup

This repo's shared `cyclesgym` environment uses Python 3.8.20, so the backend requirements are pinned to Python 3.8 compatible versions.

From the repo root:

```powershell
python -m pip install -r demo/backend/requirements.txt
cd demo/frontend
npm install
cd ../..
```

## Run Manually

Backend:

```powershell
python -m uvicorn demo.backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
cd demo/frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173).

## Run With Launcher

```powershell
.\demo\start_demo.ps1
```

This opens two PowerShell windows, one for the backend and one for the frontend.

## Alternative Backend Run

If you are already inside `demo/backend`, use:

```powershell
python run_local.py
```

This avoids the `ModuleNotFoundError: No module named 'demo'` issue that happens when `uvicorn demo.backend.app:app` is started from inside the backend folder.

## Test Commands

Backend:

```powershell
python -m pytest demo/backend/tests -q
```

Frontend:

```powershell
cd demo/frontend
npm run test
npm run build
```

## Notes

- The maize daily flow uses the audited adaptive PPO fertilization bundle from the final manifest.
- The soybean flow uses the audited hierarchical PPO report bundle and is intentionally reference-only.
- Cost display uses Pakistan baseline nutrient prices with the latest available display year from repo pricing data.
- If you are inside the conda `cyclesgym` environment, prefer `python -m pip ...` over bare `pip ...` so installs use the active interpreter.
