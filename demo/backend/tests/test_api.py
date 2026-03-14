from fastapi.testclient import TestClient

from demo.backend.app import app

client = TestClient(app)


def test_options_payload_contains_urdu_hints():
    response = client.get("/api/v1/options")
    assert response.status_code == 200
    payload = response.json()
    assert payload["crops"][0]["urdu_hint"]
    assert payload["languages"][0]["value"] == "en_pk"


def test_daily_advice_endpoint_returns_expected_shape(monkeypatch):
    from demo.backend.schemas import (
        ActionCard,
        AdviceResponse,
        BaselineComparison,
        NutrientAmounts,
        SeasonEstimate,
    )

    def fake_build_daily_advice(_payload):
        amounts = NutrientAmounts(n=10.0, p=5.0, k=3.0)
        action = ActionCard(
            title="Today's move",
            status="do_now",
            timing="This week",
            nutrients_per_hectare_kg=amounts,
            nutrients_per_acre_kg=amounts,
            field_total_kg=amounts,
            estimated_cost_pkr=1000.0,
            note="Demo",
        )
        season = SeasonEstimate(
            title="Remaining season estimate",
            nutrients_per_hectare_kg=amounts,
            nutrients_per_acre_kg=amounts,
            field_total_kg=amounts,
            estimated_cost_pkr=2000.0,
            budget_remaining_pkr=500.0,
            budget_utilization_pct=80.0,
        )
        comparison = BaselineComparison(
            baseline_label="Fixed",
            recommended_cost_pkr=2000.0,
            baseline_cost_pkr=2500.0,
            cost_delta_pkr=-500.0,
            recommended_nutrients_per_acre_kg=amounts,
            baseline_nutrients_per_acre_kg=amounts,
            summary="Demo summary",
        )
        return AdviceResponse(
            summary="Apply now.",
            today_action=action,
            next_steps=[action],
            season_estimate=season,
            baseline_comparison=comparison,
            warnings=["Watch moisture"],
            confidence="medium",
            explanation=["One", "Two"],
            support_level="full",
            metadata={"bundle_index": 3},
        )

    monkeypatch.setattr("demo.backend.app.build_daily_advice", fake_build_daily_advice)
    response = client.post(
        "/api/v1/advice/daily",
        json={
            "crop": "maize",
            "crop_stage": "vegetative",
            "land_area_acres": 4,
            "budget_pkr": 120000,
            "prior_fertilizer": {"n_kg_per_acre": 0, "p_kg_per_acre": 0, "k_kg_per_acre": 0},
            "soil_condition": "balanced",
            "recent_rain": "moderate",
            "expected_weather": "stable",
            "language": "en_pk",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["today_action"]["title"] == "Today's move"
    assert "baseline_comparison" in payload
    assert "warnings" in payload
