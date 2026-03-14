from demo.backend.schemas import DailyAdviceRequest, PriorFertilizer
from demo.backend.services.advisor import build_daily_advice


def test_soybean_daily_request_returns_light_support():
    response = build_daily_advice(
        DailyAdviceRequest(
            crop="soybean",
            crop_stage="vegetative",
            land_area_acres=5,
            budget_pkr=200000,
            prior_fertilizer=PriorFertilizer(),
            soil_condition="balanced",
            recent_rain="moderate",
            expected_weather="stable",
            language="en_pk",
        )
    )
    assert response.support_level == "light"
    assert response.today_action is None
    assert response.next_steps


def test_budget_guardrail_scales_maize_output():
    response = build_daily_advice(
        DailyAdviceRequest(
            crop="maize",
            crop_stage="vegetative",
            land_area_acres=10,
            budget_pkr=5000,
            prior_fertilizer=PriorFertilizer(),
            soil_condition="balanced",
            recent_rain="moderate",
            expected_weather="stable",
            language="en_pk",
        )
    )
    assert any("budget" in warning.lower() for warning in response.warnings)
