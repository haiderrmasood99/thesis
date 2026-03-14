from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ChoiceOption(BaseModel):
    value: str
    label: str
    urdu_hint: str


class LocalizedText(BaseModel):
    en: str
    urdu_hint: str


class PriorFertilizer(BaseModel):
    n_kg_per_acre: float = Field(default=0.0, ge=0.0, le=250.0)
    p_kg_per_acre: float = Field(default=0.0, ge=0.0, le=250.0)
    k_kg_per_acre: float = Field(default=0.0, ge=0.0, le=250.0)


class DailyAdviceRequest(BaseModel):
    crop: Literal["maize", "soybean"]
    crop_stage: str
    land_area_acres: float = Field(..., gt=0.0, le=200.0)
    budget_pkr: float = Field(..., gt=0.0, le=5_000_000.0)
    prior_fertilizer: PriorFertilizer = Field(default_factory=PriorFertilizer)
    soil_condition: Literal["dry", "balanced", "wet"]
    recent_rain: Literal["none", "light", "moderate", "heavy"]
    expected_weather: Literal["stable", "uncertain"] = "uncertain"
    language: Literal["en", "en_pk"] = "en_pk"

    @model_validator(mode="after")
    def validate_crop_stage(self) -> "DailyAdviceRequest":
        allowed_stages = {
            "maize": {
                "pre_sowing",
                "emergence",
                "vegetative",
                "flowering",
                "grain_fill",
                "maturity",
            },
            "soybean": {
                "pre_sowing",
                "vegetative",
                "flowering",
                "pod_fill",
                "maturity",
            },
        }
        if self.crop_stage not in allowed_stages[self.crop]:
            raise ValueError(f"Unsupported crop stage '{self.crop_stage}' for crop '{self.crop}'.")
        return self


class SeasonalAdviceRequest(BaseModel):
    crop: Literal["soybean", "maize"] = "soybean"
    land_area_acres: float = Field(..., gt=0.0, le=200.0)
    budget_pkr: float = Field(..., gt=0.0, le=5_000_000.0)
    language: Literal["en", "en_pk"] = "en_pk"


class NutrientAmounts(BaseModel):
    n: float
    p: float
    k: float


class ActionCard(BaseModel):
    title: str
    status: Literal["do_now", "wait", "watch", "reference"]
    timing: str
    nutrients_per_hectare_kg: NutrientAmounts
    nutrients_per_acre_kg: NutrientAmounts
    field_total_kg: NutrientAmounts
    estimated_cost_pkr: float
    note: str


class SeasonEstimate(BaseModel):
    title: str
    nutrients_per_hectare_kg: NutrientAmounts
    nutrients_per_acre_kg: NutrientAmounts
    field_total_kg: NutrientAmounts
    estimated_cost_pkr: float
    budget_remaining_pkr: float
    budget_utilization_pct: float


class BaselineComparison(BaseModel):
    baseline_label: str
    recommended_cost_pkr: float
    baseline_cost_pkr: float
    cost_delta_pkr: float
    recommended_nutrients_per_acre_kg: NutrientAmounts
    baseline_nutrients_per_acre_kg: NutrientAmounts
    summary: str


class AdviceResponse(BaseModel):
    summary: str
    today_action: ActionCard | None
    next_steps: list[ActionCard]
    season_estimate: SeasonEstimate
    baseline_comparison: BaselineComparison | None
    warnings: list[str]
    confidence: Literal["high", "medium", "guarded", "low"]
    explanation: list[str]
    support_level: Literal["full", "light"]
    metadata: dict[str, str | int | float | bool | None]


class OptionsResponse(BaseModel):
    title: LocalizedText
    region_note: LocalizedText
    crops: list[ChoiceOption]
    maize_stages: list[ChoiceOption]
    soybean_stages: list[ChoiceOption]
    soil_conditions: list[ChoiceOption]
    recent_rain: list[ChoiceOption]
    expected_weather: list[ChoiceOption]
    languages: list[ChoiceOption]
