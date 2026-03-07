import unittest
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
        assert 'cost_total_n' in step_info
        assert step_info['reporting_enabled'] is True
        assert step_info['report_crop_name'] in {'CornRM.100', 'SoybeanMG.3'}
        assert step_info['report_cost_n'] >= 0
        assert step_info['report_cost_p'] >= 0
        assert step_info['report_cost_k'] >= 0
        assert step_info['report_cost_total'] >= 0
        assert step_info['report_window_compliant'] in {True, False, None}

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


if __name__ == '__main__':
    unittest.main()
