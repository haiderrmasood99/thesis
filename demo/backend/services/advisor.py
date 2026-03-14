from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache

from cyclesgym.utils.pricing_utils import get_nutrient_prices, lookup_year_value
from demo.backend.schemas import (
    ActionCard,
    AdviceResponse,
    BaselineComparison,
    DailyAdviceRequest,
    NutrientAmounts,
    SeasonalAdviceRequest,
    SeasonEstimate,
)
from demo.backend.services.bundles import get_curated_bundles
from demo.backend.services.runtime import EpisodeStep, NutrientVector, load_bundle_summary, run_cached_fertilization_episode

HECTARES_PER_ACRE = 0.40468564224
ACRES_PER_HECTARE = 2.47105381467

LATEST_PRICE_PROFILE = "pakistan_baseline"
PRICE_YEAR = max(get_nutrient_prices(LATEST_PRICE_PROFILE)["N"].keys())

MAIZE_STAGE_PROGRESS = {
    "pre_sowing": 0.0,
    "emergence": 0.15,
    "vegetative": 0.35,
    "flowering": 0.55,
    "grain_fill": 0.78,
    "maturity": 0.92,
}

SOYBEAN_SEASON_CAP = NutrientVector(n=60.0, p=38.0, k=32.0)
MAIZE_WEEKLY_CAP = NutrientVector(n=55.0, p=28.0, k=24.0)
MAIZE_SEASON_CAP = NutrientVector(n=180.0, p=78.0, k=65.0)
MAIZE_BASELINE_TOTAL = NutrientVector(n=135.0, p=58.0, k=42.0)
SOYBEAN_BASELINE_TOTAL = NutrientVector(n=24.0, p=30.0, k=18.0)


@dataclass(frozen=True)
class SoybeanReferenceData:
    avg_total: NutrientVector
    checkpoints: tuple[NutrientVector, NutrientVector, NutrientVector]
    compliance_rate: float
    source_years: int


def _vector_to_amounts(vector: NutrientVector) -> NutrientAmounts:
    return NutrientAmounts(n=round(vector.n, 2), p=round(vector.p, 2), k=round(vector.k, 2))


def _sum_steps(steps: list[EpisodeStep]) -> NutrientVector:
    return NutrientVector(
        n=sum(step.action.n for step in steps),
        p=sum(step.action.p for step in steps),
        k=sum(step.action.k for step in steps),
    )


def _clip_vector(vector: NutrientVector, cap: NutrientVector) -> NutrientVector:
    return NutrientVector(
        n=min(vector.n, cap.n),
        p=min(vector.p, cap.p),
        k=min(vector.k, cap.k),
    )


def _scale_vector(vector: NutrientVector, ratio: float) -> NutrientVector:
    return NutrientVector(n=vector.n * ratio, p=vector.p * ratio, k=vector.k * ratio)


def _latest_nutrient_prices() -> dict[str, float]:
    series = get_nutrient_prices(LATEST_PRICE_PROFILE)
    return {name: lookup_year_value(values, PRICE_YEAR) for name, values in series.items()}


def _estimate_cost(vector: NutrientVector) -> float:
    prices = _latest_nutrient_prices()
    return vector.n * prices["N"] + vector.p * prices["P"] + vector.k * prices["K"]


def _per_hectare_to_acre(vector: NutrientVector) -> NutrientVector:
    return NutrientVector(
        n=vector.n / ACRES_PER_HECTARE,
        p=vector.p / ACRES_PER_HECTARE,
        k=vector.k / ACRES_PER_HECTARE,
    )


def _field_total_from_per_hectare(vector: NutrientVector, acres: float) -> NutrientVector:
    hectares = acres * HECTARES_PER_ACRE
    return NutrientVector(n=vector.n * hectares, p=vector.p * hectares, k=vector.k * hectares)


def _make_action_card(
    title: str,
    status: str,
    timing: str,
    vector_per_hectare: NutrientVector,
    acres: float,
    note: str,
) -> ActionCard:
    per_acre = _per_hectare_to_acre(vector_per_hectare)
    field_total = _field_total_from_per_hectare(vector_per_hectare, acres)
    return ActionCard(
        title=title,
        status=status,
        timing=timing,
        nutrients_per_hectare_kg=_vector_to_amounts(vector_per_hectare),
        nutrients_per_acre_kg=_vector_to_amounts(per_acre),
        field_total_kg=_vector_to_amounts(field_total),
        estimated_cost_pkr=round(_estimate_cost(field_total), 2),
        note=note,
    )


