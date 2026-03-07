from __future__ import annotations

import csv
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


class HierarchicalThesisReportCallback(BaseCallback):
    """
    Stream hierarchical training reports to CSV files.

    Outputs:
    - weekly_npk_log.csv
    - yearly_crop_decisions.csv
    - season_window_compliance.csv
    - reporting_summary.json
    """

    WEEKLY_FIELDS = [
        'num_timesteps',
        'env_index',
        'date',
        'year',
        'doy',
        'operation_year',
        'n_kg',
        'p_kg',
        'k_kg',
        'cost_n',
        'cost_p',
        'cost_k',
        'cost_total',
        'reward',
        'planner_applied',
        'window_compliant',
        'crop_name',
        'action_raw',
    ]

    YEARLY_FIELDS = [
        'num_timesteps',
        'env_index',
        'date',
        'operation_year',
        'crop_name',
        'crop_index',
        'plant_doy',
        'plant_end_doy',
        'plant_max_smc',
        'window_start_doy',
        'window_end_doy',
        'window_compliant',
    ]

    def __init__(self, report_dir: str, verbose: int = 0):
        super().__init__(verbose=verbose)
        self.report_dir = Path(report_dir)
        self.weekly_csv_path = self.report_dir / 'weekly_npk_log.csv'
        self.yearly_csv_path = self.report_dir / 'yearly_crop_decisions.csv'
        self.compliance_csv_path = self.report_dir / 'season_window_compliance.csv'
        self.summary_json_path = self.report_dir / 'reporting_summary.json'

        self._weekly_fh = None
        self._yearly_fh = None
        self._weekly_writer = None
        self._yearly_writer = None

        self._weekly_rows = 0
        self._yearly_rows = 0
        self._n_total = 0.0
        self._p_total = 0.0
        self._k_total = 0.0
        self._cost_n_total = 0.0
        self._cost_p_total = 0.0
        self._cost_k_total = 0.0
        self._cost_total = 0.0
        self._compliance_by_operation_year: dict[int, dict[str, int]] = {}

    @staticmethod
    def _to_builtin(value: Any):
        if isinstance(value, (np.floating, np.integer)):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
        return value

    def _extract_action_for_env(self, actions, env_index: int):
        if actions is None:
            return None
        try:
            arr = np.asarray(actions)
            if arr.ndim == 0:
                return self._to_builtin(arr)
            if arr.ndim >= 1 and env_index < arr.shape[0]:
                return self._to_builtin(arr[env_index])
            return self._to_builtin(arr)
        except Exception:
            return self._to_builtin(actions)

    def _open_writers(self):
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self._weekly_fh = open(self.weekly_csv_path, 'w', newline='', encoding='utf-8')
        self._yearly_fh = open(self.yearly_csv_path, 'w', newline='', encoding='utf-8')
        self._weekly_writer = csv.DictWriter(self._weekly_fh, fieldnames=self.WEEKLY_FIELDS)
        self._yearly_writer = csv.DictWriter(self._yearly_fh, fieldnames=self.YEARLY_FIELDS)
        self._weekly_writer.writeheader()
        self._yearly_writer.writeheader()

    def _on_training_start(self) -> None:
        self._open_writers()

    def _on_step(self) -> bool:
        infos = self.locals.get('infos')
        rewards = self.locals.get('rewards')
        actions = self.locals.get('actions')
        if infos is None:
            return True

        for env_index, info in enumerate(infos):
            if not isinstance(info, dict) or not info.get('reporting_enabled', False):
                continue

            reward_value = None
            if rewards is not None:
                try:
                    reward_value = float(np.asarray(rewards)[env_index])
                except Exception:
                    reward_value = None

            action_raw = self._extract_action_for_env(actions, env_index)
            action_raw_str = json.dumps(action_raw, default=str)

            weekly_row = {
                'num_timesteps': int(self.num_timesteps),
                'env_index': int(env_index),
                'date': info.get('report_date'),
                'year': info.get('report_year'),
                'doy': info.get('report_doy'),
                'operation_year': info.get('report_operation_year'),
                'n_kg': info.get('report_n_kg', 0.0),
                'p_kg': info.get('report_p_kg', 0.0),
                'k_kg': info.get('report_k_kg', 0.0),
                'cost_n': info.get('report_cost_n', 0.0),
                'cost_p': info.get('report_cost_p', 0.0),
                'cost_k': info.get('report_cost_k', 0.0),
                'cost_total': info.get('report_cost_total', 0.0),
                'reward': reward_value,
                'planner_applied': bool(info.get('planner_applied', False)),
                'window_compliant': info.get('report_window_compliant'),
                'crop_name': info.get('report_crop_name'),
                'action_raw': action_raw_str,
            }
            self._weekly_writer.writerow(weekly_row)
            self._weekly_rows += 1

            self._n_total += float(info.get('report_n_kg', 0.0) or 0.0)
            self._p_total += float(info.get('report_p_kg', 0.0) or 0.0)
            self._k_total += float(info.get('report_k_kg', 0.0) or 0.0)
            self._cost_n_total += float(info.get('report_cost_n', 0.0) or 0.0)
            self._cost_p_total += float(info.get('report_cost_p', 0.0) or 0.0)
            self._cost_k_total += float(info.get('report_cost_k', 0.0) or 0.0)
            self._cost_total += float(info.get('report_cost_total', 0.0) or 0.0)

            if bool(info.get('planner_applied', False)):
                yearly_row = {
                    'num_timesteps': int(self.num_timesteps),
                    'env_index': int(env_index),
                    'date': info.get('report_date'),
                    'operation_year': info.get('report_operation_year'),
                    'crop_name': info.get('report_crop_name'),
                    'crop_index': info.get('report_crop_index'),
                    'plant_doy': info.get('report_plant_doy'),
                    'plant_end_doy': info.get('report_plant_end_doy'),
                    'plant_max_smc': info.get('report_plant_max_smc'),
                    'window_start_doy': info.get('report_window_start_doy'),
                    'window_end_doy': info.get('report_window_end_doy'),
                    'window_compliant': info.get('report_window_compliant'),
                }
                self._yearly_writer.writerow(yearly_row)
                self._yearly_rows += 1

                op_year = int(info.get('report_operation_year'))
                op_stats = self._compliance_by_operation_year.setdefault(
                    op_year, {'total': 0, 'compliant': 0}
                )
                op_stats['total'] += 1
                if info.get('report_window_compliant') is True:
                    op_stats['compliant'] += 1

        return True

    def _write_compliance_outputs(self):
        total_decisions = sum(v['total'] for v in self._compliance_by_operation_year.values())
        total_compliant = sum(v['compliant'] for v in self._compliance_by_operation_year.values())

        with open(self.compliance_csv_path, 'w', newline='', encoding='utf-8') as fh:
            fields = ['operation_year', 'decisions', 'compliant', 'compliance_rate']
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for op_year in sorted(self._compliance_by_operation_year.keys()):
                stats = self._compliance_by_operation_year[op_year]
                decisions = int(stats['total'])
                compliant = int(stats['compliant'])
                rate = (compliant / decisions) if decisions > 0 else None
                writer.writerow({
                    'operation_year': op_year,
                    'decisions': decisions,
                    'compliant': compliant,
                    'compliance_rate': rate,
                })
            overall_rate = (total_compliant / total_decisions) if total_decisions > 0 else None
            writer.writerow({
                'operation_year': 'overall',
                'decisions': total_decisions,
                'compliant': total_compliant,
                'compliance_rate': overall_rate,
            })

        summary = {
            'generated_at': datetime.now().isoformat(),
            'weekly_rows': self._weekly_rows,
            'yearly_rows': self._yearly_rows,
            'total_n_kg': self._n_total,
            'total_p_kg': self._p_total,
            'total_k_kg': self._k_total,
            'total_cost_n': self._cost_n_total,
            'total_cost_p': self._cost_p_total,
            'total_cost_k': self._cost_k_total,
            'total_cost': self._cost_total,
            'total_yearly_decisions': total_decisions,
            'compliant_yearly_decisions': total_compliant,
            'overall_compliance_rate': (total_compliant / total_decisions) if total_decisions > 0 else None,
            'files': {
                'weekly_npk_log_csv': str(self.weekly_csv_path),
                'yearly_crop_decisions_csv': str(self.yearly_csv_path),
                'season_window_compliance_csv': str(self.compliance_csv_path),
            },
        }
        self.summary_json_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')

    def _close_writers(self):
        if self._weekly_fh is not None:
            self._weekly_fh.flush()
            self._weekly_fh.close()
            self._weekly_fh = None
        if self._yearly_fh is not None:
            self._yearly_fh.flush()
            self._yearly_fh.close()
            self._yearly_fh = None

    def _on_training_end(self) -> None:
        self._close_writers()
        self._write_compliance_outputs()
