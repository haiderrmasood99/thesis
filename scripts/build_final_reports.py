#!/usr/bin/env python3
"""Build the canonical final reporting dataset from the frozen final_113 bundle set."""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multitest import multipletests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cyclesgym.utils.paths import ARTIFACTS_PATH, FINAL_113_RUNS_PATH, FINAL_SUCCESSFUL_RUNS_PATH, PROJECT_PATH


REPORTING_PATH = FINAL_113_RUNS_PATH / "reporting"
MANIFEST_PATH = FINAL_113_RUNS_PATH / "manifest.csv"
REPLACEMENT_MAP_PATH = FINAL_113_RUNS_PATH / "replacement_map.csv"
HIERARCHICAL_EXPORT_PATH = FINAL_SUCCESSFUL_RUNS_PATH / "Recovered" / "wandb_export_2026-03-14T09_45_22.452+05_00.csv"

RUN_LEVEL_OUTPUT = REPORTING_PATH / "run_level_metrics.csv"
GROUPED_OUTPUT = REPORTING_PATH / "grouped_metrics.csv"
STATS_OUTPUT = REPORTING_PATH / "statistical_tests.csv"
AUDIT_OUTPUT = REPORTING_PATH / "artifact_completeness_audit.csv"
SUMMARY_OUTPUT = REPORTING_PATH / "final_reporting_summary.json"

REPEATED_GROUPS = {
    "fertilization_core",
    "crop_planning_nonhier",
    "crop_planning_hierarchical_guarded_rerun",
}

STATS_COLUMNS = [
    "report_group",
    "metric",
    "test_type",
    "term",
    "comparison",
    "n",
    "mean_a",
    "mean_b",
    "statistic",
    "df",
    "p_value",
    "corrected_p_value",
    "sum_sq",
    "eta_squared",
    "effect_size",
    "effect_size_kind",
    "ci_low",
    "ci_high",
    "notes",
]


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _as_rel(path: Path) -> str:
    return path.relative_to(PROJECT_PATH).as_posix()


def _to_bool(value: Any) -> Optional[bool]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float, np.floating, np.integer)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value: Any) -> Optional[int]:
    numeric = _to_float(value)
    if numeric is None:
        return None
    return int(numeric)


def _weather_label(value: Optional[bool]) -> str:
    if value is True:
        return "fixed_weather"
    if value is False:
        return "random_weather"
    return ""


def _adaptive_label(value: Optional[bool]) -> str:
    if value is True:
        return "adaptive"
    if value is False:
        return "nonadaptive"
    return ""


def _primary_metric_name(report_group: str, baseline: bool) -> str:
    if baseline:
        return "baseline_best_return"
    if report_group in {"crop_planning_nonhier", "crop_planning_dqn_rerun"}:
        return "eval_det_mean_reward"
    return "deterministic_return"


def _report_group(domain: str, method: str, hierarchical: bool, baseline: bool) -> str:
    if domain == "fertilization":
        if baseline:
            return "fertilization_baseline"
        if method == "DQN":
            return "fertilization_dqn_rerun"
        return "fertilization_core"
    if hierarchical:
        return "crop_planning_hierarchical_guarded_rerun"
    if method == "DQN":
        return "crop_planning_dqn_rerun"
    return "crop_planning_nonhier"


def _find_single_json(summary_dir: Path) -> Tuple[Optional[Path], int]:
    files = sorted(summary_dir.glob("*.json"))
    if not files:
        return None, 0
    return files[0], len(files)


def _series_stats(values: Sequence[Optional[float]]) -> Dict[str, Any]:
    clean = np.array([float(v) for v in values if v is not None and not pd.isna(v)], dtype=float)
    n = int(clean.size)
    if n == 0:
        return {"n": 0, "mean": None, "std": None, "se": None, "ci_low": None, "ci_high": None, "min": None, "max": None}
    mean = float(clean.mean())
    min_value = float(clean.min())
    max_value = float(clean.max())
    if n == 1:
        return {"n": 1, "mean": mean, "std": None, "se": None, "ci_low": mean, "ci_high": mean, "min": min_value, "max": max_value}
    std = float(clean.std(ddof=1))
    se = float(std / math.sqrt(n))
    t_value = float(stats.t.ppf(0.975, df=n - 1))
    half_width = t_value * se
    return {
        "n": n,
        "mean": mean,
        "std": std,
        "se": se,
        "ci_low": mean - half_width,
        "ci_high": mean + half_width,
        "min": min_value,
        "max": max_value,
    }


