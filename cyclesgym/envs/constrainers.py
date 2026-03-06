from cyclesgym.envs.utils import cap_date, date2ydoy
from abc import ABC, abstractmethod
from cyclesgym.managers import SoilNManager
from typing import List
import datetime

__all__ = ['DummyConstrainer', 'LeachingConstrainer',
           'FertilizationEventConstrainer', 'TotalNitrogenConstrainer',
           'compound_constrainer']


def _parse_action_masses(action):
    """
    Parse scalar/list/dict fertilization action into aggregate masses.

    Returns
    -------
    n_mass: float
        Nitrogen mass (kg/ha)
    total_mass: float
        Total nutrient mass across N/P/K channels (kg/ha)
    """
    if action is None:
        return 0.0, 0.0

    if isinstance(action, dict):
        n_mass = float(action.get('N', 0.0))
        n_mass += float(action.get('N_NH4', 0.0))
        n_mass += float(action.get('N_NO3', 0.0))
        p_mass = float(action.get('P', 0.0)) + float(action.get('P_INORGANIC', 0.0))
        k_mass = float(action.get('K', 0.0))
        return n_mass, n_mass + p_mass + k_mass

    if hasattr(action, '__iter__') and not isinstance(action, (str, bytes)):
        arr = list(action)
        n_mass = float(arr[0]) if len(arr) > 0 else 0.0
        p_mass = float(arr[1]) if len(arr) > 1 else 0.0
        k_mass = float(arr[2]) if len(arr) > 2 else 0.0
        return n_mass, n_mass + p_mass + k_mass

    n_mass = float(action)
    return n_mass, n_mass


# TODO: Bad interface, improve
class Constrainer(ABC):
    def __init__(self):
        self.constraint_names = None
        self.n_constraints = None

    def _get_constraint_dict(self, constraint_values):
        if not hasattr(constraint_values, '__iter__'):
            constraint_values = [constraint_values]
        return {f'cost_{name}': value for name, value in
                zip(self.constraint_names, constraint_values)}

    @abstractmethod
    def compute_constraint(self, date, *args, **kwargs):
        pass


class DummyConstrainer(Constrainer):
    """
    Dummy constrained that returns an empty dictionary for compatibility.
    """
    def compute_constraint(self, date, *args, **kwargs):
        return {}



class LeachingConstrainer(Constrainer):
    def __init__(self,
                 soil_n_manager: SoilNManager,
                 end_year: int):
        self.manager = soil_n_manager
        self.end_year = end_year
        self. leaching_columns = [13,  # 'NO3 LEACHING'
                                  14,  # 'NH4 LEACHING'
                                  15,  # 'NO3 BYPASS'
                                  16]  # 'NH4 BYPASS'

        self.volatilization_coulumns = [10]  # 'NH3 VOLATILIZ'
        self.emission_columns = [9,   # N2O FROM NITRIF
                                 12]  # N2O FROM DENIT

        self.constraint_names = ['leaching', 'volatilization', 'emission']
        self.n_constraints = len(self.constraint_names)

    def compute_constraint(self, date, *args, **kwargs):
        # Make sure we did not go into not simulated year when advancing time
        date = cap_date(date, self.end_year)

        # Get data
        year, doy = date2ydoy(date)
        data = self.manager.get_day(year, doy)

        if not data.empty:
            leaching = data.iloc[0, self.leaching_columns]
            volatilization = data.iloc[0, self.volatilization_coulumns]
            emission = data.iloc[0, self.emission_columns]
            constraint_values = [sum(leaching), sum(volatilization), sum(emission)]
        else:
            # Keep interface stable when output row is unavailable
            constraint_values = [0.0, 0.0, 0.0]

        return self._get_constraint_dict(constraint_values)


class FertilizationEventConstrainer(Constrainer):
    def __init__(self):
        self.constraint_names = ['n_fertilization_events']
        self.n_constraints = len(self.constraint_names)

    def compute_constraint(self, date, action, *args, **kwargs):
        del date, args, kwargs
        _, total_mass = _parse_action_masses(action)
        constraint_values = int(total_mass > 0)
        return self._get_constraint_dict(constraint_values)


class TotalNitrogenConstrainer(Constrainer):
    def __init__(self):
        self.constraint_names = ['total_n']
        self.n_constraints = len(self.constraint_names)

    def compute_constraint(self, date, action, *args, **kwargs):
        del date, args, kwargs
        n_mass, _ = _parse_action_masses(action)
        return self._get_constraint_dict(constraint_values=n_mass)


def compound_constrainer(c_list: List[Constrainer]):

    class Compound(object):
        def __init__(self, c_list: List[Constrainer]):
            self.c_list = c_list
            self.constraint_names = None
            self.n_constraints = sum([c.n_constraints for c in c_list])

        def compute_constraint(self, date: datetime.date, **kwargs):
            # List of dicts
            list_c_dict = [c.compute_constraint(date, **kwargs) for c in self.c_list]

            # Convert to single dict
            constraints_dict = {}

            for c_dict in list_c_dict:
                constraints_dict.update(c_dict)

            # Get names
            self.constraint_names = [name for c in c_list for name in c.constraint_names]

            # TODO: Implement check we have not modified length
            # new_n_constraints = sum([o.size for o in obs])
            # if new_Nobs != self.Nobs:
            #     print(f'Warning: runtime number of observation for {self} is different then the original'
            #           f'one: Before: {self.Nobs}, runtime: {new_Nobs}')
            #     print(self.obs_list)
            # self.Nobs = new_Nobs
            return constraints_dict

    return Compound(c_list)
