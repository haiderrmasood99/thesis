from datetime import timedelta
from cyclesgym.envs.utils import date2ydoy, ydoy2date
from cyclesgym.utils.pricing_utils import (
    N_price_dollars_per_kg as legacy_n_price_dollars_per_kg,
    get_price_profile,
)
import datetime
from bisect import bisect_right

__all__ = ['CropRewarder', 'NProfitabilityRewarder',
           'NPKProfitabilityRewarder', 'compound_rewarder']


def _lookup_year_value(year_to_value: dict, year: int):
    """Return value for year, falling back to nearest available historical year."""
    if year in year_to_value:
        return year_to_value[year]
    years = sorted(year_to_value.keys())
    if not years:
        raise KeyError("Price dictionary is empty")
    idx = bisect_right(years, year) - 1
    if idx < 0:
        return year_to_value[years[0]]
    return year_to_value[years[idx]]


def _parse_npk_action(action) -> dict:
    """
    Parse scalar/list/dict action into nutrient masses (kg/ha).

    Supported action formats:
    - scalar: interpreted as N only
    - [N], [N, P], [N, P, K]
    - {'N': ..., 'P': ..., 'K': ...}
    - {'N_NH4': ..., 'N_NO3': ..., 'P_INORGANIC': ..., 'K': ...}
    """
    masses = {'N': 0.0, 'P': 0.0, 'K': 0.0}

    if action is None:
        return masses

    if isinstance(action, dict):
        n = float(action.get('N', 0.0))
        n += float(action.get('N_NH4', 0.0))
        n += float(action.get('N_NO3', 0.0))
        p = float(action.get('P', 0.0))
        p += float(action.get('P_INORGANIC', 0.0))
        k = float(action.get('K', 0.0))
        masses.update({'N': n, 'P': p, 'K': k})
        return masses

    if hasattr(action, '__iter__') and not isinstance(action, (str, bytes)):
        arr = list(action)
        if len(arr) >= 1:
            masses['N'] = float(arr[0])
        if len(arr) >= 2:
            masses['P'] = float(arr[1])
        if len(arr) >= 3:
            masses['K'] = float(arr[2])
        return masses

    masses['N'] = float(action)
    return masses


class CropRewarder(object):

    def __init__(self, season_manager, crop_name, price_profile: str = 'us_legacy',
                 crop_prices_map: dict = None, crop_type_map: dict = None):
        self.season_manager = season_manager
        self.crop_name = crop_name
        if crop_prices_map is None or crop_type_map is None:
            profile = get_price_profile(price_profile)
            if crop_prices_map is None:
                crop_prices_map = profile['crop_prices']
            if crop_type_map is None:
                crop_type_map = profile['crop_type']

        self.dollars_per_tonne = crop_prices_map[self.crop_name]
        self.yield_column = crop_type_map[self.crop_name]

    def _harvest_profit(self, date, delta, action=None):
        # Date of previous time step
        del action

        previous_date = date - timedelta(days=delta)
        y_prev, doy_prev = date2ydoy(previous_date)

        # Did we harvest between this and previous time step?
        df = self.season_manager.season_df
        harverst_df = df.loc[(df['YEAR'] == y_prev) & (df['CROP'] == self.crop_name)]
        harvest_dollars_per_hectare = 0
        if not harverst_df.empty:
            harverst_doy = harverst_df.iloc[0]['DOY']
            harvest_date = ydoy2date(y_prev, harverst_doy)

            if previous_date < harvest_date <= date:
                # Compute harvest profit
                dollars_per_tonne = _lookup_year_value(self.dollars_per_tonne, y_prev)
                harvest = harverst_df[self.yield_column].sum()
                # Metric tonne per hectare
                harvest_dollars_per_hectare = harvest * dollars_per_tonne
        return harvest_dollars_per_hectare
    
    def compute_reward(self, date, delta, action=None):
        return self._harvest_profit(date, delta, action=action)


class NProfitabilityRewarder(object):
    def __init__(self, n_price_per_kg: dict = None, price_profile: str = 'us_legacy'):
        if n_price_per_kg is None:
            if price_profile == 'us_legacy':
                n_price_per_kg = legacy_n_price_dollars_per_kg
            else:
                profile = get_price_profile(price_profile)
                n_price_per_kg = profile['nutrient_prices']['N']
        self.n_price_per_kg = n_price_per_kg

    def compute_reward(self, date, delta, action=None):
        del delta
        Nkg_per_heactare = _parse_npk_action(action)['N']
        assert Nkg_per_heactare >= 0, 'We cannot have negative fertilization'
        y, doy = date2ydoy(date)
        del doy
        N_dollars_per_hectare = Nkg_per_heactare * _lookup_year_value(self.n_price_per_kg, y)
        return -N_dollars_per_hectare


class NPKProfitabilityRewarder(object):
    def __init__(self, nutrient_price_per_kg: dict = None, price_profile: str = 'us_legacy'):
        if nutrient_price_per_kg is None:
            nutrient_price_per_kg = get_price_profile(price_profile)['nutrient_prices']

        self.nutrient_price_per_kg = {
            'N': nutrient_price_per_kg.get('N', {}),
            'P': nutrient_price_per_kg.get('P', {}),
            'K': nutrient_price_per_kg.get('K', {}),
        }

    def compute_reward(self, date, delta, action=None):
        del delta
        masses = _parse_npk_action(action)
        assert masses['N'] >= 0, 'We cannot have negative N fertilization'
        assert masses['P'] >= 0, 'We cannot have negative P fertilization'
        assert masses['K'] >= 0, 'We cannot have negative K fertilization'

        y, doy = date2ydoy(date)
        del doy
        total_cost = 0.0
        for nutrient, mass in masses.items():
            price_series = self.nutrient_price_per_kg[nutrient]
            if not price_series:
                continue
            total_cost += mass * _lookup_year_value(price_series, y)
        return -total_cost


def compound_rewarder(rewarder_list: list):

    class Compound(object):
        def __init__(self, rewarder_list):
            self.rewarder_list = rewarder_list

        def compute_reward(self, date: datetime.date, delta, action=None):
            return sum([r.compute_reward(date, delta, action=action) for r in self.rewarder_list])

    return Compound(rewarder_list)