def _hedges_g(sample_a: np.ndarray, sample_b: np.ndarray) -> Optional[float]:
    n1 = sample_a.size
    n2 = sample_b.size
    if n1 < 2 or n2 < 2:
        return None
    var1 = sample_a.var(ddof=1)
    var2 = sample_b.var(ddof=1)
    pooled_num = ((n1 - 1) * var1) + ((n2 - 1) * var2)
    pooled_den = n1 + n2 - 2
    if pooled_den <= 0:
        return None
    pooled_sd = math.sqrt(pooled_num / pooled_den) if pooled_num > 0 else 0.0
    if pooled_sd == 0:
        return 0.0
    d_value = (sample_a.mean() - sample_b.mean()) / pooled_sd
    correction = 1.0 - (3.0 / ((4.0 * (n1 + n2)) - 9.0))
    return float(d_value * correction)


def _welch_df(sample_a: np.ndarray, sample_b: np.ndarray) -> Optional[float]:
    n1 = sample_a.size
    n2 = sample_b.size
    if n1 < 2 or n2 < 2:
        return None
    var1 = sample_a.var(ddof=1)
    var2 = sample_b.var(ddof=1)
    term1 = var1 / n1
    term2 = var2 / n2
    denominator = ((term1 ** 2) / (n1 - 1)) + ((term2 ** 2) / (n2 - 1))
    if denominator == 0:
        return None
    numerator = (term1 + term2) ** 2
    return float(numerator / denominator)


def _supporting_metric_fields() -> List[str]:
    return [
        "primary_metric_value",
        "deterministic_return",
        "eval_det_mean_reward",
        "eval_sto_mean_reward",
        "stochastic_return_mean",
        "stochastic_return_std",
        "pak_holdout_return",
        "baseline_best_return",
        "uplift_vs_best_baseline_det",
        "runtime_seconds",
    ]


def _group_key(report_group: str, row: Dict[str, Any]) -> str:
    method = row["method"]
    adaptive_label = row["adaptive_label"]
    weather_label = row["weather_label"]
    budget_label = row["budget_label"]
    if report_group in {"fertilization_core", "fertilization_dqn_rerun"}:
        return f"{method} | {adaptive_label} | {weather_label} | years={budget_label}"
    if report_group == "fertilization_baseline":
        return "Baseline only"
    if report_group in {"crop_planning_nonhier", "crop_planning_dqn_rerun"}:
        return f"{method} | {adaptive_label} | {weather_label}"
    return f"{method} | {weather_label} | guarded_rerun"


