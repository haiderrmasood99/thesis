# Farmer-First Pakistan Demo

This folder contains the local thesis MVP demo app.

## Thesis Alignment Note

The demo showcases how audited/saved RL artifacts can be turned into a farmer-facing interface with guardrails. It does **not** change the main thesis evidence boundary:

- simulation-based only
- final frozen evidence uses completed `113` + `42` runs

## What It Does

- guided local assistant for maize and soybean reference flows
- FastAPI backend with local bundle inference + budget/moisture guardrails
- React + Vite frontend with English UI and Urdu hints

## Folder Layout

- `demo/backend/`: FastAPI app, adapter, tests
- `demo/frontend/`: React/Vite app
- `demo/docs/`: user and technical notes

## Quick Setup

```powershell
python -m pip install -r demo/backend/requirements.txt
cd demo/frontend
npm install
cd ../..
```

## Run

Backend:

```powershell
python -m uvicorn demo.backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
cd demo/frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

## Scope Reminder

Treat demo output as decision-support UX over simulation artifacts, not field-validated agronomy guidance.
