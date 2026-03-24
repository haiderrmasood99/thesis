#!/usr/bin/env python3
"""Build a self-contained LaTeX report package for the final thesis experiments."""

from __future__ import annotations

import argparse
import json
import shutil
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / 'artifacts' / 'final_successful_runs' / 'thesis_reporting_pack'
OUTPUT_ROOT = REPO_ROOT / 'artifacts' / 'final_successful_runs' / 'final_experiments_report'
SCHEMA_VERSION = '1.0.0'

POINT_TITLES = {
    'point1_entropy_fertilization': 'Entropy Coefficient in Fertilization',
    'point2_hierarchical_shaping': 'Blocked-Nutrient Penalty in Hierarchical Crop Planning',
    'point3_nutrient_cost_weight': 'Nutrient Cost Weight in Fertilization',
}

POINT_SLUGS = {
    'point1_entropy_fertilization': 'fertilization_entropy_ablation',
    'point2_hierarchical_shaping': 'hierarchical_crop_planning_blocked_nutrient_penalty',
    'point3_nutrient_cost_weight': 'fertilization_nutrient_cost_weight_ablation',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', default=str(OUTPUT_ROOT))
    parser.add_argument('--overwrite', action='store_true')
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def ensure_clean(path: Path, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(f'Output root already exists: {path}')
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def latex_escape(value) -> str:
    text = '' if value is None else str(value)
    replacements = {
        '\\': r'\textbackslash{}',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def fmt_num(value, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return 'n/a'
    return f'{float(value):,.{digits}f}'


def fmt_int(value) -> str:
    if value is None or pd.isna(value):
        return 'n/a'
    return f'{int(value):,}'


def round_df(frame: pd.DataFrame, digits: int = 2) -> pd.DataFrame:
    out = frame.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            out[col] = out[col].round(digits)
    return out


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path) -> list[Path]:
    copied = []
    if not src.exists():
        return copied
    for path in sorted(src.rglob('*')):
        if path.is_dir():
            continue
        target = dst / path.relative_to(src)
        copy_file(path, target)
        copied.append(target)
    return copied


def moving_average(values: np.ndarray, window: int = 5) -> np.ndarray:
    if values.size == 0:
        return values
    if values.size < window:
        window = max(1, values.size)
    kernel = np.ones(window, dtype=float) / float(window)
    return np.convolve(values, kernel, mode='same')


def rolling_std(values: np.ndarray, window: int = 5) -> np.ndarray:
    if values.size == 0:
        return values
    series = pd.Series(values)
    return series.rolling(window=window, min_periods=1).std().fillna(0.0).to_numpy(dtype=float)


def bundle_path(row: pd.Series) -> Path:
    return Path(str(row['bundle_dir']))


def history_path(row: pd.Series) -> Path:
    return Path(str(row['history_scan_path']))


def load_history(row: pd.Series) -> pd.DataFrame:
    return pd.read_csv(history_path(row))


def pick_primary_eval_columns(history: pd.DataFrame) -> list[str]:
    candidates = [
        'eval_test_det/mean_reward',
        'eval_det/mean_reward',
        'eval_train_det/mean_reward',
        'eval_sto/mean_reward',
    ]
    present = [name for name in candidates if name in history.columns and history[name].notna().any()]
    if present:
        return present
    fallback = [
        name for name in history.columns
        if name.startswith('eval') and name.endswith('/mean_reward') and history[name].notna().any()
    ]
    return fallback[:4]


def clean_series(history: pd.DataFrame, x_col: str, y_col: str) -> tuple[np.ndarray, np.ndarray]:
    subset = history[[x_col, y_col]].dropna()
    if subset.empty:
        return np.array([]), np.array([])
    return subset[x_col].to_numpy(dtype=float), subset[y_col].to_numpy(dtype=float)


def write_png_json(png_path: Path, json_path: Path, payload: dict) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(json_path, payload)


def descriptive_aliases_for_grouped_figures() -> dict[tuple[str, str], str]:
    return {
        ('final_42_ablation', 'final_42_ablation__point1_entropy_primary_metric.png'): 'fertilization_entropy_ablation__primary_metric.png',
        ('final_42_ablation', 'final_42_ablation__point1_entropy_paired_deltas.png'): 'fertilization_entropy_ablation__paired_deltas.png',
        ('final_42_ablation', 'final_42_ablation__point2_primary_comparison.png'): 'hierarchical_crop_planning_blocked_nutrient_penalty__primary_comparison.png',
        ('final_42_ablation', 'final_42_ablation__point2_thesis_compliance.png'): 'hierarchical_crop_planning_blocked_nutrient_penalty__compliance.png',
        ('final_42_ablation', 'final_42_ablation__point3_cost_weight_primary_metric.png'): 'fertilization_nutrient_cost_weight_ablation__primary_metric.png',
        ('final_42_ablation', 'final_42_ablation__point3_cost_weight_paired_deltas.png'): 'fertilization_nutrient_cost_weight_ablation__paired_deltas.png',
    }


def has_artifact(dataset: str, run_slug: str, artifact_id: str) -> bool:
    return (PACK_ROOT / dataset / 'figures' / 'per_run' / f'{run_slug}__{artifact_id}.png').exists()


def pick_run(frame: pd.DataFrame, dataset: str, required: list[str], sort_col: str = 'primary_metric_value', ascending: bool = False) -> pd.Series:
    ordered = frame.sort_values(sort_col, ascending=ascending, na_position='last')
    for _, row in ordered.iterrows():
        slug = str(row['run_slug'])
        if all(has_artifact(dataset, slug, artifact) for artifact in required):
            return row
    return ordered.iloc[0]


def choose_exemplars(run_catalog: pd.DataFrame) -> pd.DataFrame:
    required = [
        'training_reward_vs_global_step',
        'episode_length_vs_global_step',
        'primary_metric_vs_global_step',
        'diagnostics_panel',
    ]
    rows = []
    final113 = run_catalog[(run_catalog['dataset'] == 'final_113') & (run_catalog['learned_run'] == True)].copy()
    final42 = run_catalog[(run_catalog['dataset'] == 'final_42_ablation') & (run_catalog['learned_run'] == True)].copy()
    point1 = final42[final42['point'] == 'point1_entropy_fertilization']
    point2 = final42[final42['point'] == 'point2_hierarchical_shaping']
    point3 = final42[final42['point'] == 'point3_nutrient_cost_weight']

    selected = [
        ('final_113', 'best_fertilization_single', pick_run(final113[final113['report_group'] == 'fertilization_core'], 'final_113', required), 'Best fertilization exemplar with full diagnostics.'),
        ('final_113', 'weak_random_weather_fertilization', pick_run(final113[(final113['report_group'] == 'fertilization_core') & (final113['weather_label'] == 'random_weather')], 'final_113', required, ascending=True), 'Lower-performing random-weather fertilization exemplar.'),
        ('final_113', 'best_crop_nonhier_single', pick_run(final113[final113['report_group'] == 'crop_planning_nonhier'], 'final_113', required), 'Best non-hierarchical crop-planning exemplar.'),
        ('final_113', 'best_hierarchical_single', pick_run(final113[final113['report_group'] == 'crop_planning_hierarchical_guarded_rerun'], 'final_113', required), 'Best hierarchical guarded rerun exemplar.'),
        ('final_113', 'best_dqn_descriptive', pick_run(final113[final113['report_group'].isin(['fertilization_dqn_rerun', 'crop_planning_dqn_rerun'])], 'final_113', required), 'Best DQN descriptive comparator.'),
        ('final_42_ablation', 'point1_fixed_weather_no_entropy', pick_run(point1[(point1['weather_label'] == 'fixed_weather') & (point1['ent_coef'] == 0.0)], 'final_42_ablation', required), 'Point 1 fixed-weather entropy=0.0 reference.'),
        ('final_42_ablation', 'point1_random_weather_with_entropy', pick_run(point1[(point1['weather_label'] == 'random_weather') & (point1['ent_coef'] == 0.01)], 'final_42_ablation', required), 'Point 1 random-weather entropy=0.01 winner.'),
        ('final_42_ablation', 'point2_best_a2c_fixed', pick_run(point2[(point2['method'] == 'A2C') & (point2['weather_label'] == 'fixed_weather')], 'final_42_ablation', required + ['weekly_npk_behavior', 'crop_decision_timeline', 'compliance_summary', 'blocked_cost_summary'], sort_col='deterministic_return'), 'Point 2 A2C fixed-weather winner.'),
        ('final_42_ablation', 'point2_best_ppo_random', pick_run(point2[(point2['method'] == 'PPO') & (point2['weather_label'] == 'random_weather')], 'final_42_ablation', required + ['weekly_npk_behavior', 'crop_decision_timeline', 'compliance_summary', 'blocked_cost_summary'], sort_col='deterministic_return'), 'Point 2 PPO random-weather reference.'),
        ('final_42_ablation', 'point3_best_fixed_default_weight', pick_run(point3[(point3['weather_label'] == 'fixed_weather') & (point3['nutrient_cost_weight'] == 1.0)], 'final_42_ablation', required), 'Point 3 fixed-weather default cost-weight reference.'),
        ('final_42_ablation', 'point3_best_random_high_weight', pick_run(point3[(point3['weather_label'] == 'random_weather') & (point3['nutrient_cost_weight'] == 1.2)], 'final_42_ablation', required), 'Point 3 random-weather 1.2 cost-weight exemplar.'),
        ('final_42_ablation', 'point3_weak_fixed_low_weight', pick_run(point3[(point3['weather_label'] == 'fixed_weather') & (point3['nutrient_cost_weight'] == 0.8)], 'final_42_ablation', required, ascending=True), 'Point 3 weaker fixed-weather 0.8 cost-weight exemplar.'),
    ]
    for dataset, key, row, reason in selected:
        rows.append({'dataset': dataset, 'key': key, 'run_slug': str(row['run_slug']), 'reason': reason})
    return pd.DataFrame(rows)


def find_catalog_row(run_catalog: pd.DataFrame, dataset: str, run_slug: str) -> pd.Series:
    return run_catalog[(run_catalog['dataset'] == dataset) & (run_catalog['run_slug'] == run_slug)].iloc[0]


def write_table_triplet(name: str, frame: pd.DataFrame, caption: str, label: str, output_root: Path, source_paths: list[str], notes: str | None = None) -> dict[str, Path]:
    csv_dir = output_root / 'tables' / 'csv' / 'derived'
    tex_dir = output_root / 'tables' / 'tex'
    csv_dir.mkdir(parents=True, exist_ok=True)
    tex_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_dir / f'{name}.csv'
    json_path = csv_dir / f'{name}.json'
    tex_path = tex_dir / f'{name}.tex'
    frame.to_csv(csv_path, index=False)
    write_json(json_path, {
        'schema_version': SCHEMA_VERSION,
        'generated_at': now_iso(),
        'name': name,
        'caption': caption,
        'label': label,
        'notes': notes,
        'source_paths': source_paths,
        'columns': list(frame.columns),
        'rows': frame.to_dict(orient='records'),
    })
    tabular = frame.fillna('n/a').to_latex(index=False, escape=True)
    tex = textwrap.dedent(f'''
    \\begin{{table}}[H]
    \\centering
    \\small
    \\caption{{{latex_escape(caption)}}}
    \\label{{{latex_escape(label)}}}
    \\resizebox{{\\textwidth}}{{!}}{{%
    {tabular.rstrip()}
    }}
    \\end{{table}}
    ''').strip() + '\n'
    tex_path.write_text(tex, encoding='utf-8')
    return {'csv': csv_path, 'json': json_path, 'tex': tex_path}


def build_derived_tables(output_root: Path, build_summary: dict, build_verification: dict, final_summary: dict, run_catalog: pd.DataFrame, representative_index: pd.DataFrame, grouped113: pd.DataFrame, point1_grouped: pd.DataFrame, point1_paired: pd.DataFrame, point2_grouped: pd.DataFrame, point3_grouped: pd.DataFrame, point3_paired: pd.DataFrame, exemplars: pd.DataFrame, checkpoint_gap_df: pd.DataFrame) -> dict[str, dict[str, Path]]:
    outputs = {}
    dataset_rows = []
    for item in build_summary['datasets']:
        dataset_rows.append({
            'dataset': item['dataset'],
            'expected_runs': item['expected_runs'],
            'matched_histories': item['matched_histories'],
            'learned_runs': item['learned_runs'],
            'png_count': item['png_count'],
            'csv_count': item['csv_count'],
            'json_count': item['json_count'],
            'render_png_count': item['render_png_count'],
            'missing_or_skipped_count': item['missing_or_skipped_count'],
        })
    outputs['dataset_overview'] = write_table_triplet('dataset_overview', pd.DataFrame(dataset_rows), 'Overview of the audited datasets used in this report package.', 'tab:dataset_overview', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/qa/build_summary.json'], notes='The audited canonical corpus is 113+42=155 runs.')

    counts = pd.DataFrame([{'report_group': k, 'run_count': v} for k, v in final_summary['counts']['report_group_counts'].items()])
    outputs['final113_report_group_counts'] = write_table_triplet('final113_report_group_counts', counts, 'Composition of the 113-run matrix by report group.', 'tab:final113_report_group_counts', output_root, ['artifacts/final_successful_runs/final_113/reporting/final_reporting_summary.json'])

    best_groups = pd.DataFrame([
        {'report_group': k, 'best_setting': v['group_key'], 'metric': v['metric'], 'n': v['n'], 'mean': v['mean'], 'ci_low': v['ci_low'], 'ci_high': v['ci_high']}
        for k, v in final_summary['best_groups'].items()
    ])
    outputs['final113_best_groups'] = write_table_triplet('final113_best_groups', round_df(best_groups, 3), 'Best grouped settings from the 113-run matrix.', 'tab:final113_best_groups', output_root, ['artifacts/final_successful_runs/final_113/reporting/final_reporting_summary.json'])

    single_rows = []
    for report_group, details in final_summary['best_single_runs'].items():
        row = run_catalog[(run_catalog['dataset'] == 'final_113') & (run_catalog['index'] == int(details['index']))].iloc[0]
        single_rows.append({'report_group': report_group, 'run_slug': row['run_slug'], 'label': details['label'], 'metric': details['metric'], 'value': details['value']})
    outputs['final113_best_single_runs'] = write_table_triplet('final113_best_single_runs', round_df(pd.DataFrame(single_rows), 3), 'Best single runs from the 113-run matrix.', 'tab:final113_best_single_runs', output_root, ['artifacts/final_successful_runs/final_113/reporting/final_reporting_summary.json', 'artifacts/final_successful_runs/thesis_reporting_pack/catalogs/run_catalog.csv'])

    def grouped_subset(report_group: str, top_n: int) -> pd.DataFrame:
        df = grouped113[grouped113['report_group'] == report_group].sort_values('primary_metric_value_mean', ascending=False).head(top_n)
        return df[['group_key', 'primary_metric_name', 'primary_metric_value_mean', 'primary_metric_value_ci_low', 'primary_metric_value_ci_high', 'runtime_seconds_mean', 'n']]

    outputs['final113_fertilization_top_groups'] = write_table_triplet('final113_fertilization_top_groups', round_df(grouped_subset('fertilization_core', 8), 3), 'Top grouped fertilization settings in the 113-run matrix.', 'tab:final113_fertilization_top_groups', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/final_113/tables/grouped/final_113__grouped_metrics.csv'])
    outputs['final113_crop_nonhier_groups'] = write_table_triplet('final113_crop_nonhier_groups', round_df(grouped_subset('crop_planning_nonhier', 8), 3), 'Grouped non-hierarchical crop-planning settings.', 'tab:final113_crop_nonhier_groups', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/final_113/tables/grouped/final_113__grouped_metrics.csv'])
    outputs['final113_hierarchical_groups'] = write_table_triplet('final113_hierarchical_groups', round_df(grouped_subset('crop_planning_hierarchical_guarded_rerun', 8), 3), 'Grouped hierarchical guarded-rerun settings.', 'tab:final113_hierarchical_groups', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/final_113/tables/grouped/final_113__grouped_metrics.csv'])

    dqn = run_catalog[(run_catalog['dataset'] == 'final_113') & (run_catalog['report_group'].isin(['fertilization_dqn_rerun', 'crop_planning_dqn_rerun']))][['run_slug', 'report_group', 'domain', 'method', 'weather_label', 'adaptive_label', 'total_years', 'primary_metric_name', 'primary_metric_value', 'runtime_seconds']].sort_values('primary_metric_value', ascending=False)
    outputs['final113_dqn_descriptive'] = write_table_triplet('final113_dqn_descriptive', round_df(dqn, 3), 'Descriptive DQN rerun results.', 'tab:final113_dqn_descriptive', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/catalogs/run_catalog.csv'])

    point_counts = run_catalog[run_catalog['dataset'] == 'final_42_ablation']['point'].value_counts().rename_axis('point').reset_index(name='run_count').sort_values('point')
    outputs['ablation_point_counts'] = write_table_triplet('ablation_point_counts', point_counts, 'Composition of the 42-run ablation suite by point study.', 'tab:ablation_point_counts', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/catalogs/run_catalog.csv'])

    p1 = point1_grouped[['weather_label', 'ent_coef', 'deterministic_return__mean', 'stochastic_return_mean__mean', 'pak_holdout_return__mean', 'runtime_seconds__mean']]
    outputs['fertilization_entropy_ablation_summary'] = write_table_triplet('fertilization_entropy_ablation_summary', round_df(p1, 3), 'Entropy-coefficient ablation summary for fertilization by weather regime.', 'tab:fertilization_entropy_ablation_summary', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/final_42_ablation/tables/grouped/final_42_ablation__point1_grouped_metrics.csv'])
    outputs['fertilization_entropy_ablation_paired_stats'] = write_table_triplet('fertilization_entropy_ablation_paired_stats', round_df(point1_paired, 6), 'Entropy-coefficient ablation paired deltas for matched seed and weather comparisons.', 'tab:fertilization_entropy_ablation_paired_stats', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/final_42_ablation/tables/grouped/final_42_ablation__point1_paired_stats.csv'])

    p2 = point2_grouped[['run_slug', 'method', 'weather_label', 'blocked_penalty', 'deterministic_return', 'stochastic_return_mean', 'overall_compliance_rate', 'total_cost', 'blocked_npk_kg_total', 'reward_shaping_blocked_penalty_total']]
    outputs['hierarchical_crop_planning_blocked_nutrient_penalty_summary'] = write_table_triplet('hierarchical_crop_planning_blocked_nutrient_penalty_summary', round_df(p2, 3), 'Blocked-nutrient-penalty results for hierarchical crop planning.', 'tab:hierarchical_crop_planning_blocked_nutrient_penalty_summary', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/final_42_ablation/tables/grouped/final_42_ablation__point2_grouped_metrics.csv'])

    p3 = point3_grouped[['weather_label', 'nutrient_cost_weight', 'deterministic_return__mean', 'stochastic_return_mean__mean', 'pak_holdout_return__mean', 'runtime_seconds__mean']]
    outputs['fertilization_nutrient_cost_weight_summary'] = write_table_triplet('fertilization_nutrient_cost_weight_summary', round_df(p3, 3), 'Nutrient-cost-weight ablation summary for fertilization by weather regime.', 'tab:fertilization_nutrient_cost_weight_summary', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/final_42_ablation/tables/grouped/final_42_ablation__point3_grouped_metrics.csv'])
    outputs['fertilization_nutrient_cost_weight_paired_stats'] = write_table_triplet('fertilization_nutrient_cost_weight_paired_stats', round_df(point3_paired, 6), 'Nutrient-cost-weight paired deltas against the default setting of 1.0.', 'tab:fertilization_nutrient_cost_weight_paired_stats', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/final_42_ablation/tables/grouped/final_42_ablation__point3_paired_stats.csv'])

    exemplar_rows = []
    for _, ex in exemplars.iterrows():
        row = find_catalog_row(run_catalog, str(ex['dataset']), str(ex['run_slug']))
        exemplar_rows.append({'dataset': ex['dataset'], 'key': ex['key'], 'run_slug': ex['run_slug'], 'reason': ex['reason'], 'primary_metric_name': row['primary_metric_name'], 'primary_metric_value': row['primary_metric_value']})
    outputs['selected_exemplars'] = write_table_triplet('selected_exemplars', round_df(pd.DataFrame(exemplar_rows), 3), 'Exemplar runs copied into this report package for detailed discussion.', 'tab:selected_exemplars', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/catalogs/run_catalog.csv'])

    rep = representative_index.groupby(['dataset', 'family_slug']).size().rename('render_count').reset_index().sort_values(['dataset', 'family_slug'])
    outputs['representative_families'] = write_table_triplet('representative_families', rep, 'Representative-render families copied into the report package.', 'tab:representative_families', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/catalogs/representative_index.csv'])

    outputs['checkpoint_gap_run_level'] = write_table_triplet('checkpoint_gap_run_level', round_df(checkpoint_gap_df, 3), 'Run-level best-checkpoint versus final-checkpoint summary for runs with checkpoint evaluation logs.', 'tab:checkpoint_gap_run_level', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/catalogs/run_catalog.csv'])
    checkpoint_gap_summary = (
        checkpoint_gap_df.groupby(['dataset', 'group_name'])
        .agg(
            run_count=('run_slug', 'count'),
            mean_best_checkpoint=('best_checkpoint_mean', 'mean'),
            mean_final_checkpoint=('final_checkpoint_mean', 'mean'),
            mean_best_minus_final=('best_minus_final_checkpoint', 'mean'),
        )
        .reset_index()
        .sort_values(['dataset', 'mean_best_minus_final'], ascending=[True, False])
    )
    outputs['checkpoint_gap_summary'] = write_table_triplet('checkpoint_gap_summary', round_df(checkpoint_gap_summary, 3), 'Grouped best-checkpoint versus final-checkpoint summary for runs with checkpoint evaluation logs.', 'tab:checkpoint_gap_summary', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/catalogs/run_catalog.csv'])

    qa_rows = [{'dataset': k, 'catalog_rows': v['catalog_rows'], 'history_matches': v['history_matches']} for k, v in build_verification['datasets'].items()]
    qa_rows += [
        {'dataset': 'csv_without_json', 'catalog_rows': len(build_verification['csv_without_json']), 'history_matches': len(build_verification['csv_without_json'])},
        {'dataset': 'png_without_json', 'catalog_rows': len(build_verification['png_without_json']), 'history_matches': len(build_verification['png_without_json'])},
        {'dataset': 'run_metric_json_missing', 'catalog_rows': len(build_verification['run_metric_json_missing']), 'history_matches': len(build_verification['run_metric_json_missing'])},
    ]
    outputs['qa_summary'] = write_table_triplet('qa_summary', pd.DataFrame(qa_rows), 'QA verification summary for the reporting pack reused by this report.', 'tab:qa_summary', output_root, ['artifacts/final_successful_runs/thesis_reporting_pack/qa/build_verification.json'])
    return outputs


def fig_single(path: str, caption: str, label: str, width: str = '0.92\\textwidth') -> str:
    return textwrap.dedent(f'''
    \\begin{{figure}}[H]
    \\centering
    \\includegraphics[width={width}]{{{path}}}
    \\caption{{{latex_escape(caption)}}}
    \\label{{{latex_escape(label)}}}
    \\end{{figure}}
    ''').strip()


def fig_grid(items: list[tuple[str, str]], caption: str, label: str) -> str:
    lines = ['\\begin{figure}[H]', '\\centering']
    for i, (path, subcap) in enumerate(items):
        lines += [
            '\\begin{subfigure}[t]{0.48\\textwidth}',
            '\\centering',
            f'\\includegraphics[width=\\linewidth]{{{path}}}',
            f'\\caption{{{latex_escape(subcap)}}}',
            '\\end{subfigure}',
        ]
        if i != len(items) - 1:
            lines.append('\\hfill')
        if i % 2 == 1 and i != len(items) - 1:
            lines.append('\\vspace{0.8em}')
    lines += [f'\\caption{{{latex_escape(caption)}}}', f'\\label{{{latex_escape(label)}}}', '\\end{figure}']
    return '\n'.join(lines)


def training_panel(output_root: Path, run_slug: str) -> str:
    base = output_root / 'figures' / 'exemplars' / run_slug
    items = []
    names = [
        ('training_reward_vs_global_step', 'Training reward vs global step'),
        ('episode_length_vs_global_step', 'Episode length vs global step'),
        ('primary_metric_vs_global_step', 'Primary metric vs global step'),
        ('diagnostics_panel', 'Optimization diagnostics panel'),
    ]
    for artifact_id, caption in names:
        path = base / f'{run_slug}__{artifact_id}.png'
        if path.exists():
            items.append((rel(path, output_root), caption))
    if not items:
        return ''
    return fig_grid(items, f'Training-curve panel for {run_slug}.', f'fig:{run_slug}:panel')


def checkpoint_fig(output_root: Path, run_slug: str) -> str:
    path = output_root / 'figures' / 'exemplars' / run_slug / f'{run_slug}__checkpoint_eval_curves.png'
    if not path.exists():
        return ''
    return fig_single(rel(path, output_root), f'Checkpoint evaluation curves for {run_slug}.', f'fig:{run_slug}:checkpoint')


def extra_quality_figs(output_root: Path, run_slug: str) -> str:
    artifact_map = [
        ('mean_episode_reward_per_update', 'Mean episode reward per rollout update'),
        ('evaluation_mean_reward_tracks', 'Evaluation mean reward tracks'),
        ('training_vs_evaluation_alignment', 'Training vs evaluation alignment'),
        ('best_vs_final_checkpoint_evaluation', 'Best checkpoint vs final checkpoint evaluation'),
    ]
    blocks = []
    for artifact_id, caption in artifact_map:
        path = output_root / 'figures' / 'exemplars' / run_slug / f'{run_slug}__{artifact_id}.png'
        if path.exists():
            blocks.append(
                fig_single(
                    rel(path, output_root),
                    f'{caption} for {run_slug}.',
                    f'fig:{run_slug}:{artifact_id}',
                )
            )
    return '\n'.join(blocks)


def collect_checkpoint_tracks(row: pd.Series) -> list[dict]:
    tracks = []
    checkpoints_dir = bundle_path(row) / 'models' / 'checkpoints'
    if not checkpoints_dir.exists():
        return tracks
    for npz_path in sorted(checkpoints_dir.glob('*/evaluations.npz')):
        data = np.load(npz_path, allow_pickle=True)
        timesteps = data['timesteps'].astype(float)
        means = data['results'].mean(axis=1).astype(float)
        stds = data['results'].std(axis=1).astype(float)
        tracks.append({
            'track': npz_path.parent.name,
            'timesteps': timesteps,
            'means': means,
            'stds': stds,
            'best_mean': float(np.max(means)),
            'final_mean': float(means[-1]),
            'gap_to_best': float(means[-1] - np.max(means)),
        })
    return tracks


def main_checkpoint_track_name(row: pd.Series, tracks: list[dict]) -> str | None:
    preferred = []
    if str(row.get('dataset', '')) == 'final_113' and str(row.get('domain', '')) == 'fertilization':
        preferred = ['eval_test_det', 'eval_train_det']
    elif str(row.get('dataset', '')) == 'final_113':
        preferred = ['eval_det', 'eval_test_det']
    else:
        preferred = ['eval_det', 'eval_test_det']
    names = {track['track'] for track in tracks}
    for name in preferred:
        if name in names:
            return name
    return tracks[0]['track'] if tracks else None


def generate_exemplar_quality_figures(output_root: Path, row: pd.Series) -> list[Path]:
    run_slug = str(row['run_slug'])
    dataset = str(row['dataset'])
    history = load_history(row)
    figures_dir = output_root / 'figures' / 'exemplars' / run_slug
    figures_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    source_paths = [str(history_path(row))]

    if 'global_step' in history.columns and 'rollout/ep_rew_mean' in history.columns and history['rollout/ep_rew_mean'].notna().any():
        x, y = clean_series(history, 'global_step', 'rollout/ep_rew_mean')
        if x.size:
            ma = moving_average(y)
            sigma = rolling_std(y)
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.plot(x, y, color='#9a9a9a', linewidth=1.0, alpha=0.75, label='Mean episode reward per update')
            ax.plot(x, ma, color='#1f77b4', linewidth=2.0, label='5-point moving average')
            ax.set_xlabel('Global step')
            ax.set_ylabel('Mean episode reward')
            ax.set_title('Mean episode reward per rollout update')
            ax.grid(alpha=0.25)
            ax.legend(loc='best')
            fig.tight_layout()
            png = figures_dir / f'{run_slug}__mean_episode_reward_per_update.png'
            fig.savefig(png, dpi=180, bbox_inches='tight')
            plt.close(fig)
            write_png_json(
                png,
                png.with_suffix('.json'),
                {
                    'schema_version': SCHEMA_VERSION,
                    'generated_at': now_iso(),
                    'artifact_type': 'figure',
                    'title_suffix': 'mean episode reward per rollout update',
                    'run_slug': run_slug,
                    'run_id': row['run_id'],
                    'source_paths': source_paths,
                    'series': [
                        {'name': 'rollout/ep_rew_mean', 'x': x.tolist(), 'y': y.tolist()},
                        {'name': 'rollout/ep_rew_mean_moving_average', 'x': x.tolist(), 'y': ma.tolist()},
                        {'name': 'rollout/ep_rew_mean_rolling_std', 'x': x.tolist(), 'y': sigma.tolist()},
                    ],
                },
            )
            created.append(png)

    eval_cols = pick_primary_eval_columns(history)
    if 'global_step' in history.columns and eval_cols:
        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        series_payload = []
        for col in eval_cols:
            x, y = clean_series(history, 'global_step', col)
            if x.size:
                ax.plot(x, y, linewidth=2.0, label=col.replace('/mean_reward', ''))
                series_payload.append({'name': col, 'x': x.tolist(), 'y': y.tolist()})
        if series_payload:
            ax.set_xlabel('Global step')
            ax.set_ylabel('Evaluation mean reward')
            ax.set_title('Evaluation mean reward tracks')
            ax.grid(alpha=0.25)
            ax.legend(loc='best', fontsize=8)
            fig.tight_layout()
            png = figures_dir / f'{run_slug}__evaluation_mean_reward_tracks.png'
            fig.savefig(png, dpi=180, bbox_inches='tight')
            plt.close(fig)
            write_png_json(
                png,
                png.with_suffix('.json'),
                {
                    'schema_version': SCHEMA_VERSION,
                    'generated_at': now_iso(),
                    'artifact_type': 'figure',
                    'title_suffix': 'evaluation mean reward tracks',
                    'run_slug': run_slug,
                    'run_id': row['run_id'],
                    'source_paths': source_paths,
                    'series': series_payload,
                },
            )
            created.append(png)

    primary_eval = eval_cols[0] if eval_cols else None
    if primary_eval and 'global_step' in history.columns and 'rollout/ep_rew_mean' in history.columns:
        reward_x, reward_y = clean_series(history, 'global_step', 'rollout/ep_rew_mean')
        eval_x, eval_y = clean_series(history, 'global_step', primary_eval)
        if reward_x.size and eval_x.size:
            interp_eval = np.interp(reward_x, eval_x, eval_y)
            gap = interp_eval - reward_y
            fig, axes = plt.subplots(2, 1, figsize=(8.5, 6.6), sharex=True)
            axes[0].plot(reward_x, reward_y, color='#7f7f7f', linewidth=1.2, label='Mean episode reward per update')
            axes[0].plot(reward_x, moving_average(reward_y), color='#1f77b4', linewidth=2.0, label='Training MA')
            axes[0].plot(eval_x, eval_y, color='#d62728', linewidth=2.0, marker='o', markersize=3.0, label=primary_eval.replace('/mean_reward', ''))
            axes[0].set_ylabel('Reward')
            axes[0].set_title('Training vs evaluation alignment')
            axes[0].grid(alpha=0.25)
            axes[0].legend(loc='best', fontsize=8)
            axes[1].plot(reward_x, gap, color='#9467bd', linewidth=2.0)
            axes[1].axhline(0.0, color='black', linewidth=0.8, linestyle='--')
            axes[1].set_xlabel('Global step')
            axes[1].set_ylabel('Eval - training')
            axes[1].grid(alpha=0.25)
            fig.tight_layout()
            png = figures_dir / f'{run_slug}__training_vs_evaluation_alignment.png'
            fig.savefig(png, dpi=180, bbox_inches='tight')
            plt.close(fig)
            write_png_json(
                png,
                png.with_suffix('.json'),
                {
                    'schema_version': SCHEMA_VERSION,
                    'generated_at': now_iso(),
                    'artifact_type': 'figure',
                    'title_suffix': 'training vs evaluation alignment',
                    'run_slug': run_slug,
                    'run_id': row['run_id'],
                    'source_paths': source_paths,
                    'series': [
                        {'name': 'rollout/ep_rew_mean', 'x': reward_x.tolist(), 'y': reward_y.tolist()},
                        {'name': primary_eval, 'x': eval_x.tolist(), 'y': eval_y.tolist()},
                        {'name': f'{primary_eval}_minus_rollout_ep_rew_mean', 'x': reward_x.tolist(), 'y': gap.tolist()},
                    ],
                },
            )
            created.append(png)

    tracks = collect_checkpoint_tracks(row)
    if tracks:
        main_track = main_checkpoint_track_name(row, tracks)
        ordered = sorted(tracks, key=lambda item: item['track'])
        labels = [item['track'] for item in ordered]
        bests = np.array([item['best_mean'] for item in ordered], dtype=float)
        finals = np.array([item['final_mean'] for item in ordered], dtype=float)
        ypos = np.arange(len(labels))
        fig, ax = plt.subplots(figsize=(9, max(3.8, 0.6 * len(labels) + 1.5)))
        ax.barh(ypos - 0.18, bests, height=0.36, color='#2ca02c', label='Best checkpoint mean reward')
        ax.barh(ypos + 0.18, finals, height=0.36, color='#ff7f0e', label='Final checkpoint mean reward')
        ax.set_yticks(ypos)
        ax.set_yticklabels(labels)
        ax.set_xlabel('Mean evaluation reward')
        ax.set_title('Best checkpoint vs final checkpoint evaluation')
        ax.grid(axis='x', alpha=0.25)
        ax.legend(loc='best', fontsize=8)
        fig.tight_layout()
        png = figures_dir / f'{run_slug}__best_vs_final_checkpoint_evaluation.png'
        fig.savefig(png, dpi=180, bbox_inches='tight')
        plt.close(fig)
        write_png_json(
            png,
            png.with_suffix('.json'),
            {
                'schema_version': SCHEMA_VERSION,
                'generated_at': now_iso(),
                'artifact_type': 'figure',
                'title_suffix': 'best checkpoint vs final checkpoint evaluation',
                'run_slug': run_slug,
                'run_id': row['run_id'],
                'source_paths': source_paths + [str(bundle_path(row) / 'models' / 'checkpoints')],
                'main_track': main_track,
                'series': [
                    {
                        'track': item['track'],
                        'best_mean': item['best_mean'],
                        'final_mean': item['final_mean'],
                        'gap_to_best': item['gap_to_best'],
                    }
                    for item in ordered
                ],
            },
        )
        created.append(png)

    return created


def build_checkpoint_gap_table(run_catalog: pd.DataFrame) -> pd.DataFrame:
    rows = []
    learned = run_catalog[run_catalog['learned_run'] == True].copy()
    final113_names = {
        'fertilization_core': 'Fertilization core',
        'crop_planning_nonhier': 'Crop planning non-hierarchical',
        'crop_planning_hierarchical_guarded_rerun': 'Crop planning hierarchical guarded reruns',
        'fertilization_dqn_rerun': 'Fertilization DQN reruns',
        'crop_planning_dqn_rerun': 'Crop planning DQN reruns',
    }
    for _, row in learned.iterrows():
        tracks = collect_checkpoint_tracks(row)
        if not tracks:
            continue
        main_track = main_checkpoint_track_name(row, tracks)
        main = next((track for track in tracks if track['track'] == main_track), tracks[0])
        group_name = final113_names.get(row['report_group'], row['report_group']) if row['dataset'] == 'final_113' else POINT_TITLES.get(row['point'], row['point'])
        rows.append({
            'dataset': row['dataset'],
            'group_name': group_name,
            'run_slug': row['run_slug'],
            'main_checkpoint_track': main['track'],
            'best_checkpoint_mean': main['best_mean'],
            'final_checkpoint_mean': main['final_mean'],
            'final_minus_best_checkpoint': main['gap_to_best'],
            'best_minus_final_checkpoint': -main['gap_to_best'],
        })
    return pd.DataFrame(rows)


def generate_group_quality_figures(output_root: Path, checkpoint_gap_df: pd.DataFrame) -> list[Path]:
    created: list[Path] = []
    if checkpoint_gap_df.empty:
        return created
    for dataset in ['final_113', 'final_42_ablation']:
        subset = checkpoint_gap_df[checkpoint_gap_df['dataset'] == dataset].copy()
        if subset.empty:
            continue
        grouped = (
            subset.groupby('group_name')['best_minus_final_checkpoint']
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )
        fig, ax = plt.subplots(figsize=(10, max(4.0, 0.55 * len(grouped) + 1.0)))
        ax.barh(grouped['group_name'], grouped['best_minus_final_checkpoint'], color='#4c78a8')
        ax.set_xlabel('Best checkpoint - final checkpoint mean reward')
        ax.set_ylabel('Group')
        ax.set_title('Mean checkpoint regression by group')
        ax.grid(axis='x', alpha=0.25)
        fig.tight_layout()
        png = output_root / 'figures' / 'grouped' / dataset / f'{dataset}__checkpoint_regression_by_group.png'
        png.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png, dpi=180, bbox_inches='tight')
        plt.close(fig)
        write_png_json(
            png,
            png.with_suffix('.json'),
            {
                'schema_version': SCHEMA_VERSION,
                'generated_at': now_iso(),
                'artifact_type': 'figure',
                'title_suffix': 'checkpoint regression by group',
                'dataset': dataset,
                'source_paths': ['artifacts/final_successful_runs/thesis_reporting_pack/catalogs/run_catalog.csv'],
                'series': grouped.to_dict(orient='records'),
            },
        )
        created.append(png)
    return created


def rep_gallery(output_root: Path, rep_index: pd.DataFrame, dataset: str, family_slug: str, caption: str, label: str) -> str:
    subset = rep_index[(rep_index['dataset'] == dataset) & (rep_index['family_slug'] == family_slug)].copy()
    items = []
    for _, row in subset.iterrows():
        src = Path(str(row['copied_render']))
        parts = src.parts
        start = parts.index('representative_sets')
        rel_path = Path('figures') / 'representatives' / Path(*parts[start + 1 :])
        path = output_root / rel_path
        if path.exists():
            items.append((rel(path, output_root), f"{row['selection_reason']} for {row['run_slug']}"))
    if not items:
        return ''
    return fig_grid(items[:3], caption, label)


def write_sections(output_root: Path, build_summary: dict, final_summary: dict, run_catalog: pd.DataFrame, rep_index: pd.DataFrame, exemplars: pd.DataFrame) -> list[Path]:
    sections_dir = output_root / 'sections'
    sections_dir.mkdir(parents=True, exist_ok=True)
    ex = {row['key']: row for _, row in exemplars.iterrows()}
    best_fert = find_catalog_row(run_catalog, 'final_113', ex['best_fertilization_single']['run_slug'])
    weak_rand = find_catalog_row(run_catalog, 'final_113', ex['weak_random_weather_fertilization']['run_slug'])
    best_crop = find_catalog_row(run_catalog, 'final_113', ex['best_crop_nonhier_single']['run_slug'])
    best_hier = find_catalog_row(run_catalog, 'final_113', ex['best_hierarchical_single']['run_slug'])
    best_dqn = find_catalog_row(run_catalog, 'final_113', ex['best_dqn_descriptive']['run_slug'])
    p1_fixed = find_catalog_row(run_catalog, 'final_42_ablation', ex['point1_fixed_weather_no_entropy']['run_slug'])
    p1_rand = find_catalog_row(run_catalog, 'final_42_ablation', ex['point1_random_weather_with_entropy']['run_slug'])
    p2_a2c = find_catalog_row(run_catalog, 'final_42_ablation', ex['point2_best_a2c_fixed']['run_slug'])
    p2_ppo = find_catalog_row(run_catalog, 'final_42_ablation', ex['point2_best_ppo_random']['run_slug'])
    p3_fixed = find_catalog_row(run_catalog, 'final_42_ablation', ex['point3_best_fixed_default_weight']['run_slug'])
    p3_rand = find_catalog_row(run_catalog, 'final_42_ablation', ex['point3_best_random_high_weight']['run_slug'])
    p3_low = find_catalog_row(run_catalog, 'final_42_ablation', ex['point3_weak_fixed_low_weight']['run_slug'])
    datasets = {item['dataset']: item for item in build_summary['datasets']}
    best_groups = final_summary['best_groups']

    overview = textwrap.dedent(f'''
    \\chapter{{Scope, Provenance, and Audit Status}}

    This report package documents the canonical thesis experiment corpus as audited on 2026-03-20.
    The request referenced "133+42" runs, but the frozen audited corpus used here contains 155 canonical runs:
    113 final-matrix runs plus 42 ablation runs. All discussion in this report is anchored to immutable artifacts under the thesis reporting pack.

    \\input{{tables/tex/dataset_overview.tex}}

    The 113-run matrix contributes {fmt_int(datasets['final_113']['expected_runs'])} canonical runs, all with matched recovered histories and {fmt_int(datasets['final_113']['learned_runs'])} learned policies.
    The 42-run ablation suite contributes {fmt_int(datasets['final_42_ablation']['expected_runs'])} canonical runs, all with matched recovered histories and no skipped reporting artifacts.

    \\input{{tables/tex/qa_summary.tex}}

    The reused QA matters because the source pack had zero CSV files without JSON companions, zero PNG files without JSON companions, and zero runs missing run-level metrics JSON.

    {fig_single('figures/grouped/final_113/final_113__artifact_completeness.png', 'Artifact completeness summary for the 113-run matrix.', 'fig:final113_artifacts')}

    {fig_single('figures/grouped/final_42_ablation/final_42_ablation__artifact_completeness.png', 'Artifact completeness summary for the 42-run ablation suite.', 'fig:final42_artifacts')}
    ''').strip() + '\n'

    design = textwrap.dedent('''
    \\chapter{Experimental Design and Reporting Contract}

    The report covers two distinct experiment families.
    The 113-run matrix establishes broad method and environment choices.
    The 42-run ablation suite refines those choices by testing targeted modifications.

    \\input{tables/tex/final113_report_group_counts.tex}
    \\input{tables/tex/ablation_point_counts.tex}
    \\input{tables/tex/selected_exemplars.tex}

    The copied exemplar runs are included so the LaTeX package contains every graph type needed for a detailed report:
    training reward, episode length, primary metric, checkpoint evaluation, diagnostics, grouped comparisons, runtime plots,
    policy renders, and for point 2 the weekly NPK, compliance, crop-decision, and blocked-cost figures.
    ''').strip() + '\n'

    final113 = textwrap.dedent(f'''
    \\chapter{{Results From the 113-Run Final Matrix}}

    The 113-run matrix answers the broad question of which algorithm and environment combinations are strong enough to become thesis references.
    The extra diagnostic figures added in this revision are important because a smooth training curve is not enough in reinforcement learning:
    policies can peak early, overfit to the easiest evaluation track, or finish below their own best checkpoint.

    \\input{{tables/tex/final113_best_groups.tex}}
    \\input{{tables/tex/final113_best_single_runs.tex}}
    \\input{{tables/tex/checkpoint_gap_summary.tex}}

    The grouped fertilization winner was {latex_escape(best_groups['fertilization_core']['group_key'])} with mean deterministic return {fmt_num(best_groups['fertilization_core']['mean'])}.
    The grouped non-hierarchical crop-planning winner was {latex_escape(best_groups['crop_planning_nonhier']['group_key'])} with mean evaluation reward {fmt_num(best_groups['crop_planning_nonhier']['mean'], 3)}.
    The grouped hierarchical guarded-rerun winner was {latex_escape(best_groups['crop_planning_hierarchical_guarded_rerun']['group_key'])} with mean deterministic return {fmt_num(best_groups['crop_planning_hierarchical_guarded_rerun']['mean'])}.

    {fig_single('figures/grouped/final_113/final_113__leaderboard_primary_metric.png', 'Grouped leaderboard for the 113-run final matrix.', 'fig:final113_leaderboard')}
    {fig_single('figures/grouped/final_113/final_113__grouped_comparison.png', 'Grouped comparison plot for the 113-run final matrix.', 'fig:final113_grouped')}
    {fig_single('figures/grouped/final_113/final_113__runtime_comparison.png', 'Runtime comparison across grouped settings in the 113-run matrix.', 'fig:final113_runtime')}
    {fig_single('figures/grouped/final_113/final_113__checkpoint_regression_by_group.png', 'Mean regression from best checkpoint to final checkpoint across report groups in the 113-run matrix.', 'fig:final113_checkpoint_regression')}

    \\section{{Fertilization Matrix}}
    Fertilization provides the strongest repeated-seed evidence. The grouped winner favors long-budget fixed-weather A2C without adaptation, while the best single copied fertilization run is \\texttt{{{latex_escape(best_fert['run_slug'])}}} with deterministic return {fmt_num(best_fert['deterministic_return'])}.
    A weaker random-weather exemplar, \\texttt{{{latex_escape(weak_rand['run_slug'])}}}, finishes at {fmt_num(weak_rand['deterministic_return'])}, which shows how much harder the stochastic regime is.
    The new checkpoint-regression summary matters here because it separates policies that simply climb during training from policies that actually keep their best evaluation behavior through the final checkpoint.

    \\input{{tables/tex/final113_fertilization_top_groups.tex}}
    {fig_single('figures/grouped/final_113/final_113__uplift_vs_baseline.png', 'Grouped uplift against baseline for the 113-run final matrix.', 'fig:final113_uplift')}

    \\section{{Non-Hierarchical Crop Planning}}
    The grouped non-hierarchical winner is stable fixed-weather PPO without adaptation, but the best single run is \\texttt{{{latex_escape(best_crop['run_slug'])}}} with evaluation reward {fmt_num(best_crop['eval_det_mean_reward'], 3)}.
    This shows why grouped winners and best isolated runs must be interpreted together rather than substituted for one another.
    The extra evaluation-track plots in the appendix now make it possible to see whether a run is improving only on the easiest track or across held-out tracks as well.

    \\input{{tables/tex/final113_crop_nonhier_groups.tex}}

    \\section{{Hierarchical Guarded Reruns}}
    The guarded hierarchical reruns must stay separate from the non-hierarchical leaderboard because the guardrails change the decision process itself.
    The strongest copied hierarchical exemplar is \\texttt{{{latex_escape(best_hier['run_slug'])}}} with deterministic return {fmt_num(best_hier['deterministic_return'])}.

    \\input{{tables/tex/final113_hierarchical_groups.tex}}

    \\section{{DQN Reruns}}
    DQN remains descriptive-only in this corpus. The best copied DQN exemplar is \\texttt{{{latex_escape(best_dqn['run_slug'])}}} with primary metric {fmt_num(best_dqn['primary_metric_value'], 3)}.

    \\input{{tables/tex/final113_dqn_descriptive.tex}}
    ''').strip() + '\n'

    ablation = textwrap.dedent(f'''
    \\chapter{{Results From the 42-Run Ablation Suite}}

    The ablation suite asks narrower design questions than the matrix phase, so it is the place to interpret local causal changes rather than global model-family choices.
    This revision adds extra RL-health figures here as well, especially checkpoint-regression plots and explicit evaluation-track plots, because ablation claims should depend on actual evaluation behavior rather than only on smooth rollout curves.

    {fig_single('figures/grouped/final_42_ablation/final_42_ablation__runtime_comparison.png', 'Runtime comparison across the 42-run ablation suite.', 'fig:final42_runtime')}
    {fig_single('figures/grouped/final_42_ablation/final_42_ablation__checkpoint_regression_by_group.png', 'Mean regression from best checkpoint to final checkpoint across ablation families.', 'fig:final42_checkpoint_regression')}

    \\section{{Entropy Coefficient in Fertilization}}
    The entropy-coefficient ablation shows that extra entropy is regime-dependent. Under fixed weather, entropy 0.00 outperformed 0.01. Under random weather, entropy 0.01 outperformed 0.00 and the paired random-weather deterministic delta was positive with p=0.010566.

    \\input{{tables/tex/fertilization_entropy_ablation_summary.tex}}
    \\input{{tables/tex/fertilization_entropy_ablation_paired_stats.tex}}
    {fig_single('figures/grouped/final_42_ablation/fertilization_entropy_ablation__primary_metric.png', 'Entropy-coefficient ablation in fertilization across weather regimes.', 'fig:entropy_fertilization_primary')}
    {fig_single('figures/grouped/final_42_ablation/fertilization_entropy_ablation__paired_deltas.png', 'Matched-seed deltas for the fertilization entropy ablation.', 'fig:entropy_fertilization_paired')}

    The copied exemplars \\texttt{{{latex_escape(p1_fixed['run_slug'])}}} and \\texttt{{{latex_escape(p1_rand['run_slug'])}}} make the contrast concrete: lower entropy is cleaner for the fixed regime, while higher entropy helps in the stochastic regime.

    \\section{{Blocked-Nutrient Penalty in Hierarchical Crop Planning}}
    The blocked-nutrient-penalty ablation shows that shaping helped A2C more than PPO. Compliance stayed saturated at 1.0, so the shaping term changed optimization dynamics more than explicit guardrail satisfaction.

    \\input{{tables/tex/hierarchical_crop_planning_blocked_nutrient_penalty_summary.tex}}
    {fig_single('figures/grouped/final_42_ablation/hierarchical_crop_planning_blocked_nutrient_penalty__primary_comparison.png', 'Blocked-nutrient-penalty comparison in hierarchical crop planning.', 'fig:blocked_nutrient_primary')}
    {fig_single('figures/grouped/final_42_ablation/hierarchical_crop_planning_blocked_nutrient_penalty__compliance.png', 'Compliance behavior under the blocked-nutrient-penalty ablation.', 'fig:blocked_nutrient_compliance')}

    The key copied exemplars are \\texttt{{{latex_escape(p2_a2c['run_slug'])}}} and \\texttt{{{latex_escape(p2_ppo['run_slug'])}}}. They show that A2C benefited from shaping in the fixed regime, while PPO remained strongest without additional penalty in the random regime.

    \\section{{Nutrient Cost Weight in Fertilization}}
    The nutrient-cost-weight ablation shows that cost weight 1.0 remains the safest default. Weight 1.2 is effectively tied and slightly strongest in random weather, while 0.8 is consistently weaker.

    \\input{{tables/tex/fertilization_nutrient_cost_weight_summary.tex}}
    \\input{{tables/tex/fertilization_nutrient_cost_weight_paired_stats.tex}}
    {fig_single('figures/grouped/final_42_ablation/fertilization_nutrient_cost_weight_ablation__primary_metric.png', 'Nutrient-cost-weight ablation in fertilization across weather regimes.', 'fig:nutrient_cost_primary')}
    {fig_single('figures/grouped/final_42_ablation/fertilization_nutrient_cost_weight_ablation__paired_deltas.png', 'Matched-seed deltas for the fertilization nutrient-cost-weight ablation.', 'fig:nutrient_cost_paired')}

    The copied cost-weight exemplars are \\texttt{{{latex_escape(p3_fixed['run_slug'])}}}, \\texttt{{{latex_escape(p3_rand['run_slug'])}}}, and \\texttt{{{latex_escape(p3_low['run_slug'])}}}.
    Taken together, they support keeping the default nutrient-cost balance unless there is a separate modeling reason to bias harder toward nutrient cost.
    ''').strip() + '\n'

    cross = textwrap.dedent('''
    \\chapter{Cross-Study Conclusions and Practical Recommendations}

    The combined result of the 113-run matrix and the 42-run ablation suite is a set of domain-specific recommendations rather than one universal winner.

    First, fixed-weather settings remain the cleanest way to obtain stable high-return fertilization references.
    Second, non-hierarchical crop planning should still be reported separately from the guarded hierarchical reruns.
    Third, the ablation suite refines the optimization story: extra entropy helps random-weather fertilization but not fixed-weather fertilization; blocked-nutrient shaping helps A2C more than PPO in the hierarchical setting; and nutrient-cost weight 1.0 remains the safest default.

    A concise recommendation list for future inference and reporting is therefore:
    \\begin{enumerate}
    \\item Use grouped winners from the 113-run matrix as thesis reference settings, not just isolated single-run outliers.
    \\item Keep hierarchical guarded reruns in a dedicated subsection in any final document or presentation.
    \\item For fertilization in random weather, prefer the higher-entropy ablation result over the fixed-weather preference.
    \\item Keep nutrient-cost weight at 1.0 unless a deliberate robustness study justifies 1.2.
    \\item Treat DQN outputs as descriptive context rather than as primary evidence.
    \\end{enumerate}

    The report package is operationally ready because all cited figures are copied locally into this folder, the source pack had no missing CSV/JSON or PNG/JSON companions, and the 12 point-2 runs without vec-normalize files were already validated as reportable.
    ''').strip() + '\n'

    appendix_training = textwrap.dedent(f'''
    \\chapter{{Appendix: Exemplar Training Curves}}

    This appendix collects representative training figures for the copied exemplar runs so the report package contains every graph family used in the thesis reporting workflow.
    In addition to the original training plots, it now includes explicit mean-episode-reward, evaluation-track, training-vs-evaluation-alignment, and best-vs-final-checkpoint figures.

    \\section{{113-Run Matrix Exemplars}}
    {training_panel(output_root, best_fert['run_slug'])}
    {checkpoint_fig(output_root, best_fert['run_slug'])}
    {extra_quality_figs(output_root, best_fert['run_slug'])}
    {training_panel(output_root, weak_rand['run_slug'])}
    {extra_quality_figs(output_root, weak_rand['run_slug'])}
    {training_panel(output_root, best_crop['run_slug'])}
    {checkpoint_fig(output_root, best_crop['run_slug'])}
    {extra_quality_figs(output_root, best_crop['run_slug'])}
    {training_panel(output_root, best_hier['run_slug'])}
    {extra_quality_figs(output_root, best_hier['run_slug'])}
    {training_panel(output_root, best_dqn['run_slug'])}
    {extra_quality_figs(output_root, best_dqn['run_slug'])}

    \\section{{42-Run Ablation Exemplars}}
    {training_panel(output_root, p1_fixed['run_slug'])}
    {extra_quality_figs(output_root, p1_fixed['run_slug'])}
    {training_panel(output_root, p1_rand['run_slug'])}
    {extra_quality_figs(output_root, p1_rand['run_slug'])}
    {training_panel(output_root, p3_fixed['run_slug'])}
    {extra_quality_figs(output_root, p3_fixed['run_slug'])}
    {training_panel(output_root, p3_rand['run_slug'])}
    {extra_quality_figs(output_root, p3_rand['run_slug'])}
    {training_panel(output_root, p2_a2c['run_slug'])}
    {extra_quality_figs(output_root, p2_a2c['run_slug'])}
    {training_panel(output_root, p2_ppo['run_slug'])}
    {extra_quality_figs(output_root, p2_ppo['run_slug'])}
    {fig_grid([
        (f"figures/exemplars/{p2_a2c['run_slug']}/{p2_a2c['run_slug']}__weekly_npk_behavior.png", 'Weekly NPK behavior'),
        (f"figures/exemplars/{p2_a2c['run_slug']}/{p2_a2c['run_slug']}__crop_decision_timeline.png", 'Crop decision timeline'),
        (f"figures/exemplars/{p2_a2c['run_slug']}/{p2_a2c['run_slug']}__compliance_summary.png", 'Compliance summary'),
        (f"figures/exemplars/{p2_a2c['run_slug']}/{p2_a2c['run_slug']}__blocked_cost_summary.png", 'Blocked-cost summary'),
    ], f'Process-level blocked-nutrient-penalty figures for {p2_a2c['run_slug']}.', f'fig:{p2_a2c['run_slug']}:process')}
    {fig_grid([
        (f"figures/exemplars/{p2_ppo['run_slug']}/{p2_ppo['run_slug']}__weekly_npk_behavior.png", 'Weekly NPK behavior'),
        (f"figures/exemplars/{p2_ppo['run_slug']}/{p2_ppo['run_slug']}__crop_decision_timeline.png", 'Crop decision timeline'),
        (f"figures/exemplars/{p2_ppo['run_slug']}/{p2_ppo['run_slug']}__compliance_summary.png", 'Compliance summary'),
        (f"figures/exemplars/{p2_ppo['run_slug']}/{p2_ppo['run_slug']}__blocked_cost_summary.png", 'Blocked-cost summary'),
    ], f'Process-level blocked-nutrient-penalty figures for {p2_ppo['run_slug']}.', f'fig:{p2_ppo['run_slug']}:process')}
    ''').strip() + '\n'

    appendix_renders = textwrap.dedent(f'''
    \\chapter{{Appendix: Representative Render Gallery}}

    Representative renders are copied from the thesis reporting pack so this report folder can be zipped and sent without external dependencies.

    {rep_gallery(output_root, rep_index, 'final_113', 'fertilization_core_a2c_nonadaptive_fixed_weather_years_5000', 'Representative fertilization renders for the grouped winner family in the 113-run matrix.', 'fig:rep_fertilization')}
    {rep_gallery(output_root, rep_index, 'final_113', 'crop_planning_nonhier_ppo_nonadaptive_fixed_weather', 'Representative non-hierarchical crop-planning renders for the grouped winner family.', 'fig:rep_nonhier')}
    {rep_gallery(output_root, rep_index, 'final_113', 'crop_planning_hierarchical_guarded_rerun_ppo_fixed_weather_guarded_rerun', 'Representative guarded hierarchical family.', 'fig:rep_hier')}
    {rep_gallery(output_root, rep_index, 'final_42_ablation', 'point1_random_weather_ent_0_01', 'Representative renders for the random-weather entropy winner family.', 'fig:rep_point1')}
    {rep_gallery(output_root, rep_index, 'final_42_ablation', 'point2_a2c_fixed_weather', 'Representative renders for the point-2 A2C fixed-weather family.', 'fig:rep_point2')}
    {rep_gallery(output_root, rep_index, 'final_42_ablation', 'point3_fixed_weather_cost_1_0', 'Representative renders for the point-3 default-cost fixed-weather family.', 'fig:rep_point3')}

    \\input{{tables/tex/representative_families.tex}}
    ''').strip() + '\n'

    appendix_repro = textwrap.dedent('''
    \\chapter{Appendix: Reproducibility Notes}

    This report package is source-complete but not locally compiled.
    The machine used to build it did not have pdflatex, xelatex, latexmk, tectonic, or pandoc installed.
    Compile on another machine with a TeX toolchain or upload the folder to Overleaf.

    The source tree contains \\texttt{main.tex}, the section files, copied PNG/JSON figures, source CSV/JSON tables, derived LaTeX tables, copied catalogs, copied QA artifacts, and package-level metadata.
    ''').strip() + '\n'

    sections = {
        '01_overview.tex': overview,
        '02_design.tex': design,
        '03_final113_results.tex': final113,
        '04_ablation_results.tex': ablation,
        '05_cross_study.tex': cross,
        'appendix_a_training_curves.tex': appendix_training,
        'appendix_b_representative_renders.tex': appendix_renders,
        'appendix_c_reproducibility.tex': appendix_repro,
    }
    written = []
    for name, content in sections.items():
        path = sections_dir / name
        path.write_text(content, encoding='utf-8')
        written.append(path)
    return written


def write_main_tex(output_root: Path) -> Path:
    content = textwrap.dedent(r'''
    \documentclass[11pt,a4paper]{report}
    \usepackage[T1]{fontenc}
    \usepackage[utf8]{inputenc}
    \usepackage[margin=1in]{geometry}
    \usepackage{graphicx}
    \usepackage{booktabs}
    \usepackage{longtable}
    \usepackage{array}
    \usepackage{float}
    \usepackage{pdflscape}
    \usepackage{hyperref}
    \usepackage{subcaption}
    \usepackage{caption}
    \usepackage{adjustbox}
    \hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue,pdftitle={Final Experiments Report},pdfauthor={Codex}}
    \begin{document}
    \begin{titlepage}
    \centering
    {\LARGE Final Experiments Report\par}
    \vspace{1em}
    {\large Canonical thesis experiment corpus: 113 final-matrix runs + 42 ablation runs = 155 audited runs\par}
    \vspace{2em}
    {\large Generated from the immutable thesis reporting pack on 2026-03-20\par}
    \vfill
    {\large Self-contained LaTeX source package\par}
    \end{titlepage}
    \pagenumbering{roman}
    \tableofcontents
    \clearpage
    \pagenumbering{arabic}
    \input{sections/01_overview}
    \clearpage
    \input{sections/02_design}
    \clearpage
    \input{sections/03_final113_results}
    \clearpage
    \input{sections/04_ablation_results}
    \clearpage
    \input{sections/05_cross_study}
    \clearpage
    \appendix
    \input{sections/appendix_a_training_curves}
    \clearpage
    \input{sections/appendix_b_representative_renders}
    \clearpage
    \input{sections/appendix_c_reproducibility}
    \end{document}
    ''').strip() + '\n'
    path = output_root / 'main.tex'
    path.write_text(content, encoding='utf-8')
    return path


def write_docs(output_root: Path, metadata: dict) -> None:
    readme = textwrap.dedent('''
    # Final Experiments Report

    This folder is a self-contained LaTeX source package for the canonical thesis experiment report.

    Count correction:
    - The request referenced `133 + 42`.
    - The audited canonical corpus used here is `113 + 42 = 155` runs.

    Contents:
    - `main.tex`: root LaTeX document
    - `sections/`: chapter and appendix source files
    - `figures/`: copied PNG figures and JSON companions used by the report
    - `tables/`: copied grouped CSV/JSON tables plus derived CSV/JSON/TeX tables
    - `data/catalogs/`: copied reporting-pack catalogs
    - `data/qa/`: copied QA verification artifacts
    - `report_metadata.json`: package metadata and source references

    This machine did not have a TeX compiler installed when the package was generated, so the package is source-only.
    Compile on another machine with `latexmk -pdf main.tex` or upload the folder to Overleaf.
    ''').strip() + '\n'
    build = textwrap.dedent('''
    # Build Instructions

    Recommended:
    ```bash
    latexmk -pdf -interaction=nonstopmode -file-line-error main.tex
    ```

    If `latexmk` is unavailable:
    ```bash
    pdflatex main.tex
    pdflatex main.tex
    ```
    ''').strip() + '\n'
    (output_root / 'README.md').write_text(readme, encoding='utf-8')
    (output_root / 'BUILD.md').write_text(build, encoding='utf-8')
    write_json(output_root / 'report_metadata.json', metadata)


def build_asset_manifest(output_root: Path) -> dict:
    rows = []
    for path in sorted(output_root.rglob('*')):
        if path.is_file():
            rows.append({'relative_path': rel(path, output_root), 'suffix': path.suffix.lower(), 'size_bytes': path.stat().st_size})
    data_dir = output_root / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest_csv = data_dir / 'asset_manifest.csv'
    manifest_json = data_dir / 'asset_manifest.json'
    pd.DataFrame(rows).to_csv(manifest_csv, index=False)
    write_json(manifest_json, {'schema_version': SCHEMA_VERSION, 'generated_at': now_iso(), 'row_count': len(rows), 'rows': rows})
    counts = pd.DataFrame(rows).groupby('suffix').size().rename('file_count').reset_index().sort_values('suffix') if rows else pd.DataFrame(columns=['suffix', 'file_count'])
    table_paths = write_table_triplet('report_asset_counts', counts, 'File counts in the final report package by suffix.', 'tab:report_asset_counts', output_root, ['generated internally from final_experiments_report contents'])
    return {'csv': manifest_csv, 'json': manifest_json, 'row_count': len(rows), 'counts_table': table_paths}


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_root)
    ensure_clean(output_root, args.overwrite)

    build_summary = read_json(PACK_ROOT / 'qa' / 'build_summary.json')
    build_verification = read_json(PACK_ROOT / 'qa' / 'build_verification.json')
    smoke_tests = read_json(PACK_ROOT / 'qa' / 'smoke_tests.json')
    final_summary = read_json(REPO_ROOT / 'artifacts' / 'final_successful_runs' / 'final_113' / 'reporting' / 'final_reporting_summary.json')
    run_catalog = pd.read_csv(PACK_ROOT / 'catalogs' / 'run_catalog.csv')
    rep_index = pd.read_csv(PACK_ROOT / 'catalogs' / 'representative_index.csv')
    grouped113 = pd.read_csv(PACK_ROOT / 'final_113' / 'tables' / 'grouped' / 'final_113__grouped_metrics.csv')
    point1_grouped = pd.read_csv(PACK_ROOT / 'final_42_ablation' / 'tables' / 'grouped' / 'final_42_ablation__point1_grouped_metrics.csv')
    point1_paired = pd.read_csv(PACK_ROOT / 'final_42_ablation' / 'tables' / 'grouped' / 'final_42_ablation__point1_paired_stats.csv')
    point2_grouped = pd.read_csv(PACK_ROOT / 'final_42_ablation' / 'tables' / 'grouped' / 'final_42_ablation__point2_grouped_metrics.csv')
    point3_grouped = pd.read_csv(PACK_ROOT / 'final_42_ablation' / 'tables' / 'grouped' / 'final_42_ablation__point3_grouped_metrics.csv')
    point3_paired = pd.read_csv(PACK_ROOT / 'final_42_ablation' / 'tables' / 'grouped' / 'final_42_ablation__point3_paired_stats.csv')
    exemplars = choose_exemplars(run_catalog)

    copy_tree(PACK_ROOT / 'catalogs', output_root / 'data' / 'catalogs')
    copy_tree(PACK_ROOT / 'qa', output_root / 'data' / 'qa')
    copy_tree(PACK_ROOT / 'representative_sets', output_root / 'figures' / 'representatives')
    for name in ['FINAL_EXPERIMENTS_REPORTING.md', 'README.md']:
        src = PACK_ROOT / name
        if src.exists():
            copy_file(src, output_root / 'data' / 'source_docs' / name)

    for dataset in ['final_113', 'final_42_ablation']:
        copy_tree(PACK_ROOT / dataset / 'figures' / 'grouped', output_root / 'figures' / 'grouped' / dataset)
        copy_tree(PACK_ROOT / dataset / 'figures' / 'thesis_shortlist', output_root / 'figures' / 'thesis_shortlist' / dataset)
        copy_tree(PACK_ROOT / dataset / 'tables' / 'grouped', output_root / 'tables' / 'csv' / dataset / 'grouped')

    for (dataset, source_name), alias_name in descriptive_aliases_for_grouped_figures().items():
        src_png = output_root / 'figures' / 'grouped' / dataset / source_name
        if src_png.exists():
            copy_file(src_png, src_png.with_name(alias_name))
        src_json = src_png.with_suffix('.json')
        if src_json.exists():
            copy_file(src_json, src_json.with_name(Path(alias_name).with_suffix('.json').name))

    for _, ex in exemplars.iterrows():
        fig_dir = PACK_ROOT / ex['dataset'] / 'figures' / 'per_run'
        out_dir = output_root / 'figures' / 'exemplars' / ex['run_slug']
        for src in sorted(fig_dir.glob(f"{ex['run_slug']}__*")):
            copy_file(src, out_dir / src.name)
        copy_tree(PACK_ROOT / ex['dataset'] / 'renders' / 'per_run' / ex['run_slug'], out_dir / 'renders')

    checkpoint_gap_df = build_checkpoint_gap_table(run_catalog)
    generate_group_quality_figures(output_root, checkpoint_gap_df)
    for _, ex in exemplars.iterrows():
        row = find_catalog_row(run_catalog, str(ex['dataset']), str(ex['run_slug']))
        generate_exemplar_quality_figures(output_root, row)

    derived = build_derived_tables(output_root, build_summary, build_verification, final_summary, run_catalog, rep_index, grouped113, point1_grouped, point1_paired, point2_grouped, point3_grouped, point3_paired, exemplars, checkpoint_gap_df)
    sections = write_sections(output_root, build_summary, final_summary, run_catalog, rep_index, exemplars)
    main_tex = write_main_tex(output_root)
    asset_manifest = build_asset_manifest(output_root)

    metadata = {
        'schema_version': SCHEMA_VERSION,
        'generated_at': now_iso(),
        'package_root': str(output_root),
        'source_reporting_pack': str(PACK_ROOT),
        'count_correction_note': 'The request referenced 133+42 runs, but the audited canonical corpus is 113+42=155 runs.',
        'datasets': build_summary['datasets'],
        'verification': build_verification,
        'smoke_tests': smoke_tests,
        'selected_exemplars': exemplars.to_dict(orient='records'),
        'derived_tables': {name: {k: str(v) for k, v in paths.items()} for name, paths in derived.items()},
        'sections': [str(path) for path in sections],
        'main_tex': str(main_tex),
        'asset_manifest': {
            'csv': str(asset_manifest['csv']),
            'json': str(asset_manifest['json']),
            'row_count': asset_manifest['row_count'],
            'counts_table': {k: str(v) for k, v in asset_manifest['counts_table'].items()},
        },
        'notes': [
            'This package is source-only because no TeX compiler was installed on the build machine.',
            'All grouped figures and thesis-shortlist figures were copied from the immutable thesis reporting pack.',
            'Representative render sets were copied for both datasets.',
        ],
    }
    write_docs(output_root, metadata)


if __name__ == '__main__':
    main()