def _build_run_records() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    manifest_df = pd.read_csv(MANIFEST_PATH)
    replacement_df = pd.read_csv(REPLACEMENT_MAP_PATH)
    hierarchical_export_df = pd.read_csv(HIERARCHICAL_EXPORT_PATH)
    replacement_lookup = {int(row["index"]): row for _, row in replacement_df.iterrows()}
    hierarchical_export_lookup_by_name = {str(row["Name"]): row for _, row in hierarchical_export_df.iterrows()}

    run_records: List[Dict[str, Any]] = []
    audit_records: List[Dict[str, Any]] = []
    status_columns = [
        "summary_json_status",
        "config_status",
        "wandb_summary_status",
        "wandb_metadata_status",
        "requirements_status",
        "diff_patch_status",
        "output_log_status",
        "run_record_status",
        "model_zip_status",
        "models_dir_status",
        "vec_normalize_status",
        "hierarchical_report_status",
    ]

    for _, manifest_row in manifest_df.iterrows():
        index = int(manifest_row["index"])
        bundle_dir = ARTIFACTS_PATH / str(manifest_row["bundle_dir"]).replace("\\", "/")
        summary_path, summary_count = _find_single_json(bundle_dir / "summary")
        wandb_summary_path = bundle_dir / "wandb" / "wandb-summary.json"

        summary_payload = _read_json(summary_path) if summary_path is not None else {}
        wandb_summary = _read_json(wandb_summary_path)
        metrics = summary_payload.get("metrics", {}) if isinstance(summary_payload, dict) else {}

        method = str(summary_payload.get("method") or manifest_row["method"])
        domain = str(summary_payload.get("domain") or manifest_row["domain"])
        baseline = bool(summary_payload.get("baseline") or method == "BASELINE")
        hierarchical = bool(summary_payload.get("hierarchical"))
        fixed_weather = _to_bool(summary_payload.get("fixed_weather"))

        nonadaptive_value = summary_payload.get("nonadaptive")
        if nonadaptive_value is None:
            nonadaptive_value = summary_payload.get("non_adaptive")
        nonadaptive = _to_bool(nonadaptive_value)
        adaptive = None if nonadaptive is None else not nonadaptive

        run_record = {
            "index": index,
            "label": manifest_row["label"],
            "bundle_dir": _as_rel(bundle_dir),
            "summary_json_relpath": _as_rel(summary_path) if summary_path is not None else "",
            "wandb_summary_relpath": _as_rel(wandb_summary_path) if wandb_summary_path.exists() else "",
            "run_id": str(summary_payload.get("run_id") or manifest_row["run_id"]),
            "status": "finished",
            "domain": domain,
            "method": method,
            "seed": _to_int(summary_payload.get("seed")),
            "fixed_weather": fixed_weather,
            "weather_label": _weather_label(fixed_weather),
            "nonadaptive": nonadaptive,
            "adaptive": adaptive,
            "adaptive_label": _adaptive_label(adaptive),
            "hierarchical": hierarchical,
            "baseline": baseline,
            "total_years": _to_int(summary_payload.get("total_years")),
            "budget_label": "",
            "price_profile": summary_payload.get("price_profile", ""),
            "nutrient_action_mode": summary_payload.get("nutrient_action_mode", ""),
            "report_group": "",
            "primary_metric_name": "",
            "primary_metric_value": None,
            "deterministic_return": _to_float(metrics.get("deterministic_return")),
            "eval_det_mean_reward": _to_float(wandb_summary.get("eval_det/mean_reward")),
            "eval_sto_mean_reward": _to_float(wandb_summary.get("eval_sto/mean_reward")),
            "stochastic_return_mean": _to_float(metrics.get("stochastic_return_mean")),
            "stochastic_return_std": _to_float(metrics.get("stochastic_return_std")),
            "pak_holdout_return": _to_float(metrics.get("pak_holdout_return")),
            "baseline_best_return": _to_float(metrics.get("baseline_best_return") or wandb_summary.get("baseline_best_return")),
            "uplift_vs_best_baseline_det": _to_float(metrics.get("uplift_vs_best_baseline_det") or wandb_summary.get("uplift_vs_best_baseline_det")),
            "runtime_seconds": _to_float(wandb_summary.get("_runtime")),
            "source_kind": manifest_row["source_kind"],
            "source_project": manifest_row["source_project"],
            "source_run_name": manifest_row["source_run_name"],
            "source_created": manifest_row["source_created"],
            "notes": manifest_row["notes"],
            "replacement_reason": "",
            "replacement_previous_run_id": "",
            "guardrail_enforce_calendar_windows": None,
            "guardrail_limit_fertilizer_to_season": None,
            "guardrail_annual_n_budget": None,
            "guardrail_annual_p_budget": None,
            "guardrail_annual_k_budget": None,
            "hierarchical_export_match": False,
            "hierarchical_export_det_return": None,
            "hierarchical_export_eval_det_mean_reward": None,
        }

        run_record["budget_label"] = str(run_record["total_years"]) if run_record["total_years"] is not None else ("baseline" if baseline else "")
        run_record["report_group"] = _report_group(domain, method, hierarchical, baseline)
        run_record["primary_metric_name"] = _primary_metric_name(run_record["report_group"], baseline)
        run_record["primary_metric_value"] = run_record.get(run_record["primary_metric_name"])
        run_record["group_key"] = _group_key(run_record["report_group"], run_record)

        if index in replacement_lookup:
            replacement_row = replacement_lookup[index]
            run_record["replacement_reason"] = replacement_row["reason"]
            run_record["replacement_previous_run_id"] = replacement_row["previous_run_id"]

        if run_record["report_group"] == "crop_planning_hierarchical_guarded_rerun":
            export_row = hierarchical_export_lookup_by_name.get(str(manifest_row["source_run_name"]))
            if export_row is not None:
                run_record["guardrail_enforce_calendar_windows"] = _to_bool(export_row.get("enforce_calendar_windows"))
                run_record["guardrail_limit_fertilizer_to_season"] = _to_bool(export_row.get("limit_fertilizer_to_season"))
                run_record["guardrail_annual_n_budget"] = _to_float(export_row.get("annual_n_budget"))
                run_record["guardrail_annual_p_budget"] = _to_float(export_row.get("annual_p_budget"))
                run_record["guardrail_annual_k_budget"] = _to_float(export_row.get("annual_k_budget"))
                run_record["hierarchical_export_det_return"] = _to_float(export_row.get("deterministic_return"))
                run_record["hierarchical_export_eval_det_mean_reward"] = _to_float(export_row.get("eval_det/mean_reward"))
                det_match = math.isclose(
                    float(run_record["deterministic_return"] or 0.0),
                    float(run_record["hierarchical_export_det_return"] or 0.0),
                    rel_tol=0.0,
                    abs_tol=1e-6,
                )
                eval_match = math.isclose(
                    float(run_record["eval_det_mean_reward"] or 0.0),
                    float(run_record["hierarchical_export_eval_det_mean_reward"] or 0.0),
                    rel_tol=0.0,
                    abs_tol=1e-6,
                )
                run_record["hierarchical_export_match"] = bool(det_match and eval_match)

        run_records.append(run_record)

        has_hierarchical_report = any(bundle_dir.rglob("weekly_npk_log.csv")) or any(bundle_dir.rglob("yearly_crop_decisions.csv")) or any(bundle_dir.rglob("season_window_compliance.csv")) or any(bundle_dir.rglob("reporting_summary.json"))
        audit_record = {
            "index": index,
            "label": manifest_row["label"],
            "bundle_dir": _as_rel(bundle_dir),
            "summary_json_path": run_record["summary_json_relpath"],
            "summary_json_count": summary_count,
            "summary_json_present_actual": bool(summary_path is not None),
            "wandb_summary_present_actual": wandb_summary_path.exists(),
            "model_zip_present_actual": any(bundle_dir.rglob("model.zip")),
            "best_model_present_actual": any(bundle_dir.rglob("best_model.zip")),
            "vec_normalize_present_actual": any(bundle_dir.rglob("vec_normalize*.pkl")),
            "hierarchical_report_present_actual": has_hierarchical_report,
            "is_replacement": index in replacement_lookup,
            "report_group": run_record["report_group"],
            "source_kind": manifest_row["source_kind"],
            "source_project": manifest_row["source_project"],
            "notes": manifest_row["notes"],
        }
        for column in status_columns:
            audit_record[column] = manifest_row[column]
        audit_records.append(audit_record)

    run_df = pd.DataFrame(run_records).sort_values("index").reset_index(drop=True)
    audit_df = pd.DataFrame(audit_records).sort_values("index").reset_index(drop=True)
    metadata = {
        "manifest_rows": int(manifest_df.shape[0]),
        "replacement_rows": int(replacement_df.shape[0]),
        "hierarchical_export_rows": int(hierarchical_export_df.shape[0]),
    }
    return run_df, audit_df, replacement_df, metadata


