from __future__ import annotations

from bisect import bisect_right
import json
from pathlib import Path
from typing import Dict

__all__ = [
    'CORN_BUSHEL_PER_TONNE',
    'SOYBEAN_BUSHEL_PER_TONNE',
    'N_price_dollars_per_kg',
    'crop_prices',
    'crop_type',
    'PRICE_PROFILES',
    'PAKISTAN_PRICE_DATA_PATH',
    'lookup_year_value',
    'get_price_profile',
    'get_crop_prices',
    'get_crop_type',
    'get_nutrient_prices',
]


def _constant_series(value: float, start_year: int = 1980, end_year: int = 2100) -> Dict[int, float]:
    return {y: float(value) for y in range(start_year, end_year + 1)}


def _clone_year_series_map(series_map: Dict[str, Dict[int, float]]) -> Dict[str, Dict[int, float]]:
    return {k: dict(v) for k, v in series_map.items()}


def _bag_price_to_rs_per_kg_nutrient(bag_price_rs: float, nutrient_fraction_in_product: float) -> float:
    assert nutrient_fraction_in_product > 0.0, 'Nutrient fraction must be > 0'
    return bag_price_rs / (50.0 * nutrient_fraction_in_product)


def lookup_year_value(year_to_value: Dict[int, float], year: int) -> float:
    """
    Return value for `year`, falling back to nearest available historical year.
    """
    if year in year_to_value:
        return year_to_value[year]
    years = sorted(year_to_value.keys())
    if not years:
        raise KeyError('Price dictionary is empty')
    idx = bisect_right(years, year) - 1
    if idx < 0:
        return year_to_value[years[0]]
    return year_to_value[years[idx]]


def _load_int_key_series(d: dict) -> Dict[int, float]:
    out: Dict[int, float] = {}
    for k, v in d.items():
        out[int(k)] = float(v)
    return out


def _load_pakistan_series_from_file(path: Path):
    payload = json.loads(path.read_text(encoding='utf-8'))
    crops = payload['crop_prices_lcu_per_tonne']
    nutrients = payload['nutrient_prices_rs_per_kg']
    return (
        _load_int_key_series(crops['maize']),
        _load_int_key_series(crops['soybeans']),
        _load_int_key_series(crops['maize_silage_proxy']),
        {
            'N': _load_int_key_series(nutrients['N']),
            'P': _load_int_key_series(nutrients['P']),
            'K': _load_int_key_series(nutrients['K']),
        },
    )


# Conversion rate for corn from bushel to metric ton from
# https://grains.org/markets-tools-data/tools/converting-grain-units/
CORN_BUSHEL_PER_TONNE = 39.3680
SOYBEAN_BUSHEL_PER_TONNE = 36.7437

# ---------------------------------------------------------------------------
# Legacy US profile (backward compatible default behavior)
# ---------------------------------------------------------------------------
# Avg anhydrous ammonia cost in 2020 from
# https://farmdocdaily.illinois.edu/2021/08/2021-fertilizer-price-increases-in-perspective-with-implications-for-2022-costs.html
# Computed as 496 * 0.001 ($/ton * ton/kg)
_US_N_PRICE_DOLLARS_PER_KG = {y: 496 * 0.001 for y in range(1980, 2020)}

# Avg US price of corn for 2020 from
# https://quickstats.nass.usda.gov/results/BA8CCB81-A2BB-3C5C-BD23-DBAC365C7832
_US_CORN_PRICE_DOLLARS_PER_BUSHEL = {y: 4.53 for y in range(1980, 2020)}
_US_CORN_PRICE_DOLLARS_PER_TONNE = {
    y: CORN_BUSHEL_PER_TONNE * _US_CORN_PRICE_DOLLARS_PER_BUSHEL[y]
    for y in _US_CORN_PRICE_DOLLARS_PER_BUSHEL.keys()
}

# US price of corn silage (forage) in 1970 (not available more recently)
# https://quickstats.nass.usda.gov/results/6C3AADDF-25D2-31E7-9E0A-F050F345F91D
# https://beef.unl.edu/beefwatch/2020/corn-crop-worth-more-silage-or-grain
_US_CORN_SILAGE_PRICE_DOLLARS_PER_TONNE = {y: 10 for y in range(1980, 2020)}

# Avg US price of soybean for 2020 from
# https://quickstats.nass.usda.gov/results/1A09097A-EFA4-3C47-B1D4-E7ACDFAA2575
_US_SOY_BEANS_PRICE_DOLLARS_PER_BUSHEL = {y: 9.89 for y in range(1980, 2020)}
_US_SOY_BEANS_PRICE_DOLLARS_PER_TONNE = {
    y: SOYBEAN_BUSHEL_PER_TONNE * _US_SOY_BEANS_PRICE_DOLLARS_PER_BUSHEL[y]
    for y in _US_SOY_BEANS_PRICE_DOLLARS_PER_BUSHEL.keys()
}

_US_CROP_PRICES = {
    'CornRM.90': _US_CORN_PRICE_DOLLARS_PER_TONNE,
    'CornRM.100': _US_CORN_PRICE_DOLLARS_PER_TONNE,
    'SoybeanMG.5': _US_SOY_BEANS_PRICE_DOLLARS_PER_TONNE,
    'SoybeanMG.3': _US_SOY_BEANS_PRICE_DOLLARS_PER_TONNE,
    'CornSilageRM.90': _US_CORN_SILAGE_PRICE_DOLLARS_PER_TONNE,
}