def _season_estimate(
    title: str,
    vector_per_hectare: NutrientVector,
    acres: float,
    budget_remaining: float,
) -> SeasonEstimate:
    field_total = _field_total_from_per_hectare(vector_per_hectare, acres)
    estimated_cost = _estimate_cost(field_total)
    utilization = 0.0 if budget_remaining <= 0 else min((estimated_cost / budget_remaining) * 100.0, 100.0)
    return SeasonEstimate(
        title=title,
        nutrients_per_hectare_kg=_vector_to_amounts(vector_per_hectare),
        nutrients_per_acre_kg=_vector_to_amounts(_per_hectare_to_acre(vector_per_hectare)),
        field_total_kg=_vector_to_amounts(field_total),
        estimated_cost_pkr=round(estimated_cost, 2),
        budget_remaining_pkr=round(max(budget_remaining - estimated_cost, 0.0), 2),
        budget_utilization_pct=round(utilization, 2),
    )


def _comparison(
    recommended: NutrientVector,
    baseline: NutrientVector,
    acres: float,
    label: str,
) -> BaselineComparison:
    recommended_field = _field_total_from_per_hectare(recommended, acres)
    baseline_field = _field_total_from_per_hectare(baseline, acres)
    recommended_cost = _estimate_cost(recommended_field)
    baseline_cost = _estimate_cost(baseline_field)
    delta = recommended_cost - baseline_cost
    if delta < 0:
        summary = "Recommended plan stays lighter on cost than the fixed baseline."
    elif delta > 0:
        summary = "Recommended plan is costlier than the fixed baseline, but fits the chosen scenario."
    else:
        summary = "Recommended and baseline plans are cost-aligned for this scenario."
    return BaselineComparison(
        baseline_label=label,
        recommended_cost_pkr=round(recommended_cost, 2),
        baseline_cost_pkr=round(baseline_cost, 2),
        cost_delta_pkr=round(delta, 2),
        recommended_nutrients_per_acre_kg=_vector_to_amounts(_per_hectare_to_acre(recommended)),
        baseline_nutrients_per_acre_kg=_vector_to_amounts(_per_hectare_to_acre(baseline)),
        summary=summary,
    )


def _budget_remaining(request: DailyAdviceRequest) -> float:
    prior_field_total = NutrientVector(
        n=request.prior_fertilizer.n_kg_per_acre * request.land_area_acres,
        p=request.prior_fertilizer.p_kg_per_acre * request.land_area_acres,
        k=request.prior_fertilizer.k_kg_per_acre * request.land_area_acres,
    )
    return max(request.budget_pkr - _estimate_cost(prior_field_total), 0.0)


def _stage_index(crop_stage: str, total_steps: int) -> int:
    progress = MAIZE_STAGE_PROGRESS[crop_stage]
    return min(max(round((total_steps - 1) * progress), 0), max(total_steps - 1, 0))


def _apply_maize_guardrails(
    request: DailyAdviceRequest,
    today: NutrientVector,
    next_steps: list[NutrientVector],
    season_total: NutrientVector,
) -> tuple[NutrientVector, list[NutrientVector], NutrientVector, list[str], str]:
    warnings: list[str] = []
    status = "do_now"
    today = _clip_vector(today, MAIZE_WEEKLY_CAP)
    next_steps = [_clip_vector(step, MAIZE_WEEKLY_CAP) for step in next_steps]
    season_total = _clip_vector(season_total, MAIZE_SEASON_CAP)

    if request.soil_condition == "dry" and request.recent_rain in {"none", "light"}:
        warnings.append("Dry soil and low recent rain: hold fertilizer until moisture improves.")
        shifted_today = today
        today = NutrientVector(0.0, 0.0, 0.0)
        next_steps = [shifted_today, *next_steps[:1]]
        status = "wait"
    elif request.soil_condition == "wet" and request.recent_rain == "heavy":
        warnings.append("Heavy recent rain raises nutrient loss risk, so today's dose was reduced.")
        today = NutrientVector(today.n * 0.6, today.p * 0.85, today.k * 0.9)
        status = "watch"

    remaining_budget = _budget_remaining(request)
    season_cost = _estimate_cost(_field_total_from_per_hectare(season_total, request.land_area_acres))
    if remaining_budget <= 0.0:
        warnings.append("Budget is already exhausted by prior fertilizer inputs.")
        today = NutrientVector(0.0, 0.0, 0.0)
        next_steps = [_scale_vector(step, 0.0) for step in next_steps]
        season_total = NutrientVector(0.0, 0.0, 0.0)
        status = "wait"
    elif season_cost > remaining_budget:
        ratio = max(min(remaining_budget / season_cost, 1.0), 0.0)
        warnings.append("Season recommendation was scaled down to fit the remaining budget.")
        today = _scale_vector(today, ratio)
        next_steps = [_scale_vector(step, ratio) for step in next_steps]
        season_total = _scale_vector(season_total, ratio)
        if status == "do_now":
            status = "watch"

    if request.expected_weather == "uncertain":
        warnings.append("Uncertain weather uses the robust random-weather policy, so treat advice as guarded guidance.")

    return today, next_steps, season_total, warnings, status


