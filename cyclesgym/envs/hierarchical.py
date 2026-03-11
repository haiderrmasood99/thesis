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
                 enforce_calendar_windows=True,
                 limit_fertilizer_to_season=True,
                 preplant_fertilizer_days=14,
                 postplant_fertilizer_days=120,
                 annual_n_budget=None,
                 annual_p_budget=None,
                 annual_k_budget=None,
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
        self.use_pakistan_crop_calendar = bool(use_pakistan_crop_calendar)
        self.enforce_calendar_windows = bool(enforce_calendar_windows)
        self.limit_fertilizer_to_season = bool(limit_fertilizer_to_season)
        self.preplant_fertilizer_days = max(0, int(preplant_fertilizer_days))
        self.postplant_fertilizer_days = max(0, int(postplant_fertilizer_days))

        if crop_calendar_windows is not None:
            self.crop_calendar_windows = crop_calendar_windows
        elif use_pakistan_crop_calendar:
            self.crop_calendar_windows = get_calendar_windows_for_crops(self.rotation_crops)
        else:
            self.crop_calendar_windows = {}
        self.enforce_calendar_windows = self.enforce_calendar_windows and bool(self.crop_calendar_windows)
        self.calendar_valid_crop_indices = [
            idx for idx, crop in enumerate(self.rotation_crops)
            if crop in self.crop_calendar_windows
        ]
        self.default_calendar_crop_index = (
            int(self.calendar_valid_crop_indices[0]) if self.calendar_valid_crop_indices else None
        )
        self.annual_nutrient_budgets = {
            'N': self._resolve_budget(annual_n_budget, self.maxN),
            'P': self._resolve_budget(annual_p_budget, self.maxP),
            'K': self._resolve_budget(annual_k_budget, self.maxK),
        }

        self.planned_operation_years = set()
        self.crop_decisions_by_operation_year = {}
        self.nutrient_usage_by_operation_year = {}
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

    @staticmethod
    def _resolve_budget(configured_budget, fallback_budget: float) -> float:
        if configured_budget is None:
            return float(max(0.0, fallback_budget))
        return float(max(0.0, configured_budget))

    @staticmethod
    def _zero_nutrient_action() -> dict:
        return {'N': 0.0, 'P': 0.0, 'K': 0.0}

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

    def _sanitize_crop_action(self, crop_action):
        sanitized_action = np.asarray(crop_action, dtype=np.int64).copy()
        requested_crop_index = int(sanitized_action[0])
        requested_crop_name = str(self.rotation_crops[requested_crop_index])

        effective_crop_index = requested_crop_index
        crop_action_sanitized = False
        crop_sanitization_reason = None
        fallback_crop_name = None

        if self.enforce_calendar_windows and requested_crop_name not in self.crop_calendar_windows:
            crop_sanitization_reason = 'undefined_crop_window'
            if self.default_calendar_crop_index is not None:
                effective_crop_index = int(self.default_calendar_crop_index)
                sanitized_action[0] = effective_crop_index
                crop_action_sanitized = (effective_crop_index != requested_crop_index)
                fallback_crop_name = str(self.rotation_crops[effective_crop_index])
            else:
                crop_sanitization_reason = 'no_defined_calendar_crop_available'

        return sanitized_action, {
            'requested_crop_index': requested_crop_index,
            'requested_crop_name': requested_crop_name,
            'effective_crop_index': int(effective_crop_index),
            'effective_crop_name': str(self.rotation_crops[effective_crop_index]),
            'crop_action_sanitized': bool(crop_action_sanitized),
            'crop_sanitization_reason': crop_sanitization_reason,
            'fallback_crop_name': fallback_crop_name,
            'effective_crop_has_window': bool(
                str(self.rotation_crops[effective_crop_index]) in self.crop_calendar_windows
            ),
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

    def _ensure_usage_row(self, operation_year: int):
        return self.nutrient_usage_by_operation_year.setdefault(
            int(operation_year),
            {'N': 0.0, 'P': 0.0, 'K': 0.0},
        )

    def _remaining_budget(self, operation_year: int) -> dict:
        usage = self._ensure_usage_row(operation_year)
        return {
            nutrient: max(0.0, float(self.annual_nutrient_budgets[nutrient]) - float(usage.get(nutrient, 0.0)))
            for nutrient in ['N', 'P', 'K']
        }

    def _register_nutrient_usage(self, operation_year: int, nutrient_action: dict):
        usage = self._ensure_usage_row(operation_year)
        for nutrient in ['N', 'P', 'K']:
            usage[nutrient] = float(usage.get(nutrient, 0.0)) + float(nutrient_action.get(nutrient, 0.0))

    def _fertilizer_window_segments(self, crop_decision: dict) -> list[dict]:
        if crop_decision is None:
            return []
        start_doy = int(crop_decision['plant_doy']) - self.preplant_fertilizer_days
        end_doy = int(crop_decision['plant_end_doy']) + self.postplant_fertilizer_days
        segments: list[dict] = []

        same_year_start = max(1, start_doy)
        same_year_end = min(366, end_doy)
        if same_year_start <= same_year_end:
            segments.append({
                'operation_year_offset': 0,
                'window_start_doy': int(same_year_start),
                'window_end_doy': int(same_year_end),
            })

        if end_doy > 366:
            segments.append({
                'operation_year_offset': 1,
                'window_start_doy': 1,
                'window_end_doy': int(min(366, end_doy - 366)),
            })

        return segments

    def _active_crop_context(self, operation_year: int, doy: int):
        for source_operation_year, relation in (
            (int(operation_year) - 1, 'carryover'),
            (int(operation_year), 'current'),
        ):
            crop_decision = self.crop_decisions_by_operation_year.get(source_operation_year)
            if crop_decision is None:
                continue
            for segment in self._fertilizer_window_segments(crop_decision):
                target_operation_year = source_operation_year + int(segment['operation_year_offset'])
                if target_operation_year != int(operation_year):
                    continue
                if int(segment['window_start_doy']) <= int(doy) <= int(segment['window_end_doy']):
                    context = dict(crop_decision)
                    context.update({
                        'source_operation_year': int(source_operation_year),
                        'window_start_doy': int(segment['window_start_doy']),
                        'window_end_doy': int(segment['window_end_doy']),
                        'window_relation': relation,
                    })
                    return context
        return None

    def _apply_fertilizer_guardrails(self, requested_nutrient_action: dict, operation_year: int, doy: int):
        active_crop_context = self._active_crop_context(operation_year=operation_year, doy=doy)
        budget_operation_year = int(operation_year)
        if active_crop_context is not None:
            budget_operation_year = int(active_crop_context['source_operation_year'])

        remaining_before = self._remaining_budget(budget_operation_year)
        applied_nutrient_action = {
            nutrient: float(requested_nutrient_action.get(nutrient, 0.0))
            for nutrient in ['N', 'P', 'K']
        }
        fertilizer_window_open = True
        budget_clipped = False
        gate_reason = None

        if self.limit_fertilizer_to_season and active_crop_context is None:
            fertilizer_window_open = False
            gate_reason = 'outside_active_crop_window'
            applied_nutrient_action = self._zero_nutrient_action()
            return applied_nutrient_action, {
                'active_crop_context': None,
                'budget_operation_year': budget_operation_year,
                'fertilizer_window_open': fertilizer_window_open,
                'budget_clipped': False,
                'gate_reason': gate_reason,
                'remaining_before': remaining_before,
                'remaining_after': remaining_before,
            }

        for nutrient in ['N', 'P', 'K']:
            requested_mass = float(requested_nutrient_action.get(nutrient, 0.0))
            allowed_mass = float(remaining_before.get(nutrient, 0.0))
            applied_mass = min(requested_mass, allowed_mass)
            if applied_mass + 1e-9 < requested_mass:
                budget_clipped = True
            applied_nutrient_action[nutrient] = applied_mass

        if any(float(applied_nutrient_action[n]) > 0.0 for n in ['N', 'P', 'K']):
            self._register_nutrient_usage(budget_operation_year, applied_nutrient_action)

        remaining_after = self._remaining_budget(budget_operation_year)
        if gate_reason is None:
            if budget_clipped:
                gate_reason = 'annual_budget_clipped'
            elif not any(float(requested_nutrient_action[n]) > 0.0 for n in ['N', 'P', 'K']):
                gate_reason = 'agent_requested_zero'
            else:
                gate_reason = 'applied'

        return applied_nutrient_action, {
            'active_crop_context': active_crop_context,
            'budget_operation_year': budget_operation_year,
            'fertilizer_window_open': fertilizer_window_open,
            'budget_clipped': budget_clipped,
            'gate_reason': gate_reason,
            'remaining_before': remaining_before,
            'remaining_after': remaining_after,
        }

    def step(self, action):
        action_for_check = np.asarray(action, dtype=np.int64)
        assert self.action_space.contains(action_for_check), f'{action} is not contained in the action space'
        crop_action_raw, fert_action = self._split_action(action_for_check)
        crop_action, crop_action_meta = self._sanitize_crop_action(crop_action_raw)
        requested_nutrient_action = self._fert_action_to_dict(fert_action)

        action_date = self.date
        year, doy = date2ydoy(action_date)
        operation_year = self.planter.year2opyear(year)

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
            crop_decision.update(crop_action_meta)
            self.crop_decisions_by_operation_year[int(operation_year)] = dict(crop_decision)
            self._ensure_usage_row(int(operation_year))

        nutrient_action, fert_guardrails = self._apply_fertilizer_guardrails(
            requested_nutrient_action=requested_nutrient_action,
            operation_year=operation_year,
            doy=doy,
        )
        cost_breakdown = self._nutrient_cost_breakdown(year=year, nutrient_action=nutrient_action)

        rerun_fertilizer = False
        if any(float(nutrient_action[n]) > 0.0 for n in ['N', 'P', 'K']):
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
            'report_requested_n_kg': float(requested_nutrient_action['N']),
            'report_requested_p_kg': float(requested_nutrient_action['P']),
            'report_requested_k_kg': float(requested_nutrient_action['K']),
            'report_n_kg': float(nutrient_action['N']),
            'report_p_kg': float(nutrient_action['P']),
            'report_k_kg': float(nutrient_action['K']),
            'report_cost_n': float(cost_breakdown['N']),
            'report_cost_p': float(cost_breakdown['P']),
            'report_cost_k': float(cost_breakdown['K']),
            'report_cost_total': float(cost_breakdown['total']),
            'report_requested_crop_index': int(crop_action_meta['requested_crop_index']),
            'report_requested_crop_name': crop_action_meta['requested_crop_name'],
            'report_crop_index': int(crop_action_meta['effective_crop_index']),
            'report_plant_week_idx': int(crop_action[1]),
            'report_plant_end_week_idx': int(crop_action[2]),
            'report_plant_max_smc_idx': int(crop_action[3]),
            'report_crop_action_sanitized': bool(planner_applied and crop_action_meta['crop_action_sanitized']),
            'report_crop_sanitization_reason': (
                crop_action_meta['crop_sanitization_reason'] if planner_applied else None
            ),
            'report_fallback_crop_name': crop_action_meta['fallback_crop_name'] if planner_applied else None,
            'report_fertilizer_window_open': bool(fert_guardrails['fertilizer_window_open']),
            'report_fertilizer_budget_clipped': bool(fert_guardrails['budget_clipped']),
            'report_fertilizer_gate_reason': fert_guardrails['gate_reason'],
            'report_fertilizer_budget_year': int(fert_guardrails['budget_operation_year']),
            'report_remaining_n_budget': float(fert_guardrails['remaining_after']['N']),
            'report_remaining_p_budget': float(fert_guardrails['remaining_after']['P']),
            'report_remaining_k_budget': float(fert_guardrails['remaining_after']['K']),
        }
        active_crop_context = fert_guardrails['active_crop_context']
        info.update({
            'report_active_crop_name': None if active_crop_context is None else active_crop_context['crop_name'],
            'report_active_crop_operation_year': (
                None if active_crop_context is None else int(active_crop_context['source_operation_year'])
            ),
            'report_active_window_start_doy': (
                None if active_crop_context is None else int(active_crop_context['window_start_doy'])
            ),
            'report_active_window_end_doy': (
                None if active_crop_context is None else int(active_crop_context['window_end_doy'])
            ),
            'report_active_window_relation': (
                None if active_crop_context is None else active_crop_context['window_relation']
            ),
        })
        if crop_decision is None:
            info.update({
                'report_crop_name': None,
                'report_plant_doy': None,
                'report_plant_end_doy': None,
                'report_plant_max_smc': None,
                'report_window_start_doy': None,
                'report_window_end_doy': None,
                'report_window_compliant': None,
                'report_effective_crop_name': None,
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
                'report_effective_crop_name': crop_decision['effective_crop_name'],
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
        self.crop_decisions_by_operation_year = {}
        self.nutrient_usage_by_operation_year = {}

        rerun_cycles = self.planter.reset() or self.fertilizer.reset()
        if rerun_cycles:
            self._call_cycles(debug=False, reinit=False, doy=None)

        obs = self.observer.compute_obs(self.date, N=0.0)
        obs = np.asarray(obs, dtype=np.float32)
        return (obs, {}) if GYMNASIUM else obs
