from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = Path(__file__).resolve().parent
ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts" / "final_successful_runs"
MANIFEST_PATH = ARTIFACTS_ROOT / "manifest.csv"

PRIMARY_MAIZE_LABEL = "Fertilization | PPO | adaptive | random_weather | years=1000 | seed=0"
STABLE_MAIZE_LABEL = "Fertilization | PPO | adaptive | fixed_weather | years=1000 | seed=0"
SOYBEAN_REFERENCE_LABEL = "Crop planning hierarchical | PPO | fixed_weather | seed=0 | profile=pakistan_baseline"

API_HOST = "127.0.0.1"
API_PORT = 8000
