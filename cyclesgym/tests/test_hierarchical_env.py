import unittest
from datetime import date
import numpy as np

from cyclesgym.envs.hierarchical import HierarchicalCropPlanningFertilization


class TestHierarchicalEnv(unittest.TestCase):
    def test_reset_and_first_step_applies_planner(self):
        env = HierarchicalCropPlanningFertilization(
            start_year=2005,
            end_year=2005,
            rotation_crops=['CornRM.100', 'SoybeanMG.3'],
            nutrient_action_mode='NPK',
            use_pakistan_crop_calendar=True,
            price_profile='pakistan_baseline',
        )
        obs, info = env.reset()
        assert obs.shape[0] == env.observation_space.shape[0]
        assert isinstance(info, dict)

        action = np.array([0, 0, 0, 0, 0, 0, 0], dtype=np.int64)
        step_out = env.step(action)
        step_info = step_out[-1]
        assert step_info['planner_applied'] is True
        assert step_info['report_requested_crop_name'] == 'CornRM.100'
        assert step_info['reporting_enabled'] is True
        assert step_info['report_crop_name'] == 'CornRM.100'
        assert step_info['report_cost_n'] >= 0
        assert step_info['report_cost_p'] >= 0
        assert step_info['report_cost_k'] >= 0
        assert step_info['report_cost_total'] >= 0
        assert step_info['report_window_compliant'] is True
        assert step_info['report_fertilizer_window_open'] is False
        assert step_info['report_fertilizer_gate_reason'] == 'outside_active_crop_window'
        assert step_info['report_n_kg'] == 0.0

    def test_invalid_crop_is_sanitized_to_defined_window_crop(self):
        env = HierarchicalCropPlanningFertilization(
            start_year=2005,
            end_year=2005,
            rotation_crops=['CornRM.100', 'SoybeanMG.3'],
            nutrient_action_mode='NPK',
            use_pakistan_crop_calendar=True,
            price_profile='pakistan_baseline',
        )
        env.reset()
        soybean_action = np.array([1, 0, 0, 0, 0, 0, 0], dtype=np.int64)
        step_out = env.step(soybean_action)
        step_info = step_out[-1]
        assert step_info['planner_applied'] is True
        assert step_info['report_requested_crop_name'] == 'SoybeanMG.3'
        assert step_info['report_crop_name'] == 'CornRM.100'
        assert step_info['report_effective_crop_name'] == 'CornRM.100'
        assert step_info['report_crop_action_sanitized'] is True
        assert step_info['report_crop_sanitization_reason'] == 'undefined_crop_window'
        assert step_info['report_fallback_crop_name'] == 'CornRM.100'

    def test_second_step_does_not_reapply_planner(self):
        env = HierarchicalCropPlanningFertilization(
            start_year=2005,
            end_year=2005,
            rotation_crops=['CornRM.100', 'SoybeanMG.3'],
            nutrient_action_mode='NPK',
            use_pakistan_crop_calendar=True,
            price_profile='pakistan_baseline',
        )
        env.reset()
        action = np.array([0, 0, 0, 0, 0, 0, 0], dtype=np.int64)
        env.step(action)
        step_out = env.step(action)
        step_info = step_out[-1]
        assert step_info['planner_applied'] is False
        assert step_info['report_crop_name'] is None

    def test_fertilizer_budget_is_capped_inside_active_window(self):
        env = HierarchicalCropPlanningFertilization(
            start_year=2005,
            end_year=2005,
            rotation_crops=['CornRM.100', 'SoybeanMG.3'],
            nutrient_action_mode='NPK',
            use_pakistan_crop_calendar=True,
            price_profile='pakistan_baseline',
        )
        env.reset()
        env.step(np.array([0, 0, 0, 0, 0, 0, 0], dtype=np.int64))

        env.date = date(2005, 6, 20)
        env.nutrient_usage_by_operation_year[1] = {'N': 149.0, 'P': 79.0, 'K': 59.0}

        capped_action = np.array([0, 0, 0, 0, 10, 10, 10], dtype=np.int64)
        step_out = env.step(capped_action)
        step_info = step_out[-1]

        assert step_info['planner_applied'] is False
        assert step_info['report_fertilizer_window_open'] is True
        assert step_info['report_fertilizer_budget_clipped'] is True
        assert step_info['report_fertilizer_gate_reason'] == 'annual_budget_clipped'
        assert step_info['report_n_kg'] == 1.0
        assert step_info['report_p_kg'] == 1.0
        assert step_info['report_k_kg'] == 1.0
        assert step_info['report_remaining_n_budget'] == 0.0
        assert step_info['report_remaining_p_budget'] == 0.0
        assert step_info['report_remaining_k_budget'] == 0.0


if __name__ == '__main__':
    unittest.main()