@lru_cache(maxsize=1)
def _load_soybean_reference() -> SoybeanReferenceData:
    bundle = get_curated_bundles()["soybean_reference"]
    if not bundle.report_dir:
        raise FileNotFoundError("Soybean reference bundle is missing report data.")

    yearly_path = bundle.report_dir / "yearly_crop_decisions.csv"
    weekly_path = bundle.report_dir / "weekly_npk_log.csv"
    compliance_path = bundle.report_dir / "season_window_compliance.csv"

    soybean_years: set[int] = set()
    with yearly_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["crop_name"].lower().startswith("soybean"):
                soybean_years.add(int(row["operation_year"]))

    grouped: dict[int, list[NutrientVector]] = {year: [] for year in soybean_years}
    with weekly_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            operation_year = int(row["operation_year"])
            if operation_year not in soybean_years:
                continue
            grouped[operation_year].append(
                NutrientVector(
                    n=float(row["n_kg"]),
                    p=float(row["p_kg"]),
                    k=float(row["k_kg"]),
                )
            )

    if not grouped:
        raise ValueError("No soybean years found in hierarchical reference data.")

    totals: list[NutrientVector] = []
    early: list[NutrientVector] = []
    middle: list[NutrientVector] = []
    late: list[NutrientVector] = []
    for vectors in grouped.values():
        wrapped = [EpisodeStep(0, vector, 0.0) for vector in vectors]
        totals.append(_sum_steps(wrapped))
        split = max(len(vectors) // 3, 1)
        early.append(_sum_steps([EpisodeStep(0, vector, 0.0) for vector in vectors[:split]]))
        middle.append(_sum_steps([EpisodeStep(0, vector, 0.0) for vector in vectors[split: 2 * split] or vectors[:split]]))
        late.append(_sum_steps([EpisodeStep(0, vector, 0.0) for vector in vectors[2 * split:] or vectors[-split:]]))

    def mean_vector(values: list[NutrientVector]) -> NutrientVector:
        count = max(len(values), 1)
        return NutrientVector(
            n=sum(v.n for v in values) / count,
            p=sum(v.p for v in values) / count,
            k=sum(v.k for v in values) / count,
        )

    compliance_rate = 0.0
    with compliance_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["operation_year"] == "overall":
                compliance_rate = float(row["compliance_rate"])
                break

    return SoybeanReferenceData(
        avg_total=_clip_vector(mean_vector(totals), SOYBEAN_SEASON_CAP),
        checkpoints=(
            _clip_vector(mean_vector(early), MAIZE_WEEKLY_CAP),
            _clip_vector(mean_vector(middle), MAIZE_WEEKLY_CAP),
            _clip_vector(mean_vector(late), MAIZE_WEEKLY_CAP),
        ),
        compliance_rate=compliance_rate,
        source_years=len(grouped),
    )


def build_soybean_light_advice(request: SeasonalAdviceRequest) -> AdviceResponse:
    soybean = _load_soybean_reference()
    explanation = [
        "This view is derived from the audited hierarchical crop-planning bundle and its weekly NPK reports.",
        "Soybean guidance here is seasonal reference only, so use it to compare plans rather than to follow a daily dose blindly.",
        f"Season-window compliance in the source reference run was {soybean.compliance_rate:.0%}.",
    ]
    metadata = {
        "bundle_index": get_curated_bundles()["soybean_reference"].index,
        "source_years": soybean.source_years,
        "price_year": PRICE_YEAR,
        "compliance_rate": soybean.compliance_rate,
    }
    return AdviceResponse(
        summary="Soybean is available in light-support seasonal mode, not full daily dosing mode.",
        today_action=None,
        next_steps=[
            _make_action_card(
                title="Season start reference",
                status="reference",
                timing="Start of season",
                vector_per_hectare=soybean.checkpoints[0],
                acres=request.land_area_acres,
                note="Reference only for soybean establishment weeks.",
            ),
            _make_action_card(
                title="Mid-season reference",
                status="reference",
                timing="Mid season",
                vector_per_hectare=soybean.checkpoints[1],
                acres=request.land_area_acres,
                note="Reference only for the canopy and flowering window.",
            ),
            _make_action_card(
                title="Late-season reference",
                status="reference",
                timing="Late season",
                vector_per_hectare=soybean.checkpoints[2],
                acres=request.land_area_acres,
                note="Reference only for the late soybean window.",
            ),
        ],
        season_estimate=_season_estimate(
            title="Soybean seasonal reference",
            vector_per_hectare=soybean.avg_total,
            acres=request.land_area_acres,
            budget_remaining=request.budget_pkr,
        ),
        baseline_comparison=_comparison(
            recommended=soybean.avg_total,
            baseline=SOYBEAN_BASELINE_TOTAL,
            acres=request.land_area_acres,
            label="Fixed soybean reference schedule",
        ),
        warnings=[
            "Soybean flow is light-support only in this MVP.",
            "This app does not claim province-wide soybean calibration.",
        ],
        confidence="low",
        explanation=explanation,
        support_level="light",
        metadata=metadata,
    )


def build_daily_advice(request: DailyAdviceRequest) -> AdviceResponse:
    if request.crop == "soybean":
        return build_soybean_light_advice(
            SeasonalAdviceRequest(
                crop="soybean",
                land_area_acres=request.land_area_acres,
                budget_pkr=request.budget_pkr,
                language=request.language,
            )
        )

    bundles = get_curated_bundles()
    bundle = bundles["maize_stable"] if request.expected_weather == "stable" else bundles["maize_uncertain"]
    episode = run_cached_fertilization_episode(bundle.label, deterministic=True)
    stage_index = _stage_index(request.crop_stage, len(episode.steps))
    remaining_steps = list(episode.steps[stage_index:])
    if not remaining_steps:
        remaining_steps = list(episode.steps[-1:])

    today = remaining_steps[0].action
    next_vectors = [step.action for step in remaining_steps[1:3]]
    while len(next_vectors) < 2:
        next_vectors.append(NutrientVector(0.0, 0.0, 0.0))
    season_total = _sum_steps(remaining_steps)
    today, next_vectors, season_total, warnings, status = _apply_maize_guardrails(
        request,
        today,
        next_vectors,
        season_total,
    )

    confidence = "high"
    if status in {"wait", "watch"} or warnings:
        confidence = "guarded"
    elif request.expected_weather == "uncertain":
        confidence = "medium"

    summary = "Apply a measured NPK top-up this week."
    if status == "wait":
        summary = "Wait for better soil moisture before the next fertilizer move."
    elif status == "watch":
        summary = "Use a reduced NPK dose and watch field moisture closely."

    budget_remaining = _budget_remaining(request)
    explanation = [
        "Advice starts from the audited PPO fertilization bundle, then maps to your crop stage.",
        "Budget, soil moisture, and recent rain are used as guardrails before showing the field action.",
        f"Cost estimates use Pakistan baseline nutrient prices with {PRICE_YEAR} as the display year.",
    ]

    summary_json = load_bundle_summary(bundle)
    metadata = {
        "bundle_label": bundle.label,
        "bundle_index": bundle.index,
        "policy_method": episode.method,
        "stats_loaded": episode.stats_loaded,
        "price_year": PRICE_YEAR,
        "pak_holdout_return": float(summary_json.get("metrics", {}).get("pak_holdout_return", 0.0)),
    }

    return AdviceResponse(
        summary=summary,
        today_action=_make_action_card(
            title="Today's move",
            status=status,
            timing="This week",
            vector_per_hectare=today,
            acres=request.land_area_acres,
            note="Clamp and budget guardrails have already been applied.",
        ),
        next_steps=[
            _make_action_card(
                title="Next check-in",
                status="watch",
                timing="Next week",
                vector_per_hectare=next_vectors[0],
                acres=request.land_area_acres,
                note="Keep watching moisture before repeating the dose.",
            ),
            _make_action_card(
                title="Two weeks out",
                status="watch",
                timing="Week 3",
                vector_per_hectare=next_vectors[1],
                acres=request.land_area_acres,
                note="This is still scenario guidance, not a sensor-driven prescription.",
            ),
        ],
        season_estimate=_season_estimate(
            title="Remaining season estimate",
            vector_per_hectare=season_total,
            acres=request.land_area_acres,
            budget_remaining=budget_remaining,
        ),
        baseline_comparison=_comparison(
            recommended=season_total,
            baseline=MAIZE_BASELINE_TOTAL,
            acres=request.land_area_acres,
            label="Fixed maize demo schedule",
        ),
        warnings=warnings,
        confidence=confidence,
        explanation=explanation,
        support_level="full",
        metadata=metadata,
    )
