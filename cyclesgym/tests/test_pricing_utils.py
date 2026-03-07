import unittest

from cyclesgym.utils.pricing_utils import (
    CORN_BUSHEL_PER_TONNE,
    PAKISTAN_PRICE_DATA_PATH,
    crop_prices,
    get_price_profile,
)


class TestPricingProfiles(unittest.TestCase):
    def test_legacy_defaults_unchanged(self):
        expected = CORN_BUSHEL_PER_TONNE * 4.53
        assert abs(crop_prices['CornRM.90'][1980] - expected) < 1e-9

    def test_pakistan_profile_has_npk_prices(self):
        profile = get_price_profile('pakistan_baseline')
        nutrient_prices = profile['nutrient_prices']
        assert nutrient_prices['N'][2021] > 0
        assert nutrient_prices['P'][2021] > 0
        assert nutrient_prices['K'][2021] > 0

    def test_pakistan_profile_has_crop_prices(self):
        profile = get_price_profile('pakistan_baseline')
        prices = profile['crop_prices']
        assert prices['CornRM.90'][2021] > 0
        assert prices['SoybeanMG.3'][2009] > 0

    def test_pakistan_profile_is_year_varying(self):
        profile = get_price_profile('pakistan_baseline')
        nutrient_prices = profile['nutrient_prices']
        assert nutrient_prices['N'][2020] != nutrient_prices['N'][2021]

    def test_silage_proxy_tracks_maize_series(self):
        profile = get_price_profile('pakistan_baseline')
        prices = profile['crop_prices']
        maize = prices['CornRM.90'][2024]
        silage = prices['CornSilageRM.90'][2024]
        assert abs(silage - (0.35 * maize)) < 1e-6

    def test_pakistan_data_file_exists(self):
        assert PAKISTAN_PRICE_DATA_PATH.exists()


if __name__ == '__main__':
    unittest.main()
