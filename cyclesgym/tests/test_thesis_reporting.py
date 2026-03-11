import csv
import json
import tempfile
from pathlib import Path
import unittest

import numpy as np

from cyclesgym.utils.thesis_reporting import HierarchicalThesisReportCallback


class TestHierarchicalThesisReportCallback(unittest.TestCase):
    def test_writes_weekly_yearly_and_compliance_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            report_dir = Path(td)
            cb = HierarchicalThesisReportCallback(report_dir=str(report_dir))
            cb._on_training_start()

            cb.locals = {
                'infos': [
                    {
                        'reporting_enabled': True,
                        'planner_applied': True,
                        'report_date': '2005-01-01',
                        'report_year': 2005,
                        'report_doy': 1,
                        'report_operation_year': 1,
                        'report_requested_n_kg': 10.0,
                        'report_requested_p_kg': 2.0,
                        'report_requested_k_kg': 1.0,
                        'report_n_kg': 10.0,
                        'report_p_kg': 2.0,
                        'report_k_kg': 1.0,
                        'report_cost_n': 100.0,
                        'report_cost_p': 20.0,
                        'report_cost_k': 10.0,
                        'report_cost_total': 130.0,
                        'report_requested_crop_name': 'SoybeanMG.3',
                        'report_crop_name': 'CornRM.100',
                        'report_effective_crop_name': 'CornRM.100',
                        'report_crop_index': 0,
                        'report_plant_doy': 170,
                        'report_plant_end_doy': 176,
                        'report_plant_max_smc': 0.5,
                        'report_window_start_doy': 166,
                        'report_window_end_doy': 196,
                        'report_window_compliant': True,
                        'report_crop_action_sanitized': True,
                        'report_crop_sanitization_reason': 'undefined_crop_window',
                        'report_fallback_crop_name': 'CornRM.100',
                        'report_active_crop_name': 'CornRM.100',
                        'report_fertilizer_window_open': True,
                        'report_fertilizer_gate_reason': 'applied',
                        'report_fertilizer_budget_year': 1,
                        'report_fertilizer_budget_clipped': False,
                        'report_remaining_n_budget': 140.0,
                        'report_remaining_p_budget': 78.0,
                        'report_remaining_k_budget': 59.0,
                    }
                ],
                'rewards': np.array([12.3], dtype=np.float32),
                'actions': np.array([[0, 0, 0, 0, 2, 1, 1]], dtype=np.int64),
            }
            cb.num_timesteps = 10
            assert cb._on_step() is True

            cb.locals = {
                'infos': [
                    {
                        'reporting_enabled': True,
                        'planner_applied': False,
                        'report_date': '2005-01-08',
                        'report_year': 2005,
                        'report_doy': 8,
                        'report_operation_year': 1,
                        'report_requested_n_kg': 10.0,
                        'report_requested_p_kg': 2.0,
                        'report_requested_k_kg': 1.0,
                        'report_n_kg': 0.0,
                        'report_p_kg': 0.0,
                        'report_k_kg': 0.0,
                        'report_cost_n': 0.0,
                        'report_cost_p': 0.0,
                        'report_cost_k': 0.0,
                        'report_cost_total': 0.0,
                        'report_requested_crop_name': 'CornRM.100',
                        'report_crop_name': None,
                        'report_active_crop_name': None,
                        'report_window_compliant': None,
                        'report_fertilizer_window_open': False,
                        'report_fertilizer_gate_reason': 'outside_active_crop_window',
                        'report_fertilizer_budget_year': 1,
                        'report_fertilizer_budget_clipped': False,
                        'report_remaining_n_budget': 140.0,
                        'report_remaining_p_budget': 78.0,
                        'report_remaining_k_budget': 59.0,
                    }
                ],
                'rewards': np.array([1.2], dtype=np.float32),
                'actions': np.array([[0, 0, 0, 0, 0, 0, 0]], dtype=np.int64),
            }
            cb.num_timesteps = 11
            assert cb._on_step() is True

            cb._on_training_end()

            weekly_path = report_dir / 'weekly_npk_log.csv'
            yearly_path = report_dir / 'yearly_crop_decisions.csv'
            compliance_path = report_dir / 'season_window_compliance.csv'
            summary_path = report_dir / 'reporting_summary.json'

            assert weekly_path.exists()
            assert yearly_path.exists()
            assert compliance_path.exists()
            assert summary_path.exists()

            with weekly_path.open('r', encoding='utf-8') as fh:
                rows = list(csv.DictReader(fh))
            assert len(rows) == 2

            with yearly_path.open('r', encoding='utf-8') as fh:
                rows = list(csv.DictReader(fh))
            assert len(rows) == 1
            assert rows[0]['crop_name'] == 'CornRM.100'
            assert rows[0]['requested_crop_name'] == 'SoybeanMG.3'
            assert rows[0]['crop_action_sanitized'] == 'True'

            with summary_path.open('r', encoding='utf-8') as fh:
                summary = json.load(fh)
            assert summary['weekly_rows'] == 2
            assert summary['yearly_rows'] == 1
            assert summary['overall_compliance_rate'] == 1.0
            assert summary['window_blocked_steps'] == 1
            assert summary['budget_clipped_steps'] == 0
            assert summary['sanitized_crop_decisions'] == 1


if __name__ == '__main__':
    unittest.main()