_DEFAULT_CROP_TYPE = {
    'CornRM.90': 'GRAIN YIELD',
    'CornRM.100': 'GRAIN YIELD',
    'CornSilageRM.90': 'FORAGE YIELD',
    'SoybeanMG.5': 'GRAIN YIELD',
    'SoybeanMG.3': 'GRAIN YIELD',
}

_US_NUTRIENT_PRICES = {
    'N': _US_N_PRICE_DOLLARS_PER_KG,
    'P': _constant_series(0.0, start_year=1980, end_year=2100),
    'K': _constant_series(0.0, start_year=1980, end_year=2100),
}

# ---------------------------------------------------------------------------
# Pakistan baseline profile (opt-in; year-varying)
# ---------------------------------------------------------------------------
PAKISTAN_PRICE_DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / 'resources'
    / 'pricing'
    / 'pakistan_yearly_series.json'
)

try:
    (
        _PAK_MAIZE_PRICE_RUPEES_PER_TONNE,
        _PAK_SOY_BEANS_PRICE_RUPEES_PER_TONNE,
        _PAK_CORN_SILAGE_PRICE_RUPEES_PER_TONNE,
        _PAK_NUTRIENT_PRICES,
    ) = _load_pakistan_series_from_file(PAKISTAN_PRICE_DATA_PATH)
except Exception:
    # Fallback keeps runtime stable even when external data file is unavailable.
    _PAK_MAIZE_PRICE_RUPEES_PER_TONNE = {
        2005: 10115.0,
        2006: 11000.0,
        2007: 11500.0,
        2008: 11800.0,
        2009: 17824.0,
        2010: 19504.0,
        2020: 39293.4,
        2021: 45853.9,
        2022: 69412.8,
        2023: 62974.0,
        2024: 63679.5,
    }
    _PAK_SOY_BEANS_PRICE_RUPEES_PER_TONNE = {
        2005: 20000.0,
        2006: 24000.0,
        2007: 25500.0,
        2008: 26000.0,
        2009: 32060.0,
        2010: 35430.0,
    }
    _PAK_CORN_SILAGE_PRICE_RUPEES_PER_TONNE = {
        y: _PAK_MAIZE_PRICE_RUPEES_PER_TONNE[y] * 0.35
        for y in _PAK_MAIZE_PRICE_RUPEES_PER_TONNE.keys()
    }
    _PAK_RS_PER_50KG_BAG_2021_22 = {
        'urea': 1913.0,
        'dap_18_46': 8227.0,
        'sop': 7727.0,
    }
    _P2O5_TO_P = 0.4364
    _K2O_TO_K = 0.8301
    _PAK_NPK_RS_PER_KG_2021_22 = {
        'N': _bag_price_to_rs_per_kg_nutrient(_PAK_RS_PER_50KG_BAG_2021_22['urea'], 0.46),
        'P': _bag_price_to_rs_per_kg_nutrient(_PAK_RS_PER_50KG_BAG_2021_22['dap_18_46'], 0.46 * _P2O5_TO_P),
        'K': _bag_price_to_rs_per_kg_nutrient(_PAK_RS_PER_50KG_BAG_2021_22['sop'], 0.50 * _K2O_TO_K),
    }
    _PAK_NUTRIENT_PRICES = {
        n: _constant_series(v, start_year=1980, end_year=2100)
        for n, v in _PAK_NPK_RS_PER_KG_2021_22.items()
    }


_PAK_CROP_PRICES = {
    'CornRM.90': _PAK_MAIZE_PRICE_RUPEES_PER_TONNE,
    'CornRM.100': _PAK_MAIZE_PRICE_RUPEES_PER_TONNE,
    'SoybeanMG.5': _PAK_SOY_BEANS_PRICE_RUPEES_PER_TONNE,
    'SoybeanMG.3': _PAK_SOY_BEANS_PRICE_RUPEES_PER_TONNE,
    'CornSilageRM.90': _PAK_CORN_SILAGE_PRICE_RUPEES_PER_TONNE,
}


PRICE_PROFILES = {
    'us_legacy': {
        'crop_prices': _US_CROP_PRICES,
        'crop_type': _DEFAULT_CROP_TYPE,
        'nutrient_prices': _US_NUTRIENT_PRICES,
    },
    'pakistan_baseline': {
        'crop_prices': _PAK_CROP_PRICES,
        'crop_type': _DEFAULT_CROP_TYPE,
        'nutrient_prices': _PAK_NUTRIENT_PRICES,
    },
}


def get_price_profile(profile_name: str = 'us_legacy') -> Dict[str, Dict]:
    assert profile_name in PRICE_PROFILES, (
        f'Unknown price profile {profile_name}. Available: {list(PRICE_PROFILES.keys())}'
    )
    profile = PRICE_PROFILES[profile_name]
    return {
        'crop_prices': _clone_year_series_map(profile['crop_prices']),
        'crop_type': dict(profile['crop_type']),
        'nutrient_prices': _clone_year_series_map(profile['nutrient_prices']),
    }


def get_crop_prices(profile_name: str = 'us_legacy') -> Dict[str, Dict[int, float]]:
    return get_price_profile(profile_name)['crop_prices']


def get_crop_type(profile_name: str = 'us_legacy') -> Dict[str, str]:
    return get_price_profile(profile_name)['crop_type']


def get_nutrient_prices(profile_name: str = 'us_legacy') -> Dict[str, Dict[int, float]]:
    return get_price_profile(profile_name)['nutrient_prices']


# Backward-compatible exports (legacy US profile by default).
crop_prices = get_crop_prices('us_legacy')
crop_type = get_crop_type('us_legacy')
N_price_dollars_per_kg = get_nutrient_prices('us_legacy')['N']
