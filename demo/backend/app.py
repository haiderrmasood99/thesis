from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from demo.backend.schemas import AdviceResponse, DailyAdviceRequest, OptionsResponse, SeasonalAdviceRequest
from demo.backend.services.advisor import build_daily_advice, build_soybean_light_advice
from demo.backend.services.bundles import get_curated_bundles
from demo.backend.services.options import get_options_payload

app = FastAPI(
    title="Farmer-First Pakistan Demo API",
    version="0.1.0",
    description="Local thesis MVP backend for farmer-friendly maize advice and soybean seasonal reference.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str | int]:
    bundles = get_curated_bundles()
    return {
        "status": "ok",
        "curated_bundles": len(bundles),
    }


@app.get("/api/v1/options", response_model=OptionsResponse)
def options() -> OptionsResponse:
    return get_options_payload()


@app.post("/api/v1/advice/daily", response_model=AdviceResponse)
def daily_advice(payload: DailyAdviceRequest) -> AdviceResponse:
    return build_daily_advice(payload)


@app.post("/api/v1/advice/seasonal", response_model=AdviceResponse)
def seasonal_advice(payload: SeasonalAdviceRequest) -> AdviceResponse:
    return build_soybean_light_advice(payload)