def _build_grouped_metrics(run_df: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        "report_group",
        "group_key",
        "domain",
        "method",
        "adaptive",
        "adaptive_label",
        "fixed_weather",
        "weather_label",
        "hierarchical",
        "baseline",
        "total_years",
        "budget_label",
        "primary_metric_name",
    ]
    rows: List[Dict[str, Any]] = []
    for group_values, group_df in run_df.groupby(group_columns, dropna=False):
        row = dict(zip(group_columns, group_values))
        row["n"] = int(group_df.shape[0])
        row["source_kind_set"] = "|".join(sorted(group_df["source_kind"].dropna().astype(str).unique()))
        row["inferential_eligible"] = bool(row["report_group"] in REPEATED_GROUPS and row["n"] == 3)
        for metric in _supporting_metric_fields():
            metric_stats = _series_stats(group_df[metric].tolist())
            row[f"{metric}_mean"] = metric_stats["mean"]
            row[f"{metric}_std"] = metric_stats["std"]
            row[f"{metric}_se"] = metric_stats["se"]
            row[f"{metric}_ci_low"] = metric_stats["ci_low"]
            row[f"{metric}_ci_high"] = metric_stats["ci_high"]
            row[f"{metric}_min"] = metric_stats["min"]
            row[f"{metric}_max"] = metric_stats["max"]
        rows.append(row)
    grouped_df = pd.DataFrame(rows)
    return grouped_df.sort_values(["report_group", "primary_metric_value_mean"], ascending=[True, False]).reset_index(drop=True)


