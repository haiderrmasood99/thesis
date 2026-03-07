from datetime import date, timedelta
from pathlib import Path
import os

import numpy as np

from cyclesgym.envs.common import CyclesEnv
from cyclesgym.envs.observers import compound_observer, SoilNObserver, NToDateObserver
from cyclesgym.envs.rewarders import (
    CropRewarder,
    NProfitabilityRewarder,
    NPKProfitabilityRewarder,
    compound_rewarder,
)
from cyclesgym.envs.implementers import RotationPlanter, FixedRateNFertilizer, FixedRateNPKFertilizer
from cyclesgym.envs.constrainers import (
    FertilizationEventConstrainer,
    TotalNitrogenConstrainer,
    LeachingConstrainer,
    compound_constrainer,
)
from cyclesgym.managers import WeatherManager, CropManager, SeasonManager, OperationManager, SoilNManager
from cyclesgym.envs.weather_generator import FixedWeatherGenerator
from cyclesgym.envs.utils import date2ydoy
from cyclesgym.utils.pakistan_crop_calendar import get_calendar_windows_for_crops
from cyclesgym.utils.pricing_utils import get_nutrient_prices, lookup_year_value
from cyclesgym.utils.paths import CYCLES_PATH
from cyclesgym.utils.gym_compat import spaces, GYMNASIUM

__all__ = ['HierarchicalCropPlanningFertilization']


