from demo.backend.services.bundles import get_curated_bundles
from demo.backend.services.runtime import BundleRuntimeConfig, NutrientVector, decode_action_to_amounts


def test_decode_action_to_amounts_for_npk():
    config = BundleRuntimeConfig(
        method="PPO",
        observation_dim=14,
        start_year=2005,
        end_year=2005,
        sampling_start_year=2005,
        sampling_end_year=2023,
        fixed_weather=False,
        nonadaptive=False,
        soil_env=True,
        with_obs_year=True,
        nutrient_action_mode="NPK",
        n_actions=11,
        p_actions=11,
        k_actions=11,
        maxN=150.0,
        maxP=80.0,
        maxK=60.0,
        price_profile="pakistan_baseline",
    )
    decoded = decode_action_to_amounts([10, 5, 2], config)
    assert decoded == NutrientVector(n=150.0, p=40.0, k=12.0)


def test_curated_fertilization_bundle_has_stats():
    bundle = get_curated_bundles()["maize_uncertain"]
    assert bundle.stats_path is not None
    assert bundle.stats_path.exists()