def _anova_rows(run_df: pd.DataFrame) -> List[Dict[str, Any]]:
    specs = [
        {
            "report_group": "fertilization_core",
            "metric": "deterministic_return",
            "formula": "deterministic_return ~ C(method) + C(adaptive_label) + C(weather_label) + C(budget_label) + C(method):C(weather_label) + C(method):C(budget_label) + C(adaptive_label):C(weather_label)",
        },
        {
            "report_group": "crop_planning_nonhier",
            "metric": "eval_det_mean_reward",
            "formula": "eval_det_mean_reward ~ C(method) + C(adaptive_label) + C(weather_label) + C(method):C(weather_label)",
        },
        {
            "report_group": "crop_planning_hierarchical_guarded_rerun",
            "metric": "deterministic_return",
            "formula": "deterministic_return ~ C(method) + C(weather_label)",
        },
    ]
    rows: List[Dict[str, Any]] = []
    for spec in specs:
        data = run_df[(run_df["report_group"] == spec["report_group"]) & run_df[spec["metric"]].notna()].copy()
        if data.empty:
            continue
        for column in ["method", "adaptive_label", "weather_label", "budget_label"]:
            if column in data.columns:
                data[column] = data[column].fillna("").astype("object")
        data[spec["metric"]] = data[spec["metric"]].astype(float)
        model = ols(spec["formula"], data=data).fit()
        anova_df = anova_lm(model, typ=2)
        total_sum_sq = float(anova_df["sum_sq"].sum())
        for term, values in anova_df.iterrows():
            rows.append(
                {
                    "report_group": spec["report_group"],
                    "metric": spec["metric"],
                    "test_type": "anova_type_ii",
                    "term": term,
                    "comparison": "",
                    "n": int(data.shape[0]),
                    "mean_a": None,
                    "mean_b": None,
                    "statistic": _to_float(values.get("F")),
                    "df": _to_float(values.get("df")),
                    "p_value": _to_float(values.get("PR(>F)")),
                    "corrected_p_value": None,
                    "sum_sq": _to_float(values.get("sum_sq")),
                    "eta_squared": (_to_float(values.get("sum_sq")) / total_sum_sq) if total_sum_sq else None,
                    "effect_size": None,
                    "effect_size_kind": "",
                    "ci_low": None,
                    "ci_high": None,
                    "notes": spec["formula"],
                }
            )
    return rows