class HierarchicalCropPlanningFertilization(CyclesEnv):
    """
    Single-agent hierarchical environment:
    - High-level (yearly): crop planning action (crop + planting window).
    - Low-level (weekly): fertilization action (N or NPK).

    At the first step of each year, crop planning channels are applied once;
    fertilization channels are applied every step.
    """

    def __init__(self,
                 start_year,
                 end_year,
                 rotation_crops,
                 delta=7,
                 n_actions=11,
                 maxN=150.0,
                 nutrient_action_mode='NPK',
                 maxP=80.0,
                 maxK=60.0,
                 p_actions=None,
                 k_actions=None,
                 n_nh4_rate=0.75,
                 price_profile='pakistan_baseline',
                 use_pakistan_crop_calendar=True,
                 crop_calendar_windows=None,
                 soil_file='Pakistan_Soil_final.soil',
                 weather_generator_class=FixedWeatherGenerator,
                 weather_generator_kwargs={
                     'base_weather_file': CYCLES_PATH.joinpath('input', 'Pakistan_Site_final.weather')
                 }):
        self.rotation_crops = list(rotation_crops)
        self.nutrient_action_mode = str(nutrient_action_mode).upper()
        assert self.nutrient_action_mode in ['N', 'NPK'], (
            f"nutrient_action_mode must be 'N' or 'NPK'. Got {nutrient_action_mode}"
        )

        self.maxN = float(maxN)
        self.maxP = float(maxP)
        self.maxK = float(maxK)
        self.n_actions = int(n_actions)
        self.p_actions = int(p_actions) if p_actions is not None else int(n_actions)
        self.k_actions = int(k_actions) if k_actions is not None else int(n_actions)
        self.n_nh4_rate = float(n_nh4_rate)
        self.price_profile = price_profile
        self.nutrient_prices = get_nutrient_prices(self.price_profile)

        if crop_calendar_windows is not None:
            self.crop_calendar_windows = crop_calendar_windows
        elif use_pakistan_crop_calendar:
            self.crop_calendar_windows = get_calendar_windows_for_crops(self.rotation_crops)
        else:
            self.crop_calendar_windows = {}

        self.planned_operation_years = set()
        self.planter = None
        self.fertilizer = None
        self.soil_n_file = None
        self.soil_n_manager = None

        super().__init__(
            SIMULATION_START_YEAR=start_year,
            SIMULATION_END_YEAR=end_year,
            ROTATION_SIZE=end_year - start_year + 1,
            USE_REINITIALIZATION=0,
            ADJUSTED_YIELDS=0,
            HOURLY_INFILTRATION=1,
            AUTOMATIC_NITROGEN=0,
            AUTOMATIC_PHOSPHORUS=0,
            AUTOMATIC_SULFUR=0,
            DAILY_WEATHER_OUT=0,
            DAILY_CROP_OUT=1,
            DAILY_RESIDUE_OUT=0,
            DAILY_WATER_OUT=0,
            DAILY_NITROGEN_OUT=1,
            DAILY_SOIL_CARBON_OUT=0,
            DAILY_SOIL_LYR_CN_OUT=0,
            ANNUAL_SOIL_OUT=0,
            ANNUAL_PROFILE_OUT=0,
            ANNUAL_NFLUX_OUT=0,
            CROP_FILE='GenericCrops_final.crop',
            # Overridden in _create_operation_file
            OPERATION_FILE='Pakistan_Corn_final.operation',
            SOIL_FILE=soil_file,
            WEATHER_GENERATOR_CLASS=weather_generator_class,
            WEATHER_GENERATOR_KWARGS=weather_generator_kwargs,
            REINIT_FILE='N / A',
            delta=delta,
        )

        self._init_observer()
        self._generate_observation_space()
        self._generate_action_space()
        self.constrainer = None

    def _decode_crop_action(self, crop_action):
        plan = self.planter.convert_action_to_dict(
            int(crop_action[0]),
            int(crop_action[1]),
            int(crop_action[2]),
            int(crop_action[3]),
        )
        crop_name = str(plan['CROP'])
        plant_doy = int(plan['DOY'])
        plant_end_doy = int(plan['END_DOY'])
        plant_max_smc = float(plan['MAX_SMC'])
        window = self.crop_calendar_windows.get(crop_name)
        if window is None:
            window_start_doy = None
            window_end_doy = None
            window_compliant = None
        else:
            window_start_doy = int(window[0])
            window_end_doy = int(window[1])
            window_compliant = (
                window_start_doy <= plant_doy <= window_end_doy and
                plant_doy <= plant_end_doy <= window_end_doy
            )

        return {
            'crop_name': crop_name,
            'plant_doy': plant_doy,
            'plant_end_doy': plant_end_doy,
            'plant_max_smc': plant_max_smc,
            'window_start_doy': window_start_doy,
            'window_end_doy': window_end_doy,
            'window_compliant': window_compliant,
        }

    def _nutrient_cost_breakdown(self, year: int, nutrient_action: dict):
        costs = {'N': 0.0, 'P': 0.0, 'K': 0.0}
        for nutrient in ['N', 'P', 'K']:
            series = self.nutrient_prices.get(nutrient, {})
            if not series:
                continue
            costs[nutrient] = float(nutrient_action.get(nutrient, 0.0)) * float(
                lookup_year_value(series, year)
            )
        costs['total'] = costs['N'] + costs['P'] + costs['K']
        return costs

    def _generate_action_space(self):
        n_crops = len(self.rotation_crops)
        if self.nutrient_action_mode == 'NPK':
            self.action_space = spaces.MultiDiscrete([n_crops, 14, 10, 10,
                                                      self.n_actions, self.p_actions, self.k_actions])
        else:
            self.action_space = spaces.MultiDiscrete([n_crops, 14, 10, 10, self.n_actions])

    def _generate_observation_space(self):
        self.observation_space = spaces.Box(
            low=np.array(self.observer.lower_bound, dtype=np.float32),
            high=np.array(self.observer.upper_bound, dtype=np.float32),
            shape=self.observer.lower_bound.shape,
            dtype=np.float32,
        )

    def _init_input_managers(self):
        self.weather_manager = WeatherManager(self.weather_input_file)
        self.input_managers = [self.weather_manager]
        self.input_files = [self.weather_input_file]

    def _init_output_managers(self):
        self.crop_output_file = [self._get_output_dir().joinpath(crop + '.dat') for crop in self.rotation_crops]
        self.season_file = self._get_output_dir().joinpath('season.dat')
        self.soil_n_file = self._get_output_dir().joinpath('N.dat')

        for file in self.crop_output_file:
            if not os.path.exists(file):
                with open(file, 'w'):
                    pass

        self.crop_output_manager = [CropManager(file) for file in self.crop_output_file]
        self.season_manager = SeasonManager(self.season_file)
        self.soil_n_manager = SoilNManager(self.soil_n_file)

        self.output_managers = [*self.crop_output_manager,
                                self.season_manager,
                                self.soil_n_manager]
        self.output_files = [*self.crop_output_file,
                             self.season_file,
                             self.soil_n_file]

    def _init_observer(self, *args, **kwargs):
        end_year = self.ctrl_base_manager.ctrl_dict['SIMULATION_END_YEAR']
        self.observer = compound_observer([
            SoilNObserver(soil_n_manager=self.soil_n_manager, end_year=end_year),
            NToDateObserver(end_year=end_year, with_year=True),
        ])

    def _init_rewarder(self, *args, **kwargs):
        crop_rewarders = [
            CropRewarder(self.season_manager, crop_name=name, price_profile=self.price_profile)
            for name in self.rotation_crops
        ]
        if self.nutrient_action_mode == 'NPK':
            fertilizer_rewarder = NPKProfitabilityRewarder(price_profile=self.price_profile)
        else:
            fertilizer_rewarder = NProfitabilityRewarder(price_profile=self.price_profile)
        self.rewarder = compound_rewarder([*crop_rewarders, fertilizer_rewarder])

    def _init_implementer(self, *args, **kwargs):
        self.planter = RotationPlanter(
            operation_manager=self.op_manager,
            operation_fname=self.op_file,
            rotation_crops=self.rotation_crops,
            start_year=self.ctrl_base_manager.ctrl_dict['SIMULATION_START_YEAR'],
            crop_calendar_windows=self.crop_calendar_windows,
        )
        if self.nutrient_action_mode == 'NPK':
            self.fertilizer = FixedRateNPKFertilizer(
                operation_manager=self.op_manager,
                operation_fname=self.op_file,
                n_nh4_rate=self.n_nh4_rate,
                start_year=self.ctrl_base_manager.ctrl_dict['SIMULATION_START_YEAR'],
            )
        else:
            self.fertilizer = FixedRateNFertilizer(
                operation_manager=self.op_manager,
                operation_fname=self.op_file,
                rate=self.n_nh4_rate,
                start_year=self.ctrl_base_manager.ctrl_dict['SIMULATION_START_YEAR'],
            )

    def _init_constrainer(self):
        end_year = self.ctrl_base_manager.ctrl_dict['SIMULATION_END_YEAR']
        self.constrainer = compound_constrainer([
            TotalNitrogenConstrainer(),
            FertilizationEventConstrainer(),
            LeachingConstrainer(soil_n_manager=self.soil_n_manager, end_year=end_year),
        ])

    def _create_operation_file(self):
        # Start from an empty operation file so all management is agent-driven.
        self.op_file = Path(self.input_dir.name).joinpath('operation.operation')
        open(self.op_file, 'w').close()
        self.op_manager = OperationManager(self.op_file)
        self.op_base_manager = OperationManager(self.op_file)

    @staticmethod
    def _scaled_discrete_to_mass(action: int, max_mass: float, n_bins: int) -> float:
        if n_bins <= 1:
            return 0.0
        return max_mass * float(action) / float(n_bins - 1)

    def _split_action(self, action):
        arr = np.asarray(action, dtype=np.int64).reshape(-1)
        expected = 7 if self.nutrient_action_mode == 'NPK' else 5
        assert arr.size == expected, f'Expected action size {expected}, got {arr.size}'
        crop_action = arr[:4]
        fert_action = arr[4:]
        return crop_action, fert_action

    def _fert_action_to_dict(self, fert_action):
        n_mass = self._scaled_discrete_to_mass(int(fert_action[0]), self.maxN, self.n_actions)
        if self.nutrient_action_mode == 'NPK':
            p_mass = self._scaled_discrete_to_mass(int(fert_action[1]), self.maxP, self.p_actions)
            k_mass = self._scaled_discrete_to_mass(int(fert_action[2]), self.maxK, self.k_actions)
            return {'N': n_mass, 'P': p_mass, 'K': k_mass}
        return {'N': n_mass, 'P': 0.0, 'K': 0.0}

    def step(self, action):
        action_for_check = np.asarray(action, dtype=np.int64)
        assert self.action_space.contains(action_for_check), f'{action} is not contained in the action space'
        crop_action, fert_action = self._split_action(action_for_check)
        nutrient_action = self._fert_action_to_dict(fert_action)

        action_date = self.date
        year, doy = date2ydoy(action_date)
        operation_year = self.planter.year2opyear(year)
        cost_breakdown = self._nutrient_cost_breakdown(year=year, nutrient_action=nutrient_action)

        rerun_planter = False
        planner_applied = False
        crop_decision = None
        if operation_year not in self.planned_operation_years and doy <= self.delta:
            rerun_planter = self.planter.implement_action(
                self.date,
                int(crop_action[0]),
                int(crop_action[1]),
                int(crop_action[2]),
                int(crop_action[3]),
            )
            planner_applied = True
            self.planned_operation_years.add(operation_year)
            crop_decision = self._decode_crop_action(crop_action)

        if self.nutrient_action_mode == 'NPK':
            rerun_fertilizer = self.fertilizer.implement_action(self.date, nutrient_action)
        else:
            rerun_fertilizer = self.fertilizer.implement_action(self.date, mass=nutrient_action['N'])

        if rerun_planter or rerun_fertilizer:
            self._call_cycles(debug=False)

        self.date += timedelta(days=self.delta)
        self._update_output_managers()

        done = self.date.year > self.ctrl_base_manager.ctrl_dict['SIMULATION_END_YEAR']
        reward = self.rewarder.compute_reward(date=self.date, delta=self.delta, action=nutrient_action)

        info = {
            'planner_applied': planner_applied,
            'reporting_enabled': True,
            'report_date': action_date.isoformat(),
            'report_year': int(year),
            'report_doy': int(doy),
            'report_operation_year': int(operation_year),
            'report_n_kg': float(nutrient_action['N']),
            'report_p_kg': float(nutrient_action['P']),
            'report_k_kg': float(nutrient_action['K']),
            'report_cost_n': float(cost_breakdown['N']),
            'report_cost_p': float(cost_breakdown['P']),
            'report_cost_k': float(cost_breakdown['K']),
            'report_cost_total': float(cost_breakdown['total']),
            'report_crop_index': int(crop_action[0]),
            'report_plant_week_idx': int(crop_action[1]),
            'report_plant_end_week_idx': int(crop_action[2]),
            'report_plant_max_smc_idx': int(crop_action[3]),
        }
        if crop_decision is None:
            info.update({
                'report_crop_name': None,
                'report_plant_doy': None,
                'report_plant_end_doy': None,
                'report_plant_max_smc': None,
                'report_window_start_doy': None,
                'report_window_end_doy': None,
                'report_window_compliant': None,
            })
        else:
            info.update({
                'report_crop_name': crop_decision['crop_name'],
                'report_plant_doy': int(crop_decision['plant_doy']),
                'report_plant_end_doy': int(crop_decision['plant_end_doy']),
                'report_plant_max_smc': float(crop_decision['plant_max_smc']),
                'report_window_start_doy': crop_decision['window_start_doy'],
                'report_window_end_doy': crop_decision['window_end_doy'],
                'report_window_compliant': crop_decision['window_compliant'],
            })
        info.update(self.constrainer.compute_constraint(date=self.date, action=nutrient_action))

        obs = self.observer.compute_obs(self.date, N=nutrient_action['N'])
        obs = np.asarray(obs, dtype=np.float32)

        if GYMNASIUM:
            terminated, truncated = done, False
            return obs, reward, terminated, truncated, info
        else:
            return obs, reward, done, info

    def reset(self, *, seed=None, options=None):
        self._common_reset()
        self._init_observer()
        self._init_rewarder()
        self._init_implementer()
        self._init_constrainer()
        self.planned_operation_years = set()

        rerun_cycles = self.planter.reset() or self.fertilizer.reset()
        if rerun_cycles:
            self._call_cycles(debug=False, reinit=False, doy=None)

        obs = self.observer.compute_obs(self.date, N=0.0)
        obs = np.asarray(obs, dtype=np.float32)
        return (obs, {}) if GYMNASIUM else obs
