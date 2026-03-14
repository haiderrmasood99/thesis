# Architecture

## Overview

The app has two local processes:

1. FastAPI backend
2. React + Vite frontend

The backend owns artifact discovery, model/runtime loading, guardrails, and response shaping. The frontend owns the farmer-facing guided flow and result rendering.

## Artifact Sources

The backend reads from:

- `artifacts/final_successful_runs/manifest.csv`
- fertilization bundle for maize daily advice
- hierarchical report bundle for soybean seasonal reference

The archived `Local Files and Folders/demo` code is only used as a reference for environment construction patterns.

## Backend Layers

### Bundle Registry

- resolves manifest rows into absolute bundle paths
- exposes curated maize and soybean bundle selections

### Runtime Adapter

- parses `wandb/config.yaml`
- loads `model.zip`
- loads `VecNormalize` stats when available
- builds the fertilization environment from bundle config
- decodes both scalar and `MultiDiscrete` actions into NPK amounts

### Advisor Layer

- maps crop stage into a season position
- applies demo-safe weekly and seasonal nutrient caps
- applies budget, dry-soil, and heavy-rain guardrails
- returns field-ready cards and baseline comparison

## Frontend Structure

- hero and quick-start section
- guided form assistant
- result panel
- comparison card
- evidence drawer for thesis/demo use

## Why the Guardrails Exist

The underlying policy artifacts were trained in simulation and can suggest very aggressive weekly actions. The MVP clamps those outputs into a safer demo envelope before showing them to a non-technical farmer user.