def _pairwise_rows(run_df: pd.DataFrame, grouped_df: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for report_group in sorted(REPEATED_GROUPS):
        eligible_groups = grouped_df[
            (grouped_df["report_group"] == report_group) & (grouped_df["inferential_eligible"] == True)
        ].sort_values("primary_metric_value_mean", ascending=False)
        top_groups = eligible_groups.head(3)
        if top_groups.shape[0] < 2:
            continue

        metric_name = str(top_groups["primary_metric_name"].iloc[0])
        pending_rows: List[Dict[str, Any]] = []
        p_values: List[float] = []
        for first, second in combinations(top_groups["group_key"].tolist(), 2):
            sample_a = run_df[(run_df["report_group"] == report_group) & (run_df["group_key"] == first)][metric_name].dropna().to_numpy(dtype=float)
            sample_b = run_df[(run_df["report_group"] == report_group) & (run_df["group_key"] == second)][metric_name].dropna().to_numpy(dtype=float)
            if sample_a.size == 0 or sample_b.size == 0:
                continue
            test_result = stats.ttest_ind(sample_a, sample_b, equal_var=False)
            p_value = float(test_result.pvalue)
            p_values.append(p_value)
            pending_rows.append(
                {
                    "report_group": report_group,
                    "metric": metric_name,
                    "test_type": "pairwise_welch_t",
                    "term": "",
                    "comparison": f"{first} vs {second}",
                    "n": int(sample_a.size + sample_b.size),
                    "mean_a": float(sample_a.mean()),
                    "mean_b": float(sample_b.mean()),
                    "statistic": float(test_result.statistic),
                    "df": _welch_df(sample_a, sample_b),
                    "p_value": p_value,
                    "corrected_p_value": None,
                    "sum_sq": None,
                    "eta_squared": None,
                    "effect_size": _hedges_g(sample_a, sample_b),
                    "effect_size_kind": "hedges_g",
                    "ci_low": None,
                    "ci_high": None,
                    "notes": "top_3_repeated_groups_holm_corrected",
                }
            )
        if pending_rows:
            _, corrected, _, _ = multipletests(p_values, method="holm")
            for row, corrected_p_value in zip(pending_rows, corrected):
                row["corrected_p_value"] = float(corrected_p_value)
                rows.append(row)
    return rows


def _ci_rows(grouped_df: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    eligible = grouped_df[grouped_df["inferential_eligible"] == True]
    for _, row in eligible.iterrows():
        rows.append(
            {
                "report_group": row["report_group"],
                "metric": row["primary_metric_name"],
                "test_type": "group_ci_95",
                "term": row["group_key"],
                "comparison": "",
                "n": int(row["n"]),
                "mean_a": row["primary_metric_value_mean"],
                "mean_b": None,
                "statistic": row["primary_metric_value_mean"],
                "df": max(int(row["n"]) - 1, 0),
                "p_value": None,
                "corrected_p_value": None,
                "sum_sq": None,
                "eta_squared": None,
                "effect_size": None,
                "effect_size_kind": "",
                "ci_low": row["primary_metric_value_ci_low"],
                "ci_high": row["primary_metric_value_ci_high"],
                "notes": "t_distribution_95_ci",
            }
        )
    return rows


def _best_group_payload(grouped_df: pd.DataFrame, report_group: str) -> Dict[str, Any]:
    subset = grouped_df[grouped_df["report_group"] == report_group].sort_values("primary_metric_value_mean", ascending=False)
    if subset.empty:
        return {}
    top_row = subset.iloc[0]
    return {
        "group_key": top_row["group_key"],
        "metric": top_row["primary_metric_name"],
        "n": int(top_row["n"]),
        "mean": top_row["primary_metric_value_mean"],
        "ci_low": top_row["primary_metric_value_ci_low"],
        "ci_high": top_row["primary_metric_value_ci_high"],
    }


def _best_run_payload(run_df: pd.DataFrame, report_group: str) -> Dict[str, Any]:
    subset = run_df[(run_df["report_group"] == report_group) & run_df["primary_metric_value"].notna()].copy()
    if subset.empty:
        return {}
    best_row = subset.sort_values("primary_metric_value", ascending=False).iloc[0]
    return {
        "index": int(best_row["index"]),
        "label": best_row["label"],
        "metric": best_row["primary_metric_name"],
        "value": best_row["primary_metric_value"],
    }


def _build_summary_payload(
    run_df: pd.DataFrame,
    grouped_df: pd.DataFrame,
    stats_df: pd.DataFrame,
    audit_df: pd.DataFrame,
    replacement_df: pd.DataFrame,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    report_group_counts = {
        key: int(value) for key, value in run_df["report_group"].value_counts().sort_index().to_dict().items()
    }
    replacement_counts = {
        key: int(value) for key, value in replacement_df["source_project"].value_counts().sort_index().to_dict().items()
    }
    hierarchical_rows = run_df[run_df["report_group"] == "crop_planning_hierarchical_guarded_rerun"]
    hierarchical_guards = {
        "enforce_calendar_windows": bool(hierarchical_rows["guardrail_enforce_calendar_windows"].dropna().all()),
        "limit_fertilizer_to_season": bool(hierarchical_rows["guardrail_limit_fertilizer_to_season"].dropna().all()),
        "annual_n_budget": sorted(hierarchical_rows["guardrail_annual_n_budget"].dropna().unique().tolist()),
        "annual_p_budget": sorted(hierarchical_rows["guardrail_annual_p_budget"].dropna().unique().tolist()),
        "annual_k_budget": sorted(hierarchical_rows["guardrail_annual_k_budget"].dropna().unique().tolist()),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "canonical_source": "artifacts/final_successful_runs/final_113",
        "counts": {
            "manifest_rows": metadata["manifest_rows"],
            "replacement_rows": metadata["replacement_rows"],
            "hierarchical_export_rows": metadata["hierarchical_export_rows"],
            "run_level_rows": int(run_df.shape[0]),
            "report_group_counts": report_group_counts,
            "replacement_source_counts": replacement_counts,
        },
        "best_groups": {
            "fertilization_core": _best_group_payload(grouped_df, "fertilization_core"),
            "fertilization_dqn_rerun": _best_group_payload(grouped_df, "fertilization_dqn_rerun"),
            "crop_planning_nonhier": _best_group_payload(grouped_df, "crop_planning_nonhier"),
            "crop_planning_dqn_rerun": _best_group_payload(grouped_df, "crop_planning_dqn_rerun"),
            "crop_planning_hierarchical_guarded_rerun": _best_group_payload(grouped_df, "crop_planning_hierarchical_guarded_rerun"),
        },
        "best_single_runs": {
            "fertilization_core": _best_run_payload(run_df, "fertilization_core"),
            "crop_planning_nonhier": _best_run_payload(run_df, "crop_planning_nonhier"),
            "crop_planning_hierarchical_guarded_rerun": _best_run_payload(run_df, "crop_planning_hierarchical_guarded_rerun"),
        },
        "artifact_audit": {
            "missing_hierarchical_report_rows": int((audit_df["hierarchical_report_present_actual"] == False).sum()),
            "missing_vec_normalize_rows": int((audit_df["vec_normalize_present_actual"] == False).sum()),
            "hierarchical_rerun_missing_report_rows": int(
                audit_df[
                    (audit_df["report_group"] == "crop_planning_hierarchical_guarded_rerun")
                    & (audit_df["hierarchical_report_present_actual"] == False)
                ].shape[0]
            ),
        },
        "statistics": {
            "inferential_groups": int(grouped_df[grouped_df["inferential_eligible"] == True].shape[0]),
            "anova_rows": int((stats_df["test_type"] == "anova_type_ii").sum()),
            "pairwise_rows": int((stats_df["test_type"] == "pairwise_welch_t").sum()),
        },
        "hierarchical_guarded_rerun": {
            "row_count": int(hierarchical_rows.shape[0]),
            "guardrails": hierarchical_guards,
            "all_export_matches": bool(hierarchical_rows["hierarchical_export_match"].all()),
            "primary_metric": "deterministic_return",
            "comparability_note": "Report the corrected guarded hierarchical reruns in a dedicated subsection rather than ranking them inside the non-hierarchical crop-planning leaderboard.",
        },
        "limitations": [
            "Results remain simulation-based and are not field validated.",
            "Irrigation is not implemented as a learned action in the active training flows.",
            "The crop-planning stack remains centered on the working maize-soy configuration.",
            "Recovered hierarchical rerun bundles do not include the original thesis report directories.",
            "Recovered rerun summary JSON files were reconstructed into the frozen final_113 bundle set from recovered metadata.",
            "Inferential statistics are restricted to repeated three-seed groups; DQN reruns and the baseline row remain descriptive only.",
        ],
    }


def main() -> int:
    REPORTING_PATH.mkdir(parents=True, exist_ok=True)

    run_df, audit_df, replacement_df, metadata = _build_run_records()
    grouped_df = _build_grouped_metrics(run_df)
    stats_rows = _ci_rows(grouped_df) + _anova_rows(run_df) + _pairwise_rows(run_df, grouped_df)
    stats_df = pd.DataFrame(stats_rows, columns=STATS_COLUMNS)
    summary_payload = _build_summary_payload(run_df, grouped_df, stats_df, audit_df, replacement_df, metadata)

    run_df.to_csv(RUN_LEVEL_OUTPUT, index=False)
    grouped_df.to_csv(GROUPED_OUTPUT, index=False)
    stats_df.to_csv(STATS_OUTPUT, index=False)
    audit_df.to_csv(AUDIT_OUTPUT, index=False)
    SUMMARY_OUTPUT.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    print(f"Wrote: {RUN_LEVEL_OUTPUT}")
    print(f"Wrote: {GROUPED_OUTPUT}")
    print(f"Wrote: {STATS_OUTPUT}")
    print(f"Wrote: {AUDIT_OUTPUT}")
    print(f"Wrote: {SUMMARY_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
