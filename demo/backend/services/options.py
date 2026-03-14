from __future__ import annotations

from demo.backend.schemas import ChoiceOption, LocalizedText, OptionsResponse


def get_options_payload() -> OptionsResponse:
    return OptionsResponse(
        title=LocalizedText(
            en="Kissan Demo Advisor",
            urdu_hint="Pakistan ke kisano ke liye demo mashwara",
        ),
        region_note=LocalizedText(
            en="Single Pakistan-context demo region with weather scenarios.",
            urdu_hint="Yeh aik single demo ilaqa hai, poori Pakistan deployment ka daawa nahin.",
        ),
        crops=[
            ChoiceOption(value="maize", label="Maize", urdu_hint="Makai"),
            ChoiceOption(value="soybean", label="Soybean", urdu_hint="Soyabean"),
        ],
        maize_stages=[
            ChoiceOption(value="pre_sowing", label="Pre-sowing", urdu_hint="Beej se pehle"),
            ChoiceOption(value="emergence", label="Emergence", urdu_hint="Nikalna shuru"),
            ChoiceOption(value="vegetative", label="Vegetative", urdu_hint="Pattay aur nashonuma"),
            ChoiceOption(value="flowering", label="Flowering", urdu_hint="Phool ka marhala"),
            ChoiceOption(value="grain_fill", label="Grain fill", urdu_hint="Dana bharna"),
            ChoiceOption(value="maturity", label="Maturity", urdu_hint="Pakkai"),
        ],
        soybean_stages=[
            ChoiceOption(value="pre_sowing", label="Pre-sowing", urdu_hint="Beej se pehle"),
            ChoiceOption(value="vegetative", label="Vegetative", urdu_hint="Nashonuma"),
            ChoiceOption(value="flowering", label="Flowering", urdu_hint="Phool ka marhala"),
            ChoiceOption(value="pod_fill", label="Pod fill", urdu_hint="Phalli bharna"),
            ChoiceOption(value="maturity", label="Maturity", urdu_hint="Pakkai"),
        ],
        soil_conditions=[
            ChoiceOption(value="dry", label="Dry", urdu_hint="Sookhi mitti"),
            ChoiceOption(value="balanced", label="Balanced", urdu_hint="Mozoon mitti"),
            ChoiceOption(value="wet", label="Wet", urdu_hint="Geeli mitti"),
        ],
        recent_rain=[
            ChoiceOption(value="none", label="No rain", urdu_hint="Barish nahin hui"),
            ChoiceOption(value="light", label="Light rain", urdu_hint="Halki barish"),
            ChoiceOption(value="moderate", label="Moderate rain", urdu_hint="Miyani barish"),
            ChoiceOption(value="heavy", label="Heavy rain", urdu_hint="Zyada barish"),
        ],
        expected_weather=[
            ChoiceOption(value="stable", label="Stable season", urdu_hint="Mustaqil mausam"),
            ChoiceOption(value="uncertain", label="Uncertain season", urdu_hint="Ghair yaqini mausam"),
        ],
        languages=[
            ChoiceOption(value="en_pk", label="English + Urdu hints", urdu_hint="English aur Urdu hints"),
            ChoiceOption(value="en", label="English only", urdu_hint="Sirf English"),
        ],
    )
