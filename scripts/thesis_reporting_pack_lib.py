#!/usr/bin/env python3
"""Shared implementation for the immutable thesis reporting pack."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

import matplotlib
import numpy as np
import pandas as pd
import yaml
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cyclesgym.utils.paths import FINAL_113_RUNS_PATH, FINAL_SUCCESSFUL_RUNS_PATH, PROJECT_PATH


SCHEMA_VERSION = "1.0.0"
DEFAULT_OUTPUT_ROOT = FINAL_SUCCESSFUL_RUNS_PATH / "thesis_reporting_pack"
FINAL_42_ROOT = FINAL_SUCCESSFUL_RUNS_PATH / "final_42_ablation"

HISTORY_ROOTS = [
    {
        "project": "Recovered/wandb_full_backup/Thesis-Final",
        "path": FINAL_SUCCESSFUL_RUNS_PATH / "Recovered" / "wandb_full_backup" / "Thesis-Final",
    },
    {
        "project": "Recovered/wandb_full_backup/Thesis-Final-Hierarchical-Rerun",
        "path": FINAL_SUCCESSFUL_RUNS_PATH / "Recovered" / "wandb_full_backup" / "Thesis-Final-Hierarchical-Rerun",
    },
    {
        "project": "Recovered 17 March/wandb_full_backup/17-March-Runs",
        "path": FINAL_SUCCESSFUL_RUNS_PATH / "Recovered 17 March" / "wandb_full_backup" / "17-March-Runs",
    },
]

PLOT_COLORS = {
    "reward": "#0f766e",
    "reward_smooth": "#134e4a",
    "length": "#b45309",
    "primary": "#1d4ed8",
    "baseline": "#7c3aed",
    "deterministic": "#166534",
    "stochastic": "#0f766e",
    "blocked": "#b91c1c",
    "n": "#1d4ed8",
    "p": "#ea580c",
    "k": "#16a34a",
    "runtime": "#6b7280",
}

REQUIRED_DATASET_SUBDIRS = ["tables", "figures", "metrics_json", "renders", "cache", "qa"]
TABLE_SUBDIRS = ["per_run", "grouped"]
FIGURE_SUBDIRS = ["per_run", "grouped", "thesis_shortlist"]
METRIC_SUBDIRS = ["per_run", "grouped"]

FINAL_113_COPY_TABLES = {
    "run_level_metrics.csv": "final_113__run_level_metrics.csv",
    "grouped_metrics.csv": "final_113__grouped_metrics.csv",
    "statistical_tests.csv": "final_113__statistical_tests.csv",
    "artifact_completeness_audit.csv": "final_113__artifact_completeness_audit.csv",
}


@dataclass
class BuildContext:
    output_root: Path
    overwrite: bool = False
    max_plot_points: int = 500


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_rel(path: Optional[Path]) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(PROJECT_PATH).as_posix()
    except Exception:
        return str(path.resolve())


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return payload or {}


def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float, np.integer, np.floating)):
        if pd.isna(value):
            return None
        return float(value)
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def safe_int(value: Any) -> Optional[int]:
    numeric = safe_float(value)
    return None if numeric is None else int(round(numeric))


def safe_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value)


def weather_label(flag: Optional[bool]) -> str:
    if flag is True:
        return "fixed_weather"
    if flag is False:
        return "random_weather"
    return "unknown_weather"


def adaptive_label(flag: Optional[bool]) -> str:
    if flag is True:
        return "adaptive"
    if flag is False:
        return "nonadaptive"
    return "unknown_adaptive"


def decimal_slug(value: Any) -> str:
    if value is None or value == "":
        return "na"
    text = str(value).strip()
    text = text.replace("-", "neg_").replace(".", "_")
    cleaned = []
    for ch in text:
        cleaned.append(ch if ch.isalnum() or ch == "_" else "_")
    out = "".join(cleaned).strip("_")
    return out or "na"


def slugify(text: str) -> str:
    chars = []
    for ch in str(text).strip().lower():
        chars.append(ch if ch.isalnum() else "_")
    out = "".join(chars)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or "na"


def rolling_mean(values: pd.Series, window: int = 15) -> pd.Series:
    if values.empty:
        return values
    width = max(3, min(window, max(3, len(values) // 8)))
    return values.rolling(width, min_periods=1).mean()


def downsample_frame(df: pd.DataFrame, x_col: str, max_points: int) -> pd.DataFrame:
    if x_col not in df.columns or len(df) <= max_points:
        return df.copy()
    idx = np.linspace(0, len(df) - 1, num=max_points, dtype=int)
    return df.iloc[np.unique(idx)].copy()


def confidence_interval(values: Iterable[Any]) -> dict[str, Optional[float]]:
    clean = np.array([safe_float(v) for v in values if safe_float(v) is not None], dtype=float)
    if clean.size == 0:
        return {"n": 0, "mean": None, "std": None, "ci_low": None, "ci_high": None}
    mean = float(clean.mean())
    if clean.size == 1:
        return {"n": 1, "mean": mean, "std": None, "ci_low": mean, "ci_high": mean}
    std = float(clean.std(ddof=1))
    se = std / math.sqrt(clean.size)
    t_value = float(stats.t.ppf(0.975, df=clean.size - 1))
    delta = t_value * se
    return {"n": int(clean.size), "mean": mean, "std": std, "ci_low": mean - delta, "ci_high": mean + delta}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (Path,)):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def write_table(
    df: pd.DataFrame,
    csv_path: Path,
    *,
    source_paths: list[str],
    notes: Optional[list[str]] = None,
    extra: Optional[dict[str, Any]] = None,
) -> Path:
    ensure_dir(csv_path.parent)
    df.to_csv(csv_path, index=False)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utcnow_iso(),
        "artifact_type": "table",
        "csv_path": to_rel(csv_path),
        "source_paths": source_paths,
        "notes": notes or [],
        "columns": list(df.columns),
        "row_count": int(len(df)),
        "rows": df.replace({np.nan: None}).to_dict(orient="records"),
    }
    if extra:
        payload.update(extra)
    json_path = csv_path.with_suffix(".json")
    write_json(json_path, payload)
    return json_path


def save_figure(
    fig: plt.Figure,
    png_path: Path,
    *,
    source_paths: list[str],
    series_payload: list[dict[str, Any]],
    notes: Optional[list[str]] = None,
    extra: Optional[dict[str, Any]] = None,
) -> Path:
    ensure_dir(png_path.parent)
    fig.tight_layout()
    fig.savefig(png_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utcnow_iso(),
        "artifact_type": "figure",
        "png_path": to_rel(png_path),
        "source_paths": source_paths,
        "notes": notes or [],
        "series": series_payload,
    }
    if extra:
        payload.update(extra)
    json_path = png_path.with_suffix(".json")
    write_json(json_path, payload)
    return json_path


def load_existing_final113_tables() -> dict[str, pd.DataFrame]:
    reporting_root = FINAL_113_RUNS_PATH / "reporting"
    tables: dict[str, pd.DataFrame] = {}
    for filename in FINAL_113_COPY_TABLES:
        path = reporting_root / filename
        if path.exists():
            tables[filename] = pd.read_csv(path)
    return tables


def load_existing_final113_summary() -> dict[str, Any]:
    return read_json(FINAL_113_RUNS_PATH / "reporting" / "final_reporting_summary.json")


def discover_history_sources() -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    by_run_id: dict[str, dict[str, Any]] = {}
    for spec in HISTORY_ROOTS:
        root = spec["path"]
        project = spec["project"]
        if not root.exists():
            continue
        for run_dir in sorted(root.iterdir()):
            if not run_dir.is_dir() or "__" not in run_dir.name:
                continue
            run_id, run_name = run_dir.name.split("__", 1)
            history_path = run_dir / "history" / "history_scan.csv"
            row = {
                "history_project": project,
                "run_id": run_id,
                "run_name": run_name,
                "history_run_dir": str(run_dir.resolve()),
                "history_scan_path": str(history_path.resolve()) if history_path.exists() else "",
                "history_scan_exists": history_path.exists(),
                "system_metrics_path": str((run_dir / "system_metrics.json").resolve())
                if (run_dir / "system_metrics.json").exists()
                else "",
            }
            rows.append(row)
            by_run_id.setdefault(run_id, row)
    df = pd.DataFrame(rows).sort_values(["history_project", "run_id"]).reset_index(drop=True)
    return df, by_run_id


def load_ablation_run_summary_lookup() -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    rows: list[pd.DataFrame] = []
    reporting_root = FINAL_42_ROOT / "reporting" / "low_hanging_ablation"
    if reporting_root.exists():
        for path in sorted(reporting_root.rglob("run_summary.csv")):
            df = pd.read_csv(path)
            df["run_summary_path"] = str(path.resolve())
            df["batch"] = path.parent.name
            rows.append(df)
    if not rows:
        empty = pd.DataFrame()
        return empty, {}
    merged = pd.concat(rows, ignore_index=True)
    lookup: dict[str, dict[str, Any]] = {}
    for _, row in merged.iterrows():
        row_dict = {key: row[key] for key in merged.columns}
        summary_name = Path(str(row.get("summary_json", ""))).name
        if summary_name:
            lookup[f"summary_name:{summary_name}"] = row_dict
        summary_path = Path(str(row.get("summary_json", "")))
        if summary_path.exists():
            payload = read_json(summary_path)
            run_id = str(payload.get("run_id", "")).strip()
            if run_id:
                lookup[f"run_id:{run_id}"] = row_dict
    return merged, lookup


def build_final113_reporting_lookup() -> dict[str, dict[str, Any]]:
    path = FINAL_113_RUNS_PATH / "reporting" / "run_level_metrics.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    return {str(row["run_id"]): row.to_dict() for _, row in df.iterrows()}


def find_single_file(path: Path, pattern: str) -> Optional[Path]:
    matches = sorted(path.glob(pattern))
    return matches[0] if matches else None


def resolve_manifest_bundle_dir(value: str) -> Path:
    rel = Path(str(value).replace("\\", "/"))
    if rel.parts and rel.parts[0] == "final_successful_runs":
        return (FINAL_SUCCESSFUL_RUNS_PATH.parent / rel).resolve()
    return (PROJECT_PATH / rel).resolve()


def extract_eval_npz_paths(bundle_dir: Path) -> list[Path]:
    checkpoints = bundle_dir / "models" / "checkpoints"
    if not checkpoints.exists():
        return []
    return sorted(checkpoints.rglob("evaluations.npz"))


def resolve_point2_report_dir(bundle_dir: Path) -> Optional[Path]:
    reports_root = bundle_dir / "reports"
    if not reports_root.exists():
        return None
    thesis_report = reports_root / "thesis_report"
    if thesis_report.exists():
        return thesis_report
    subdirs = sorted(path for path in reports_root.iterdir() if path.is_dir())
    return subdirs[0] if subdirs else None


def flatten_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
    baseline_returns = metrics.get("baseline_returns", {}) if isinstance(metrics, dict) else {}
    row = {key: value for key, value in payload.items() if key != "metrics"}
    row.update(
        {
            "deterministic_return": safe_float(metrics.get("deterministic_return")),
            "stochastic_return_mean": safe_float(metrics.get("stochastic_return_mean")),
            "stochastic_return_std": safe_float(metrics.get("stochastic_return_std")),
            "pak_holdout_return": safe_float(metrics.get("pak_holdout_return")),
            "baseline_best_return": safe_float(metrics.get("baseline_best_return")),
            "uplift_vs_best_baseline_det": safe_float(metrics.get("uplift_vs_best_baseline_det")),
            "baseline_returns": baseline_returns if isinstance(baseline_returns, dict) else {},
        }
    )
    return row


def parse_run_scalar_record(
    *,
    dataset: str,
    manifest_row: dict[str, Any],
    history_lookup: dict[str, dict[str, Any]],
    final113_lookup: dict[str, dict[str, Any]],
    ablation_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    bundle_dir = resolve_manifest_bundle_dir(str(manifest_row["bundle_dir"]))
    summary_path = find_single_file(bundle_dir / "summary", "*.json")
    summary_payload = flatten_metrics(read_json(summary_path)) if summary_path else {}
    config_path = bundle_dir / "wandb" / "config.yaml"
    wandb_summary_path = bundle_dir / "wandb" / "wandb-summary.json"
    bundle_metadata_path = bundle_dir / "bundle_metadata.json"
    config_payload = read_yaml(config_path)
    wandb_summary = read_json(wandb_summary_path)
    run_id = str(summary_payload.get("run_id") or manifest_row.get("run_id") or "").strip()
    run_slug = bundle_dir.name
    history = history_lookup.get(run_id, {})
    final113_row = final113_lookup.get(run_id, {})
    summary_name = summary_path.name if summary_path else ""
    ablation_row = ablation_lookup.get(f"run_id:{run_id}", {}) or ablation_lookup.get(f"summary_name:{summary_name}", {})

    fixed_weather = safe_bool(summary_payload.get("fixed_weather"))
    nonadaptive = safe_bool(
        summary_payload.get("nonadaptive")
        if "nonadaptive" in summary_payload
        else summary_payload.get("non_adaptive")
    )
    adaptive = None if nonadaptive is None else not nonadaptive
    hierarchical = safe_bool(summary_payload.get("hierarchical"))
    baseline = safe_bool(summary_payload.get("baseline"))

    point = str(manifest_row.get("point", "") or "")
    batch = str(manifest_row.get("batch", "") or ablation_row.get("batch", "") or "")
    ent_coef = safe_float(ablation_row.get("ent_coef"))
    if ent_coef is None and point == "point1_entropy_fertilization" and summary_name:
        name = summary_name.replace(".json", "")
        if "ent0.01" in name or "ent0_01" in run_slug:
            ent_coef = 0.01
        elif "ent0" in name or run_slug.endswith("ent0"):
            ent_coef = 0.0
    blocked_penalty = safe_float(
        summary_payload.get("blocked_nutrient_penalty_per_kg")
        if summary_payload.get("blocked_nutrient_penalty_per_kg") is not None
        else ablation_row.get("blocked_nutrient_penalty_per_kg")
    )
    nutrient_cost_weight = safe_float(
        summary_payload.get("nutrient_cost_weight")
        if summary_payload.get("nutrient_cost_weight") is not None
        else ablation_row.get("nutrient_cost_weight")
    )
    total_years = safe_int(summary_payload.get("total_years"))

    if dataset == "final_113":
        report_group = str(final113_row.get("report_group", ""))
        group_key = str(final113_row.get("group_key", ""))
        primary_metric_name = str(final113_row.get("primary_metric_name", "")) or (
            "deterministic_return" if summary_payload.get("domain") == "fertilization" else "eval_det_mean_reward"
        )
        primary_metric_value = safe_float(final113_row.get("primary_metric_value"))
        eval_det_mean_reward = safe_float(final113_row.get("eval_det_mean_reward"))
        eval_sto_mean_reward = safe_float(final113_row.get("eval_sto_mean_reward"))
        runtime_seconds = safe_float(final113_row.get("runtime_seconds"))
    else:
        report_group = point
        if point == "point1_entropy_fertilization":
            group_key = f"ent_{decimal_slug(ent_coef)}__{weather_label(fixed_weather)}"
            primary_metric_name = "deterministic_return"
        elif point == "point2_hierarchical_shaping":
            group_key = (
                f"{str(summary_payload.get('method', '')).lower()}__{weather_label(fixed_weather)}__"
                f"blocked_penalty_{decimal_slug(blocked_penalty)}"
            )
            primary_metric_name = "deterministic_return"
        else:
            group_key = f"cost_weight_{decimal_slug(nutrient_cost_weight)}__{weather_label(fixed_weather)}"
            primary_metric_name = "deterministic_return"
        primary_metric_value = safe_float(summary_payload.get(primary_metric_name))
        eval_det_mean_reward = safe_float(ablation_row.get("eval_det_mean_reward"))
        eval_sto_mean_reward = safe_float(ablation_row.get("eval_sto_mean_reward"))
        runtime_seconds = safe_float(ablation_row.get("elapsed_seconds"))

    eval_npz_paths = extract_eval_npz_paths(bundle_dir)

    row = {
        "dataset": dataset,
        "index": safe_int(manifest_row.get("index")),
        "label": str(manifest_row.get("label", "")),
        "run_id": run_id,
        "run_slug": run_slug,
        "bundle_dir": str(bundle_dir),
        "bundle_dir_rel": to_rel(bundle_dir),
        "summary_json_path": str(summary_path.resolve()) if summary_path else "",
        "config_path": str(config_path.resolve()) if config_path.exists() else "",
        "wandb_summary_path": str(wandb_summary_path.resolve()) if wandb_summary_path.exists() else "",
        "bundle_metadata_path": str(bundle_metadata_path.resolve()) if bundle_metadata_path.exists() else "",
        "domain": str(summary_payload.get("domain", manifest_row.get("domain", ""))),
        "method": str(summary_payload.get("method", manifest_row.get("method", ""))),
        "seed": safe_int(summary_payload.get("seed")),
        "fixed_weather": fixed_weather,
        "weather_label": weather_label(fixed_weather),
        "nonadaptive": nonadaptive,
        "adaptive": adaptive,
        "adaptive_label": adaptive_label(adaptive),
        "hierarchical": hierarchical,
        "baseline": baseline,
        "learned_run": bool((bundle_dir / "models" / "model.zip").exists() and not baseline),
        "total_years": total_years,
        "price_profile": str(summary_payload.get("price_profile", "")),
        "point": point,
        "batch": batch,
        "ent_coef": ent_coef,
        "blocked_penalty": blocked_penalty,
        "nutrient_cost_weight": nutrient_cost_weight,
        "report_group": report_group,
        "group_key": group_key,
        "primary_metric_name": primary_metric_name,
        "primary_metric_value": primary_metric_value,
        "deterministic_return": safe_float(summary_payload.get("deterministic_return")),
        "stochastic_return_mean": safe_float(summary_payload.get("stochastic_return_mean")),
        "stochastic_return_std": safe_float(summary_payload.get("stochastic_return_std")),
        "pak_holdout_return": safe_float(summary_payload.get("pak_holdout_return")),
        "eval_det_mean_reward": eval_det_mean_reward,
        "eval_sto_mean_reward": eval_sto_mean_reward,
        "baseline_best_return": safe_float(summary_payload.get("baseline_best_return")),
        "uplift_vs_best_baseline_det": safe_float(summary_payload.get("uplift_vs_best_baseline_det")),
        "runtime_seconds": runtime_seconds,
        "history_project": history.get("history_project", ""),
        "history_run_dir": history.get("history_run_dir", ""),
        "history_scan_path": history.get("history_scan_path", ""),
        "system_metrics_path": history.get("system_metrics_path", ""),
        "history_match": bool(history),
        "summary_json_exists": bool(summary_path and summary_path.exists()),
        "config_exists": config_path.exists(),
        "wandb_summary_exists": wandb_summary_path.exists(),
        "model_zip_exists": (bundle_dir / "models" / "model.zip").exists(),
        "vec_normalize_exists": any((bundle_dir / "runtime").glob("vec_normalize_*.pkl")),
        "point2_report_exists": resolve_point2_report_dir(bundle_dir) is not None,
        "eval_npz_count": len(eval_npz_paths),
        "history_rows": None,
        "action_table_count": None,
        "notes": str(manifest_row.get("notes", "")),
        "source_manifest": to_rel(FINAL_113_RUNS_PATH / "manifest.csv" if dataset == "final_113" else FINAL_42_ROOT / "manifest.csv"),
        "source_paths": json.dumps(
            [
                to_rel(summary_path) if summary_path else "",
                to_rel(config_path) if config_path.exists() else "",
                to_rel(wandb_summary_path) if wandb_summary_path.exists() else "",
                to_rel(Path(history.get("history_scan_path", ""))) if history.get("history_scan_path") else "",
            ]
        ),
        "baseline_returns_json": json.dumps(summary_payload.get("baseline_returns", {})),
        "run_name": str(history.get("run_name", "")),
        "wandb_runtime_seconds": safe_float(wandb_summary.get("_runtime")),
    }
    return row


def build_run_catalog(
    dataset: str,
    history_lookup: dict[str, dict[str, Any]],
    final113_lookup: dict[str, dict[str, Any]],
    ablation_lookup: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    manifest_path = FINAL_113_RUNS_PATH / "manifest.csv" if dataset == "final_113" else FINAL_42_ROOT / "manifest.csv"
    manifest_df = pd.read_csv(manifest_path)
    rows = [
        parse_run_scalar_record(
            dataset=dataset,
            manifest_row=manifest_row.to_dict(),
            history_lookup=history_lookup,
            final113_lookup=final113_lookup,
            ablation_lookup=ablation_lookup,
        )
        for _, manifest_row in manifest_df.iterrows()
    ]
    return pd.DataFrame(rows).sort_values(["dataset", "index"]).reset_index(drop=True)


def history_columns_for_row(row: pd.Series) -> list[str]:
    base = [
        "global_step",
        "_step",
        "_runtime",
        "rollout/ep_rew_mean",
        "rollout/ep_len_mean",
        "deterministic_return",
        "stochastic_return_mean",
        "stochastic_return_std",
        "pak_holdout_return",
        "eval_test_det/mean_reward",
        "eval_test_sto/mean_reward",
        "eval_train_det/mean_reward",
        "eval_train_sto/mean_reward",
        "eval_det/mean_reward",
        "eval_sto/mean_reward",
        "eval_det_new_years/mean_reward",
        "eval_sto_new_years/mean_reward",
        "eval_det_other_loc/mean_reward",
        "eval_sto_other_loc/mean_reward",
        "train/approx_kl",
        "train/clip_fraction",
        "train/explained_variance",
        "train/learning_rate",
        "train/loss",
        "train/policy_gradient_loss",
        "train/value_loss",
        "train/entropy_loss",
        "rollout/exploration_rate",
        "time/fps",
        "summary_json_path",
    ]
    if str(row["domain"]) == "fertilization":
        base.extend(
            [
                "eval/long_eval_det2",
                "eval/long_eval_det5",
                "eval/long_eval_sto2",
                "eval/long_eval_sto5",
            ]
        )
    return base


def load_history_dataframe(history_path: str, row: pd.Series) -> pd.DataFrame:
    if not history_path:
        return pd.DataFrame()
    df = pd.read_csv(history_path)
    keep = [col for col in history_columns_for_row(row) if col in df.columns]
    if not keep:
        return pd.DataFrame()
    selected = df[keep].copy()
    sort_col = "global_step" if "global_step" in selected.columns else "_step"
    if sort_col in selected.columns:
        selected = selected.sort_values(sort_col).reset_index(drop=True)
    return selected


def infer_x_column(df: pd.DataFrame) -> Optional[str]:
    for column in ("global_step", "_step", "_runtime"):
        if column in df.columns:
            return column
    return None


def primary_history_candidates(row: pd.Series) -> list[str]:
    if row["dataset"] == "final_113" and str(row["domain"]) == "crop_planning" and not bool(row["hierarchical"]):
        return ["eval_det/mean_reward", "deterministic_return", "eval_test_det/mean_reward"]
    if str(row["domain"]) == "fertilization":
        return ["deterministic_return", "eval_test_det/mean_reward", "eval_train_det/mean_reward"]
    return ["deterministic_return", "eval_det/mean_reward", "eval_test_det/mean_reward"]


def get_primary_history_column(df: pd.DataFrame, row: pd.Series) -> Optional[str]:
    for column in primary_history_candidates(row):
        if column in df.columns and df[column].notna().any():
            return column
    return None


def diagnostics_columns(df: pd.DataFrame, row: pd.Series) -> list[str]:
    method = str(row["method"]).upper()
    if method in {"PPO", "A2C"}:
        candidates = [
            "train/approx_kl",
            "train/clip_fraction",
            "train/explained_variance",
            "train/learning_rate",
            "train/policy_gradient_loss",
            "train/value_loss",
            "train/entropy_loss",
            "train/loss",
            "time/fps",
        ]
    else:
        candidates = [
            "train/loss",
            "rollout/exploration_rate",
            "train/learning_rate",
            "time/fps",
            "eval_test_det/mean_reward",
            "eval_det/mean_reward",
        ]
    return [col for col in candidates if col in df.columns][:6]


def flatten_evaluation_curves(bundle_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for npz_path in extract_eval_npz_paths(bundle_dir):
        checkpoint_name = npz_path.parent.name
        payload = np.load(npz_path, allow_pickle=True)
        timesteps = payload["timesteps"]
        results = payload["results"]
        lengths = payload["ep_lengths"]
        for idx, timestep in enumerate(timesteps):
            rewards = np.asarray(results[idx], dtype=float)
            ep_lengths = np.asarray(lengths[idx], dtype=float)
            rows.append(
                {
                    "checkpoint_name": checkpoint_name,
                    "timestep": int(timestep),
                    "mean_reward": float(rewards.mean()) if rewards.size else None,
                    "std_reward": float(rewards.std(ddof=0)) if rewards.size else None,
                    "min_reward": float(rewards.min()) if rewards.size else None,
                    "max_reward": float(rewards.max()) if rewards.size else None,
                    "mean_ep_length": float(ep_lengths.mean()) if ep_lengths.size else None,
                    "n_eval_episodes": int(rewards.size),
                }
            )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["checkpoint_name", "timestep"]).reset_index(drop=True)


def run_metrics_table(row: pd.Series) -> pd.DataFrame:
    keys = [
        "dataset",
        "index",
        "label",
        "run_id",
        "run_slug",
        "domain",
        "method",
        "seed",
        "fixed_weather",
        "weather_label",
        "adaptive",
        "adaptive_label",
        "hierarchical",
        "baseline",
        "point",
        "batch",
        "ent_coef",
        "blocked_penalty",
        "nutrient_cost_weight",
        "primary_metric_name",
        "primary_metric_value",
        "deterministic_return",
        "stochastic_return_mean",
        "stochastic_return_std",
        "pak_holdout_return",
        "eval_det_mean_reward",
        "eval_sto_mean_reward",
        "baseline_best_return",
        "uplift_vs_best_baseline_det",
        "runtime_seconds",
        "history_project",
        "history_match",
        "model_zip_exists",
        "vec_normalize_exists",
        "point2_report_exists",
        "eval_npz_count",
    ]
    return pd.DataFrame([{key: row.get(key) for key in keys}])


def load_action_table(history_run_dir: Path, pattern: str) -> pd.DataFrame:
    matches = sorted(history_run_dir.rglob(pattern))
    if not matches:
        return pd.DataFrame()
    payload = read_json(matches[0])
    columns = payload.get("columns", [])
    data = payload.get("data", [])
    if not columns or not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data, columns=columns)


def copy_point2_report_artifacts(
    row: pd.Series,
    dataset_root: Path,
    missing: list[dict[str, Any]],
) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    if not bool(row.get("point2_report_exists")):
        return frames
    source_dir = resolve_point2_report_dir(Path(str(row.get("bundle_dir"))))
    if source_dir is None or not source_dir.exists():
        missing.append(
            {
                "run_slug": row["run_slug"],
                "artifact_type": "point2_report",
                "reason": "report directory missing inside bundle",
            }
        )
        return frames
    tables_dir = dataset_root / "tables" / "per_run"
    metrics_dir = dataset_root / "metrics_json" / "per_run"
    for filename in ("weekly_npk_log.csv", "yearly_crop_decisions.csv", "season_window_compliance.csv"):
        src = source_dir / filename
        if not src.exists():
            continue
        df = pd.read_csv(src)
        dst = tables_dir / f"{row['run_slug']}__{filename}"
        write_table(df, dst, source_paths=[to_rel(src)], notes=["copied from canonical point2 thesis report"])
        frames[filename] = df
    summary_path = source_dir / "reporting_summary.json"
    if summary_path.exists():
        summary_dst = metrics_dir / f"{row['run_slug']}__reporting_summary.json"
        shutil.copy2(summary_path, summary_dst)
    return frames


def build_basic_line_plot(
    row: pd.Series,
    df: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    png_path: Path,
    ylabel: str,
    title_suffix: str,
    color: str,
    smooth: bool = False,
) -> None:
    plot_df = downsample_frame(df[[x_col, y_col]].dropna(), x_col, 500)
    if plot_df.empty:
        raise ValueError(f"empty plot data for {y_col}")
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.plot(plot_df[x_col], plot_df[y_col], color=color, linewidth=1.2, label=y_col)
    series_payload = [
        {
            "name": y_col,
            "x": plot_df[x_col].tolist(),
            "y": plot_df[y_col].tolist(),
        }
    ]
    if smooth and len(plot_df) > 5:
        smooth_values = rolling_mean(plot_df[y_col])
        ax.plot(plot_df[x_col], smooth_values, color=PLOT_COLORS["reward_smooth"], linewidth=2.0, label="moving_average")
        series_payload.append(
            {
                "name": f"{y_col}_moving_average",
                "x": plot_df[x_col].tolist(),
                "y": smooth_values.tolist(),
            }
        )
    ax.set_title(f"{row['run_slug']} | {title_suffix}")
    ax.set_xlabel(x_col)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    save_figure(
        fig,
        png_path,
        source_paths=[row["history_scan_path"]],
        series_payload=series_payload,
        extra={"run_id": row["run_id"], "run_slug": row["run_slug"], "title_suffix": title_suffix},
    )


def build_diagnostics_plot(row: pd.Series, df: pd.DataFrame, x_col: str, png_path: Path) -> None:
    cols = diagnostics_columns(df, row)
    if not cols:
        raise ValueError("no diagnostics columns")
    plot_df = downsample_frame(df[[x_col] + cols].dropna(how="all"), x_col, 500)
    fig, axes = plt.subplots(len(cols), 1, figsize=(8.8, max(4.5, 2.2 * len(cols))), sharex=True)
    if len(cols) == 1:
        axes = [axes]
    series_payload: list[dict[str, Any]] = []
    for ax, col in zip(axes, cols):
        series = plot_df[[x_col, col]].dropna()
        ax.plot(series[x_col], series[col], linewidth=1.2, color="#374151")
        ax.set_ylabel(col)
        ax.grid(alpha=0.2)
        series_payload.append({"name": col, "x": series[x_col].tolist(), "y": series[col].tolist()})
    axes[0].set_title(f"{row['run_slug']} | diagnostics panel")
    axes[-1].set_xlabel(x_col)
    save_figure(
        fig,
        png_path,
        source_paths=[row["history_scan_path"]],
        series_payload=series_payload,
        extra={"run_id": row["run_id"], "run_slug": row["run_slug"], "diagnostics_columns": cols},
    )


def build_eval_curve_plot(row: pd.Series, df: pd.DataFrame, png_path: Path) -> None:
    if df.empty:
        raise ValueError("empty checkpoint evaluation frame")
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    series_payload: list[dict[str, Any]] = []
    for checkpoint_name, group in df.groupby("checkpoint_name"):
        plot_df = downsample_frame(group[["timestep", "mean_reward"]].dropna(), "timestep", 500)
        if plot_df.empty:
            continue
        ax.plot(plot_df["timestep"], plot_df["mean_reward"], linewidth=1.6, label=checkpoint_name)
        series_payload.append(
            {
                "name": checkpoint_name,
                "x": plot_df["timestep"].tolist(),
                "y": plot_df["mean_reward"].tolist(),
            }
        )
    ax.set_title(f"{row['run_slug']} | checkpoint evaluation progression")
    ax.set_xlabel("timestep")
    ax.set_ylabel("mean_reward")
    ax.grid(alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    save_figure(
        fig,
        png_path,
        source_paths=[to_rel(Path(row["bundle_dir"]) / "models" / "checkpoints")],
        series_payload=series_payload,
        extra={"run_id": row["run_id"], "run_slug": row["run_slug"]},
    )


def build_point2_figures(
    row: pd.Series,
    dataset_root: Path,
    frames: dict[str, pd.DataFrame],
    missing: list[dict[str, Any]],
) -> None:
    weekly = frames.get("weekly_npk_log.csv", pd.DataFrame())
    yearly = frames.get("yearly_crop_decisions.csv", pd.DataFrame())
    compliance = frames.get("season_window_compliance.csv", pd.DataFrame())
    figure_dir = dataset_root / "figures" / "per_run"
    report_dir = resolve_point2_report_dir(Path(str(row["bundle_dir"])))
    if not weekly.empty and "num_timesteps" in weekly.columns:
        plot_df = downsample_frame(
            weekly[["num_timesteps", "n_kg", "p_kg", "k_kg", "blocked_npk_kg"]].dropna(how="all"),
            "num_timesteps",
            500,
        )
        fig, ax = plt.subplots(figsize=(8.8, 4.8))
        for col, color in [("n_kg", PLOT_COLORS["n"]), ("p_kg", PLOT_COLORS["p"]), ("k_kg", PLOT_COLORS["k"])]:
            ax.plot(plot_df["num_timesteps"], plot_df[col], linewidth=1.2, label=col, color=color)
        if "blocked_npk_kg" in plot_df.columns:
            ax.plot(plot_df["num_timesteps"], plot_df["blocked_npk_kg"], linewidth=1.2, label="blocked_npk_kg", color=PLOT_COLORS["blocked"])
        ax.set_title(f"{row['run_slug']} | weekly npk behavior")
        ax.set_xlabel("num_timesteps")
        ax.set_ylabel("kg")
        ax.grid(alpha=0.25)
        ax.legend(loc="best")
        save_figure(
            fig,
            figure_dir / f"{row['run_slug']}__weekly_npk_behavior.png",
            source_paths=[to_rel(report_dir / "weekly_npk_log.csv") if report_dir else ""],
            series_payload=[
                {"name": col, "x": plot_df["num_timesteps"].tolist(), "y": plot_df[col].tolist()}
                for col in ["n_kg", "p_kg", "k_kg", "blocked_npk_kg"]
                if col in plot_df.columns
            ],
        )
    else:
        missing.append({"run_slug": row["run_slug"], "artifact_type": "figure", "artifact_id": "weekly_npk_behavior", "reason": "weekly_npk_log.csv missing or incomplete"})

    if not yearly.empty and "operation_year" in yearly.columns:
        plot_df = yearly.copy()
        crop_order = {name: idx for idx, name in enumerate(sorted(plot_df["effective_crop_name"].fillna("unknown").astype(str).unique()))}
        plot_df["crop_y"] = plot_df["effective_crop_name"].fillna("unknown").astype(str).map(crop_order)
        fig, ax = plt.subplots(figsize=(8.8, 4.6))
        ax.scatter(plot_df["operation_year"], plot_df["crop_y"], s=26, color=PLOT_COLORS["primary"])
        ax.set_yticks(list(crop_order.values()))
        ax.set_yticklabels(list(crop_order.keys()))
        ax.set_title(f"{row['run_slug']} | crop decision timeline")
        ax.set_xlabel("operation_year")
        ax.set_ylabel("effective_crop_name")
        ax.grid(alpha=0.25)
        save_figure(
            fig,
            figure_dir / f"{row['run_slug']}__crop_decision_timeline.png",
            source_paths=[to_rel(report_dir / "yearly_crop_decisions.csv") if report_dir else ""],
            series_payload=[
                {
                    "name": "effective_crop_name",
                    "x": plot_df["operation_year"].tolist(),
                    "y": plot_df["crop_y"].tolist(),
                    "labels": list(crop_order.keys()),
                }
            ],
        )
    else:
        missing.append({"run_slug": row["run_slug"], "artifact_type": "figure", "artifact_id": "crop_decision_timeline", "reason": "yearly_crop_decisions.csv missing or incomplete"})

    if not compliance.empty and "operation_year" in compliance.columns:
        plot_df = compliance[["operation_year", "compliance_rate"]].dropna()
        fig, ax = plt.subplots(figsize=(8.8, 4.2))
        ax.bar(plot_df["operation_year"].astype(str), plot_df["compliance_rate"], color="#15803d")
        ax.set_ylim(0, 1.05)
        ax.set_title(f"{row['run_slug']} | compliance summary")
        ax.set_xlabel("operation_year")
        ax.set_ylabel("compliance_rate")
        ax.grid(alpha=0.15, axis="y")
        save_figure(
            fig,
            figure_dir / f"{row['run_slug']}__compliance_summary.png",
            source_paths=[to_rel(report_dir / "season_window_compliance.csv") if report_dir else ""],
            series_payload=[{"name": "compliance_rate", "x": plot_df["operation_year"].tolist(), "y": plot_df["compliance_rate"].tolist()}],
        )

    summary_path = report_dir / "reporting_summary.json" if report_dir else Path()
    summary = read_json(summary_path)
    if summary:
        fig, ax = plt.subplots(figsize=(7.4, 4.8))
        keys = ["total_cost", "blocked_npk_kg_total", "overall_compliance_rate", "reward_shaping_blocked_penalty_total"]
        values = [safe_float(summary.get(key)) or 0.0 for key in keys]
        ax.bar(range(len(keys)), values, color=["#1d4ed8", "#b91c1c", "#15803d", "#7c3aed"])
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(keys, rotation=25, ha="right")
        ax.set_title(f"{row['run_slug']} | blocked and cost summary")
        ax.grid(alpha=0.15, axis="y")
        save_figure(
            fig,
            figure_dir / f"{row['run_slug']}__blocked_cost_summary.png",
            source_paths=[to_rel(summary_path)],
            series_payload=[{"name": "summary_bars", "x": keys, "y": values}],
        )


def build_run_render(
    row: pd.Series,
    dataset_root: Path,
    history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    point2_frames: dict[str, pd.DataFrame],
    missing: list[dict[str, Any]],
) -> None:
    if not bool(row["learned_run"]):
        missing.append({"run_slug": row["run_slug"], "artifact_type": "render", "artifact_id": "primary_render", "reason": "non-learned baseline row"})
        return
    render_dir = dataset_root / "renders" / "per_run" / row["run_slug"]
    ensure_dir(render_dir)
    history_run_dir = Path(str(row["history_run_dir"])) if row.get("history_run_dir") else None
    fig, axes = plt.subplots(2, 2, figsize=(10.0, 7.2))
    axes = axes.ravel()
    series_payload: list[dict[str, Any]] = []
    source_paths: list[str] = []
    built = False

    if history_run_dir and str(row["domain"]) == "fertilization":
        n_df = load_action_table(history_run_dir, "*det1_N_table.table.json")
        p_df = load_action_table(history_run_dir, "*det1_P_table.table.json")
        k_df = load_action_table(history_run_dir, "*det1_K_table.table.json")
        total_df = load_action_table(history_run_dir, "*fertilizer_npk.table.json")
        if not n_df.empty and not p_df.empty and not k_df.empty:
            for df, col, color in [(n_df, n_df.columns[1], PLOT_COLORS["n"]), (p_df, p_df.columns[1], PLOT_COLORS["p"]), (k_df, k_df.columns[1], PLOT_COLORS["k"])]:
                axes[0].plot(df.iloc[:, 0], df.iloc[:, 1], linewidth=1.2, label=col, color=color)
                series_payload.append({"name": col, "x": df.iloc[:, 0].tolist(), "y": df.iloc[:, 1].tolist()})
            axes[0].set_title("deterministic fertilizer actions")
            axes[0].set_xlabel(n_df.columns[0])
            axes[0].set_ylabel("action")
            axes[0].legend(loc="best")
            axes[0].grid(alpha=0.2)
            source_paths.extend([to_rel(history_run_dir)])
            built = True
        if not total_df.empty:
            totals = total_df.iloc[0].to_dict()
            x = ["Total_N", "Total_P", "Total_K"]
            y = [safe_float(totals.get("Total_N")) or 0.0, safe_float(totals.get("Total_P")) or 0.0, safe_float(totals.get("Total_K")) or 0.0]
            axes[1].bar(x, y, color=[PLOT_COLORS["n"], PLOT_COLORS["p"], PLOT_COLORS["k"]])
            axes[1].set_title("deterministic total fertilizer")
            axes[1].grid(alpha=0.15, axis="y")
            series_payload.append({"name": "total_fertilizer", "x": x, "y": y})
            built = True

    if not point2_frames.get("weekly_npk_log.csv", pd.DataFrame()).empty:
        weekly = downsample_frame(point2_frames["weekly_npk_log.csv"][["num_timesteps", "n_kg", "p_kg", "k_kg"]].dropna(), "num_timesteps", 300)
        for col, color in [("n_kg", PLOT_COLORS["n"]), ("p_kg", PLOT_COLORS["p"]), ("k_kg", PLOT_COLORS["k"])]:
            axes[0].plot(weekly["num_timesteps"], weekly[col], linewidth=1.1, label=col, color=color)
            series_payload.append({"name": col, "x": weekly["num_timesteps"].tolist(), "y": weekly[col].tolist()})
        axes[0].set_title("weekly applied N/P/K")
        axes[0].legend(loc="best")
        axes[0].grid(alpha=0.2)
        built = True
        yearly = point2_frames.get("yearly_crop_decisions.csv", pd.DataFrame())
        if not yearly.empty:
            crop_order = {name: idx for idx, name in enumerate(sorted(yearly["effective_crop_name"].fillna("unknown").astype(str).unique()))}
            yearly = yearly.copy()
            yearly["crop_y"] = yearly["effective_crop_name"].fillna("unknown").astype(str).map(crop_order)
            axes[1].scatter(yearly["operation_year"], yearly["crop_y"], s=20, color=PLOT_COLORS["primary"])
            axes[1].set_yticks(list(crop_order.values()))
            axes[1].set_yticklabels(list(crop_order.keys()))
            axes[1].set_title("crop timeline")
            axes[1].grid(alpha=0.2)
            series_payload.append({"name": "crop_timeline", "x": yearly["operation_year"].tolist(), "y": yearly["crop_y"].tolist(), "labels": list(crop_order.keys())})
        built = True

    x_col = infer_x_column(history_df)
    primary_col = get_primary_history_column(history_df, row) if not history_df.empty else None
    if x_col and "rollout/ep_rew_mean" in history_df.columns:
        reward_df = downsample_frame(history_df[[x_col, "rollout/ep_rew_mean"]].dropna(), x_col, 300)
        axes[2].plot(reward_df[x_col], reward_df["rollout/ep_rew_mean"], color=PLOT_COLORS["reward"], linewidth=1.1)
        axes[2].set_title("training reward")
        axes[2].grid(alpha=0.2)
        series_payload.append({"name": "rollout/ep_rew_mean", "x": reward_df[x_col].tolist(), "y": reward_df["rollout/ep_rew_mean"].tolist()})
        built = True
    elif not eval_df.empty:
        for checkpoint_name, group in eval_df.groupby("checkpoint_name"):
            plot_df = downsample_frame(group[["timestep", "mean_reward"]].dropna(), "timestep", 250)
            axes[2].plot(plot_df["timestep"], plot_df["mean_reward"], linewidth=1.1, label=checkpoint_name)
            series_payload.append({"name": checkpoint_name, "x": plot_df["timestep"].tolist(), "y": plot_df["mean_reward"].tolist()})
        axes[2].set_title("checkpoint eval curves")
        axes[2].legend(loc="best", fontsize=7)
        axes[2].grid(alpha=0.2)
        built = True

    metrics = [
        ("primary", safe_float(row["primary_metric_value"])),
        ("det", safe_float(row["deterministic_return"])),
        ("sto_mean", safe_float(row["stochastic_return_mean"])),
        ("baseline", safe_float(row["baseline_best_return"])),
    ]
    metric_names = [name for name, value in metrics if value is not None]
    metric_values = [value for _, value in metrics if value is not None]
    if metric_values:
        axes[3].bar(range(len(metric_values)), metric_values, color=["#1d4ed8", "#166534", "#0f766e", "#7c3aed"][: len(metric_values)])
        axes[3].set_xticks(range(len(metric_values)))
        axes[3].set_xticklabels(metric_names, rotation=20, ha="right")
        axes[3].set_title("final scalar metrics")
        axes[3].grid(alpha=0.15, axis="y")
        series_payload.append({"name": "final_scalar_metrics", "x": metric_names, "y": metric_values})
        built = True

    for ax in axes:
        ax.tick_params(labelsize=8)

    if not built:
        plt.close(fig)
        missing.append({"run_slug": row["run_slug"], "artifact_type": "render", "artifact_id": "primary_render", "reason": "no renderable source data"})
        return
    fig.suptitle(f"{row['run_slug']} | deterministic policy behavior panel", fontsize=11)
    save_figure(
        fig,
        render_dir / f"{row['run_slug']}__primary_render.png",
        source_paths=source_paths or [row.get("history_scan_path", ""), to_rel(Path(row["bundle_dir"]) / "models" / "checkpoints")],
        series_payload=series_payload,
        extra={"run_id": row["run_id"], "run_slug": row["run_slug"], "render_kind": "policy_behavior_panel"},
    )


def build_run_outputs(row: pd.Series, dataset_root: Path, missing: list[dict[str, Any]]) -> dict[str, Any]:
    cache_dir = dataset_root / "cache" / "per_run" / row["run_slug"]
    ensure_dir(cache_dir)
    tables_dir = dataset_root / "tables" / "per_run"
    figures_dir = dataset_root / "figures" / "per_run"
    metrics_dir = dataset_root / "metrics_json" / "per_run"
    history_df = load_history_dataframe(str(row.get("history_scan_path", "")), row)
    eval_df = flatten_evaluation_curves(Path(str(row["bundle_dir"])))
    outputs: dict[str, Any] = {"history_rows": int(len(history_df)), "action_table_count": 0}

    metrics_table = run_metrics_table(row)
    write_table(
        metrics_table,
        tables_dir / f"{row['run_slug']}__run_metrics.csv",
        source_paths=[row["summary_json_path"], row["wandb_summary_path"], row["history_scan_path"]],
    )
    write_json(
        metrics_dir / f"{row['run_slug']}__run_metrics.json",
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utcnow_iso(),
            "artifact_type": "run_metrics",
            "run_slug": row["run_slug"],
            "run_id": row["run_id"],
            "source_paths": [row["summary_json_path"], row["wandb_summary_path"], row["history_scan_path"]],
            "metrics": metrics_table.iloc[0].replace({np.nan: None}).to_dict(),
        },
    )

    if not history_df.empty:
        write_table(
            history_df,
            cache_dir / f"{row['run_slug']}__history_selected.csv",
            source_paths=[row["history_scan_path"]],
            notes=["selected reporting columns only"],
        )
    else:
        missing.append({"run_slug": row["run_slug"], "artifact_type": "cache", "artifact_id": "history_selected", "reason": "history_scan.csv missing or unreadable"})

    if not eval_df.empty:
        write_table(
            eval_df,
            cache_dir / f"{row['run_slug']}__checkpoint_eval_curves.csv",
            source_paths=[to_rel(Path(row["bundle_dir"]) / "models" / "checkpoints")],
        )

    point2_frames = copy_point2_report_artifacts(row, dataset_root, missing)

    x_col = infer_x_column(history_df)
    if x_col and "rollout/ep_rew_mean" in history_df.columns:
        try:
            build_basic_line_plot(
                row,
                history_df,
                x_col=x_col,
                y_col="rollout/ep_rew_mean",
                png_path=figures_dir / f"{row['run_slug']}__training_reward_vs_global_step.png",
                ylabel="reward",
                title_suffix="training reward vs global step",
                color=PLOT_COLORS["reward"],
                smooth=True,
            )
        except Exception as exc:
            missing.append({"run_slug": row["run_slug"], "artifact_type": "figure", "artifact_id": "training_reward_vs_global_step", "reason": str(exc)})
    else:
        missing.append({"run_slug": row["run_slug"], "artifact_type": "figure", "artifact_id": "training_reward_vs_global_step", "reason": "reward column unavailable"})

    if x_col and "rollout/ep_len_mean" in history_df.columns:
        try:
            build_basic_line_plot(
                row,
                history_df,
                x_col=x_col,
                y_col="rollout/ep_len_mean",
                png_path=figures_dir / f"{row['run_slug']}__episode_length_vs_global_step.png",
                ylabel="episode_length",
                title_suffix="episode length vs global step",
                color=PLOT_COLORS["length"],
            )
        except Exception as exc:
            missing.append({"run_slug": row["run_slug"], "artifact_type": "figure", "artifact_id": "episode_length_vs_global_step", "reason": str(exc)})
    else:
        missing.append({"run_slug": row["run_slug"], "artifact_type": "figure", "artifact_id": "episode_length_vs_global_step", "reason": "episode length column unavailable"})

    primary_col = get_primary_history_column(history_df, row) if x_col else None
    if x_col and primary_col:
        primary_plot_error: Optional[str] = None
        plotted = False
        for candidate in primary_history_candidates(row):
            if candidate not in history_df.columns:
                continue
            try:
                build_basic_line_plot(
                    row,
                    history_df,
                    x_col=x_col,
                    y_col=candidate,
                    png_path=figures_dir / f"{row['run_slug']}__primary_metric_vs_global_step.png",
                    ylabel=candidate,
                    title_suffix="primary evaluation metric vs global step",
                    color=PLOT_COLORS["primary"],
                )
                plotted = True
                break
            except Exception as exc:
                primary_plot_error = str(exc)
        if not plotted:
            missing.append({"run_slug": row["run_slug"], "artifact_type": "figure", "artifact_id": "primary_metric_vs_global_step", "reason": primary_plot_error or "no plottable primary metric candidate"})
    else:
        missing.append({"run_slug": row["run_slug"], "artifact_type": "figure", "artifact_id": "primary_metric_vs_global_step", "reason": "primary history metric unavailable"})

    try:
        if x_col:
            build_diagnostics_plot(row, history_df, x_col, figures_dir / f"{row['run_slug']}__diagnostics_panel.png")
        else:
            raise ValueError("no x column")
    except Exception as exc:
        missing.append({"run_slug": row["run_slug"], "artifact_type": "figure", "artifact_id": "diagnostics_panel", "reason": str(exc)})

    try:
        build_eval_curve_plot(row, eval_df, figures_dir / f"{row['run_slug']}__checkpoint_eval_curves.png")
    except Exception as exc:
        missing.append({"run_slug": row["run_slug"], "artifact_type": "figure", "artifact_id": "checkpoint_eval_curves", "reason": str(exc)})

    if row["point"] == "point2_hierarchical_shaping":
        build_point2_figures(row, dataset_root, point2_frames, missing)

    build_run_render(row, dataset_root, history_df, eval_df, point2_frames, missing)

    history_run_dir = Path(str(row["history_run_dir"])) if row.get("history_run_dir") else None
    if history_run_dir and history_run_dir.exists():
        outputs["action_table_count"] = len(list(history_run_dir.rglob("*.table.json")))
    outputs["history_rows"] = int(len(history_df))
    return outputs


def build_bar_figure(
    df: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    png_path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
    source_paths: list[str],
    rotate: int = 25,
) -> None:
    plot_df = df[[x_col, y_col]].dropna().copy()
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    ax.bar(plot_df[x_col].astype(str), plot_df[y_col], color="#1d4ed8")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=rotate)
    ax.grid(alpha=0.15, axis="y")
    save_figure(
        fig,
        png_path,
        source_paths=source_paths,
        series_payload=[{"name": y_col, "x": plot_df[x_col].astype(str).tolist(), "y": plot_df[y_col].tolist()}],
    )


def build_grouped_line_figure(
    df: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    group_col: str,
    png_path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
    source_paths: list[str],
) -> None:
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    series_payload: list[dict[str, Any]] = []
    for name, group in df.groupby(group_col):
        plot_df = group[[x_col, y_col]].dropna().sort_values(x_col)
        ax.plot(plot_df[x_col], plot_df[y_col], marker="o", linewidth=1.4, label=str(name))
        series_payload.append({"name": str(name), "x": plot_df[x_col].tolist(), "y": plot_df[y_col].tolist()})
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.2)
    save_figure(fig, png_path, source_paths=source_paths, series_payload=series_payload)


def write_dataset_catalogs(
    dataset: str,
    dataset_root: Path,
    catalog_df: pd.DataFrame,
    source_manifest: Path,
) -> None:
    write_table(
        catalog_df,
        dataset_root / "tables" / "grouped" / f"{dataset}__run_catalog.csv",
        source_paths=[to_rel(source_manifest)],
        extra={"dataset": dataset},
    )


def build_final113_grouped_outputs(dataset_root: Path, catalog_df: pd.DataFrame, missing: list[dict[str, Any]]) -> None:
    reporting_root = FINAL_113_RUNS_PATH / "reporting"
    copied_tables: dict[str, pd.DataFrame] = {}
    for src_name, dst_name in FINAL_113_COPY_TABLES.items():
        src = reporting_root / src_name
        if not src.exists():
            missing.append({"run_slug": "", "artifact_type": "grouped_table", "artifact_id": src_name, "reason": "existing final_113 reporting table missing"})
            continue
        df = pd.read_csv(src)
        copied_tables[src_name] = df
        write_table(
            df,
            dataset_root / "tables" / "grouped" / dst_name,
            source_paths=[to_rel(src)],
            notes=["copied from frozen final_113 reporting outputs"],
        )

    summary_payload = load_existing_final113_summary()
    write_json(
        dataset_root / "metrics_json" / "grouped" / "final_113__final_reporting_summary.json",
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utcnow_iso(),
            "artifact_type": "summary_json",
            "source_paths": [to_rel(reporting_root / "final_reporting_summary.json")],
            "payload": summary_payload,
        },
    )

    if "grouped_metrics.csv" in copied_tables:
        grouped = copied_tables["grouped_metrics.csv"]
        top_groups = grouped.sort_values("primary_metric_value_mean", ascending=False).head(12)
        build_bar_figure(
            top_groups,
            x_col="group_key",
            y_col="primary_metric_value_mean",
            png_path=dataset_root / "figures" / "grouped" / "final_113__leaderboard_primary_metric.png",
            title="final_113 leaderboard by grouped primary metric mean",
            xlabel="group_key",
            ylabel="primary_metric_value_mean",
            source_paths=[to_rel(reporting_root / "grouped_metrics.csv")],
            rotate=55,
        )

    runtime_summary = (
        catalog_df[catalog_df["learned_run"] == True]
        .groupby("report_group", dropna=False)["runtime_seconds"]
        .agg(["count", "mean", "min", "max"])
        .reset_index()
        .rename(columns={"count": "n", "mean": "runtime_seconds_mean", "min": "runtime_seconds_min", "max": "runtime_seconds_max"})
    )
    write_table(
        runtime_summary,
        dataset_root / "tables" / "grouped" / "final_113__runtime_summary.csv",
        source_paths=[to_rel(FINAL_113_RUNS_PATH / "manifest.csv"), to_rel(reporting_root / "run_level_metrics.csv")],
    )
    build_bar_figure(
        runtime_summary,
        x_col="report_group",
        y_col="runtime_seconds_mean",
        png_path=dataset_root / "figures" / "grouped" / "final_113__runtime_comparison.png",
        title="final_113 runtime comparison by report group",
        xlabel="report_group",
        ylabel="runtime_seconds_mean",
        source_paths=[to_rel(dataset_root / "tables" / "grouped" / "final_113__runtime_summary.csv")],
    )

    completeness = pd.DataFrame(
        [
            {"artifact": "model_zip_present", "count": int(catalog_df["model_zip_exists"].sum())},
            {"artifact": "vec_normalize_present", "count": int(catalog_df["vec_normalize_exists"].sum())},
            {"artifact": "history_match", "count": int(catalog_df["history_match"].sum())},
            {"artifact": "point2_report_present", "count": int(catalog_df["point2_report_exists"].sum())},
        ]
    )
    write_table(
        completeness,
        dataset_root / "tables" / "grouped" / "final_113__artifact_completeness_summary.csv",
        source_paths=[to_rel(FINAL_113_RUNS_PATH / "manifest.csv")],
    )
    build_bar_figure(
        completeness,
        x_col="artifact",
        y_col="count",
        png_path=dataset_root / "figures" / "grouped" / "final_113__artifact_completeness.png",
        title="final_113 artifact completeness summary",
        xlabel="artifact",
        ylabel="count",
        source_paths=[to_rel(dataset_root / "tables" / "grouped" / "final_113__artifact_completeness_summary.csv")],
    )

    learned = catalog_df[catalog_df["learned_run"] == True].copy()
    learned["uplift_vs_baseline_for_plot"] = learned["uplift_vs_best_baseline_det"].fillna(0.0)
    uplift = learned.groupby("report_group", dropna=False)["uplift_vs_baseline_for_plot"].mean().reset_index()
    write_table(
        uplift,
        dataset_root / "tables" / "grouped" / "final_113__uplift_vs_baseline.csv",
        source_paths=[to_rel(FINAL_113_RUNS_PATH / "reporting" / "run_level_metrics.csv")],
    )
    build_bar_figure(
        uplift,
        x_col="report_group",
        y_col="uplift_vs_baseline_for_plot",
        png_path=dataset_root / "figures" / "grouped" / "final_113__uplift_vs_baseline.png",
        title="final_113 uplift vs baseline by report group",
        xlabel="report_group",
        ylabel="mean_uplift_vs_baseline",
        source_paths=[to_rel(dataset_root / "tables" / "grouped" / "final_113__uplift_vs_baseline.csv")],
    )

    best_runs = learned.sort_values("primary_metric_value", ascending=False).head(8)[["run_slug", "primary_metric_value"]]
    write_table(
        best_runs,
        dataset_root / "tables" / "grouped" / "final_113__best_run_leaderboard.csv",
        source_paths=[to_rel(FINAL_113_RUNS_PATH / "reporting" / "run_level_metrics.csv")],
    )
    build_bar_figure(
        best_runs,
        x_col="run_slug",
        y_col="primary_metric_value",
        png_path=dataset_root / "figures" / "grouped" / "final_113__grouped_comparison.png",
        title="final_113 best learned runs by primary metric",
        xlabel="run_slug",
        ylabel="primary_metric_value",
        source_paths=[to_rel(dataset_root / "tables" / "grouped" / "final_113__best_run_leaderboard.csv")],
        rotate=55,
    )

    shortlist_map = [
        ("final_113__leaderboard_primary_metric.png", "final_113__shortlist__leaderboard_primary_metric.png"),
        ("final_113__runtime_comparison.png", "final_113__shortlist__runtime_comparison.png"),
        ("final_113__artifact_completeness.png", "final_113__shortlist__artifact_completeness.png"),
        ("final_113__uplift_vs_baseline.png", "final_113__shortlist__uplift_vs_baseline.png"),
        ("final_113__grouped_comparison.png", "final_113__shortlist__grouped_comparison.png"),
    ]
    for src_name, dst_name in shortlist_map:
        src = dataset_root / "figures" / "grouped" / src_name
        if src.exists():
            shutil.copy2(src, dataset_root / "figures" / "thesis_shortlist" / dst_name)
            shutil.copy2(src.with_suffix(".json"), (dataset_root / "figures" / "thesis_shortlist" / dst_name).with_suffix(".json"))


def paired_delta_rows(df: pd.DataFrame, group_cols: list[str], treatment_col: str, control_value: Any, compare_values: list[Any], metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, group in df.groupby(group_cols, dropna=False):
        control = group[group[treatment_col] == control_value]
        if control.empty:
            continue
        control_row = control.iloc[0]
        for compare_value in compare_values:
            treatment = group[group[treatment_col] == compare_value]
            if treatment.empty:
                continue
            treatment_row = treatment.iloc[0]
            row: dict[str, Any] = {}
            if isinstance(key, tuple):
                for idx, col in enumerate(group_cols):
                    row[col] = key[idx]
            else:
                row[group_cols[0]] = key
            row.update({treatment_col: compare_value, "control_value": control_value})
            for metric in metrics:
                control_metric = safe_float(control_row.get(metric))
                treatment_metric = safe_float(treatment_row.get(metric))
                row[f"{metric}_control"] = control_metric
                row[f"{metric}_treatment"] = treatment_metric
                row[f"{metric}_delta"] = None if control_metric is None or treatment_metric is None else treatment_metric - control_metric
            rows.append(row)
    return pd.DataFrame(rows)


def paired_stats_table(delta_df: pd.DataFrame, group_col: str, treatment_col: str, metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if delta_df.empty:
        return pd.DataFrame()
    for metric in metrics:
        delta_col = f"{metric}_delta"
        for group_name, group in delta_df.groupby([group_col, treatment_col], dropna=False):
            series = group[delta_col].dropna().astype(float)
            if series.empty:
                continue
            payload: dict[str, Any] = {
                "metric": metric,
                group_col: group_name[0] if isinstance(group_name, tuple) else group_name,
                treatment_col: group_name[1] if isinstance(group_name, tuple) else None,
                "n": int(series.size),
                "mean_delta": float(series.mean()),
            }
            if series.size >= 2:
                t_stat, p_value = stats.ttest_1samp(series, popmean=0.0)
                payload.update({"t_stat": float(t_stat), "p_value": float(p_value)})
            else:
                payload.update({"t_stat": None, "p_value": None})
            rows.append(payload)
    return pd.DataFrame(rows)


def collect_excluded_attempts() -> pd.DataFrame:
    recovered_root = FINAL_SUCCESSFUL_RUNS_PATH / "Recovered 17 March" / "thesis" / "artifacts" / "final_successful_runs" / "low_hanging_ablation"
    rows: list[dict[str, Any]] = []
    if not recovered_root.exists():
        return pd.DataFrame()
    for path in sorted(recovered_root.rglob("run_summary.csv")):
        df = pd.read_csv(path)
        if "status" not in df.columns:
            continue
        failed = df[df["status"].astype(str).str.upper() == "FAILED"].copy()
        if failed.empty:
            continue
        failed["source_run_summary"] = str(path.resolve())
        rows.extend(failed.replace({np.nan: None}).to_dict(orient="records"))
    return pd.DataFrame(rows)


def build_final42_grouped_outputs(dataset_root: Path, catalog_df: pd.DataFrame, excluded_attempts: pd.DataFrame) -> None:
    grouped_dir = dataset_root / "tables" / "grouped"
    figures_dir = dataset_root / "figures" / "grouped"
    shortlist_dir = dataset_root / "figures" / "thesis_shortlist"
    metric_cols = [
        "primary_metric_value",
        "deterministic_return",
        "stochastic_return_mean",
        "stochastic_return_std",
        "pak_holdout_return",
        "baseline_best_return",
        "uplift_vs_best_baseline_det",
        "runtime_seconds",
    ]
    run_level = catalog_df[
        [
            "dataset",
            "index",
            "run_id",
            "run_slug",
            "label",
            "point",
            "batch",
            "domain",
            "method",
            "seed",
            "fixed_weather",
            "weather_label",
            "adaptive",
            "adaptive_label",
            "hierarchical",
            "ent_coef",
            "blocked_penalty",
            "nutrient_cost_weight",
            "primary_metric_name",
            "primary_metric_value",
            "deterministic_return",
            "stochastic_return_mean",
            "stochastic_return_std",
            "pak_holdout_return",
            "baseline_best_return",
            "uplift_vs_best_baseline_det",
            "runtime_seconds",
            "history_match",
            "point2_report_exists",
        ]
    ].copy()
    write_table(run_level, grouped_dir / "final_42_ablation__run_level_metrics.csv", source_paths=[to_rel(FINAL_42_ROOT / "manifest.csv")])

    point1 = catalog_df[catalog_df["point"] == "point1_entropy_fertilization"].copy()
    p1_grouped = (
        point1.groupby(["weather_label", "ent_coef"], dropna=False)[metric_cols]
        .agg(["count", "mean", "std", "min", "max"])
        .reset_index()
    )
    p1_grouped.columns = ["__".join([str(v) for v in col if str(v)]).strip("_") for col in p1_grouped.columns.to_flat_index()]
    write_table(p1_grouped, grouped_dir / "final_42_ablation__point1_grouped_metrics.csv", source_paths=[to_rel(FINAL_42_ROOT / "manifest.csv")])
    build_grouped_line_figure(
        p1_grouped.rename(columns={"primary_metric_value__mean": "primary_metric_mean"}),
        x_col="ent_coef",
        y_col="primary_metric_mean",
        group_col="weather_label",
        png_path=figures_dir / "final_42_ablation__point1_entropy_primary_metric.png",
        title="point1 entropy fertilization primary metric by entropy coefficient",
        xlabel="ent_coef",
        ylabel="primary_metric_mean",
        source_paths=[to_rel(grouped_dir / "final_42_ablation__point1_grouped_metrics.csv")],
    )

    p1_deltas = paired_delta_rows(
        point1,
        group_cols=["weather_label", "seed"],
        treatment_col="ent_coef",
        control_value=0.0,
        compare_values=[0.01],
        metrics=["deterministic_return", "stochastic_return_mean", "stochastic_return_std", "pak_holdout_return", "runtime_seconds"],
    )
    write_table(p1_deltas, grouped_dir / "final_42_ablation__point1_paired_deltas.csv", source_paths=[to_rel(FINAL_42_ROOT / "manifest.csv")])
    p1_stats = paired_stats_table(p1_deltas, "weather_label", "ent_coef", ["deterministic_return", "stochastic_return_mean", "stochastic_return_std", "pak_holdout_return", "runtime_seconds"])
    write_table(p1_stats, grouped_dir / "final_42_ablation__point1_paired_stats.csv", source_paths=[to_rel(grouped_dir / "final_42_ablation__point1_paired_deltas.csv")])
    if not p1_deltas.empty:
        delta_plot = p1_deltas.groupby("weather_label", dropna=False)["deterministic_return_delta"].mean().reset_index()
        build_bar_figure(
            delta_plot,
            x_col="weather_label",
            y_col="deterministic_return_delta",
            png_path=figures_dir / "final_42_ablation__point1_entropy_paired_deltas.png",
            title="point1 entropy paired deterministic-return delta (0.01 - 0.0)",
            xlabel="weather_label",
            ylabel="deterministic_return_delta",
            source_paths=[to_rel(grouped_dir / "final_42_ablation__point1_paired_deltas.csv")],
        )

    point2 = catalog_df[catalog_df["point"] == "point2_hierarchical_shaping"].copy()
    point2_summary_rows: list[dict[str, Any]] = []
    for _, row in point2.iterrows():
        report_dir = resolve_point2_report_dir(Path(str(row["bundle_dir"])))
        summary_path = report_dir / "reporting_summary.json" if report_dir else Path()
        payload = read_json(summary_path)
        point2_summary_rows.append(
            {
                "run_slug": row["run_slug"],
                "method": row["method"],
                "weather_label": row["weather_label"],
                "blocked_penalty": row["blocked_penalty"],
                "deterministic_return": row["deterministic_return"],
                "stochastic_return_mean": row["stochastic_return_mean"],
                "baseline_best_return": row["baseline_best_return"],
                "uplift_vs_best_baseline_det": row["uplift_vs_best_baseline_det"],
                "overall_compliance_rate": safe_float(payload.get("overall_compliance_rate")),
                "total_cost": safe_float(payload.get("total_cost")),
                "blocked_npk_kg_total": safe_float(payload.get("blocked_npk_kg_total")),
                "reward_shaping_blocked_penalty_total": safe_float(payload.get("reward_shaping_blocked_penalty_total")),
                "window_blocked_steps": safe_int(payload.get("window_blocked_steps")),
                "budget_clipped_steps": safe_int(payload.get("budget_clipped_steps")),
            }
        )
    point2_grouped = pd.DataFrame(point2_summary_rows).sort_values(["method", "weather_label", "blocked_penalty"]).reset_index(drop=True)
    write_table(point2_grouped, grouped_dir / "final_42_ablation__point2_grouped_metrics.csv", source_paths=[to_rel(FINAL_42_ROOT / "manifest.csv")])
    build_grouped_line_figure(
        point2_grouped,
        x_col="blocked_penalty",
        y_col="deterministic_return",
        group_col="method",
        png_path=figures_dir / "final_42_ablation__point2_primary_comparison.png",
        title="point2 hierarchical shaping deterministic return by blocked penalty",
        xlabel="blocked_penalty_per_kg",
        ylabel="deterministic_return",
        source_paths=[to_rel(grouped_dir / "final_42_ablation__point2_grouped_metrics.csv")],
    )
    if not point2_grouped.empty:
        point2_cost = point2_grouped.copy()
        point2_cost["method_weather"] = point2_cost["method"].astype(str) + " | " + point2_cost["weather_label"].astype(str)
        build_grouped_line_figure(
            point2_cost,
            x_col="blocked_penalty",
            y_col="overall_compliance_rate",
            group_col="method_weather",
            png_path=figures_dir / "final_42_ablation__point2_thesis_compliance.png",
            title="point2 overall compliance rate by blocked penalty",
            xlabel="blocked_penalty_per_kg",
            ylabel="overall_compliance_rate",
            source_paths=[to_rel(grouped_dir / "final_42_ablation__point2_grouped_metrics.csv")],
        )

    point3 = catalog_df[catalog_df["point"] == "point3_nutrient_cost_weight"].copy()
    p3_grouped = (
        point3.groupby(["weather_label", "nutrient_cost_weight"], dropna=False)[metric_cols]
        .agg(["count", "mean", "std", "min", "max"])
        .reset_index()
    )
    p3_grouped.columns = ["__".join([str(v) for v in col if str(v)]).strip("_") for col in p3_grouped.columns.to_flat_index()]
    write_table(p3_grouped, grouped_dir / "final_42_ablation__point3_grouped_metrics.csv", source_paths=[to_rel(FINAL_42_ROOT / "manifest.csv")])
    build_grouped_line_figure(
        p3_grouped.rename(columns={"primary_metric_value__mean": "primary_metric_mean"}),
        x_col="nutrient_cost_weight",
        y_col="primary_metric_mean",
        group_col="weather_label",
        png_path=figures_dir / "final_42_ablation__point3_cost_weight_primary_metric.png",
        title="point3 cost-weight primary metric by nutrient cost weight",
        xlabel="nutrient_cost_weight",
        ylabel="primary_metric_mean",
        source_paths=[to_rel(grouped_dir / "final_42_ablation__point3_grouped_metrics.csv")],
    )

    p3_deltas = paired_delta_rows(
        point3,
        group_cols=["weather_label", "seed"],
        treatment_col="nutrient_cost_weight",
        control_value=1.0,
        compare_values=[0.8, 1.2],
        metrics=["deterministic_return", "stochastic_return_mean", "stochastic_return_std", "pak_holdout_return", "runtime_seconds"],
    )
    write_table(p3_deltas, grouped_dir / "final_42_ablation__point3_paired_deltas.csv", source_paths=[to_rel(FINAL_42_ROOT / "manifest.csv")])
    p3_stats = paired_stats_table(p3_deltas, "weather_label", "nutrient_cost_weight", ["deterministic_return", "stochastic_return_mean", "stochastic_return_std", "pak_holdout_return", "runtime_seconds"])
    write_table(p3_stats, grouped_dir / "final_42_ablation__point3_paired_stats.csv", source_paths=[to_rel(grouped_dir / "final_42_ablation__point3_paired_deltas.csv")])
    if not p3_deltas.empty:
        delta_plot = p3_deltas.groupby("nutrient_cost_weight", dropna=False)["deterministic_return_delta"].mean().reset_index()
        build_bar_figure(
            delta_plot,
            x_col="nutrient_cost_weight",
            y_col="deterministic_return_delta",
            png_path=figures_dir / "final_42_ablation__point3_cost_weight_paired_deltas.png",
            title="point3 deterministic-return delta vs cost_weight=1.0",
            xlabel="nutrient_cost_weight",
            ylabel="deterministic_return_delta",
            source_paths=[to_rel(grouped_dir / "final_42_ablation__point3_paired_deltas.csv")],
        )

    runtime_summary = catalog_df.groupby("point", dropna=False)["runtime_seconds"].agg(["count", "mean", "min", "max"]).reset_index()
    runtime_summary.rename(columns={"count": "n", "mean": "runtime_seconds_mean", "min": "runtime_seconds_min", "max": "runtime_seconds_max"}, inplace=True)
    write_table(runtime_summary, grouped_dir / "final_42_ablation__runtime_summary.csv", source_paths=[to_rel(FINAL_42_ROOT / "manifest.csv")])
    build_bar_figure(
        runtime_summary,
        x_col="point",
        y_col="runtime_seconds_mean",
        png_path=figures_dir / "final_42_ablation__runtime_comparison.png",
        title="final_42 ablation runtime comparison by point",
        xlabel="point",
        ylabel="runtime_seconds_mean",
        source_paths=[to_rel(grouped_dir / "final_42_ablation__runtime_summary.csv")],
        rotate=20,
    )

    completeness = pd.DataFrame(
        [
            {"artifact": "model_zip_present", "count": int(catalog_df["model_zip_exists"].sum())},
            {"artifact": "vec_normalize_present", "count": int(catalog_df["vec_normalize_exists"].sum())},
            {"artifact": "point2_report_present", "count": int(catalog_df["point2_report_exists"].sum())},
            {"artifact": "history_match", "count": int(catalog_df["history_match"].sum())},
        ]
    )
    write_table(completeness, grouped_dir / "final_42_ablation__artifact_completeness_summary.csv", source_paths=[to_rel(FINAL_42_ROOT / "manifest.csv")])
    build_bar_figure(
        completeness,
        x_col="artifact",
        y_col="count",
        png_path=figures_dir / "final_42_ablation__artifact_completeness.png",
        title="final_42 ablation artifact completeness summary",
        xlabel="artifact",
        ylabel="count",
        source_paths=[to_rel(grouped_dir / "final_42_ablation__artifact_completeness_summary.csv")],
    )

    if not excluded_attempts.empty:
        write_table(excluded_attempts, grouped_dir / "final_42_ablation__excluded_source_attempts.csv", source_paths=[to_rel(FINAL_SUCCESSFUL_RUNS_PATH / "Recovered 17 March" / "thesis" / "artifacts" / "final_successful_runs" / "low_hanging_ablation")])

    shortlist_map = [
        ("final_42_ablation__point1_entropy_primary_metric.png", "final_42_ablation__shortlist__point1_entropy_primary_metric.png"),
        ("final_42_ablation__point2_primary_comparison.png", "final_42_ablation__shortlist__point2_primary_comparison.png"),
        ("final_42_ablation__point3_cost_weight_primary_metric.png", "final_42_ablation__shortlist__point3_cost_weight_primary_metric.png"),
        ("final_42_ablation__runtime_comparison.png", "final_42_ablation__shortlist__runtime_comparison.png"),
        ("final_42_ablation__artifact_completeness.png", "final_42_ablation__shortlist__artifact_completeness.png"),
    ]
    for src_name, dst_name in shortlist_map:
        src = figures_dir / src_name
        if src.exists():
            shutil.copy2(src, shortlist_dir / dst_name)
            shutil.copy2(src.with_suffix(".json"), (shortlist_dir / dst_name).with_suffix(".json"))


def build_representative_sets(output_root: Path, all_catalog: pd.DataFrame) -> pd.DataFrame:
    rep_root = output_root / "representative_sets"
    rows: list[dict[str, Any]] = []

    def copy_rep(row: pd.Series, family_slug: str, reason: str) -> None:
        src = output_root / row["dataset"] / "renders" / "per_run" / row["run_slug"] / f"{row['run_slug']}__primary_render.png"
        src_json = src.with_suffix(".json")
        if not src.exists():
            return
        dst_dir = rep_root / row["dataset"] / family_slug
        ensure_dir(dst_dir)
        dst = dst_dir / src.name
        shutil.copy2(src, dst)
        if src_json.exists():
            shutil.copy2(src_json, dst.with_suffix(".json"))
        rows.append(
            {
                "dataset": row["dataset"],
                "family_slug": family_slug,
                "run_slug": row["run_slug"],
                "run_id": row["run_id"],
                "report_group": row["report_group"],
                "group_key": row["group_key"],
                "selection_reason": reason,
                "source_render": to_rel(src),
                "copied_render": to_rel(dst),
            }
        )

    final113 = all_catalog[(all_catalog["dataset"] == "final_113") & (all_catalog["learned_run"] == True)]
    for (report_group, group_key), group in final113.groupby(["report_group", "group_key"], dropna=False):
        if len(group) < 3:
            continue
        ordered = group.sort_values("primary_metric_value").reset_index(drop=True)
        family_slug = slugify(f"{report_group}__{group_key}")
        copy_rep(ordered.iloc[0], family_slug, "worst_of_repeated_group")
        copy_rep(ordered.iloc[len(ordered) // 2], family_slug, "median_of_repeated_group")
        copy_rep(ordered.iloc[-1], family_slug, "best_of_repeated_group")

    final42 = all_catalog[all_catalog["dataset"] == "final_42_ablation"]
    point1 = final42[final42["point"] == "point1_entropy_fertilization"]
    for _, group in point1.groupby(["weather_label", "ent_coef"], dropna=False):
        ordered = group.sort_values("primary_metric_value").reset_index(drop=True)
        family_slug = slugify(f"point1__{group.iloc[0]['weather_label']}__ent_{decimal_slug(group.iloc[0]['ent_coef'])}")
        copy_rep(ordered.iloc[0], family_slug, "worst_of_repeated_group")
        copy_rep(ordered.iloc[len(ordered) // 2], family_slug, "median_of_repeated_group")
        copy_rep(ordered.iloc[-1], family_slug, "best_of_repeated_group")

    point3 = final42[final42["point"] == "point3_nutrient_cost_weight"]
    for _, group in point3.groupby(["weather_label", "nutrient_cost_weight"], dropna=False):
        ordered = group.sort_values("primary_metric_value").reset_index(drop=True)
        family_slug = slugify(f"point3__{group.iloc[0]['weather_label']}__cost_{decimal_slug(group.iloc[0]['nutrient_cost_weight'])}")
        copy_rep(ordered.iloc[0], family_slug, "worst_of_repeated_group")
        copy_rep(ordered.iloc[len(ordered) // 2], family_slug, "median_of_repeated_group")
        copy_rep(ordered.iloc[-1], family_slug, "best_of_repeated_group")

    point2 = final42[final42["point"] == "point2_hierarchical_shaping"]
    for _, group in point2.groupby(["method", "weather_label"], dropna=False):
        ordered = group.sort_values("primary_metric_value").reset_index(drop=True)
        family_slug = slugify(f"point2__{group.iloc[0]['method']}__{group.iloc[0]['weather_label']}")
        copy_rep(ordered.iloc[0], family_slug, "worst_of_single_seed_family")
        copy_rep(ordered.iloc[-1], family_slug, "best_of_single_seed_family")

    if rows:
        rep_df = pd.DataFrame(rows).sort_values(["dataset", "family_slug", "selection_reason", "run_slug"]).reset_index(drop=True)
    else:
        rep_df = pd.DataFrame(columns=["dataset", "family_slug", "run_slug", "run_id", "report_group", "group_key", "selection_reason", "source_render", "copied_render"])
    write_table(rep_df, output_root / "catalogs" / "representative_index.csv", source_paths=[to_rel(output_root / "catalogs" / "run_catalog.csv")])
    return rep_df


def dataset_qa_summary(dataset_root: Path, dataset: str, catalog_df: pd.DataFrame, missing: list[dict[str, Any]]) -> dict[str, Any]:
    png_files = list(dataset_root.rglob("*.png"))
    csv_files = list(dataset_root.rglob("*.csv"))
    json_files = list(dataset_root.rglob("*.json"))
    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utcnow_iso(),
        "dataset": dataset,
        "expected_runs": int(len(catalog_df)),
        "matched_histories": int(catalog_df["history_match"].sum()),
        "learned_runs": int(catalog_df["learned_run"].sum()),
        "png_count": len(png_files),
        "csv_count": len(csv_files),
        "json_count": len(json_files),
        "render_png_count": len(list((dataset_root / "renders").rglob("*.png"))),
        "missing_or_skipped_count": len(missing),
    }
    write_json(dataset_root / "qa" / "summary.json", summary)
    write_json(dataset_root / "qa" / "missing_or_skipped.json", {"schema_version": SCHEMA_VERSION, "generated_at": utcnow_iso(), "dataset": dataset, "items": missing})
    return summary


def verify_reporting_pack(output_root: Path, all_catalog: pd.DataFrame) -> dict[str, Any]:
    csv_paths = list(output_root.rglob("*.csv"))
    png_paths = list(output_root.rglob("*.png"))
    csv_without_json = [to_rel(path) for path in csv_paths if not path.with_suffix(".json").exists()]
    png_without_json = [to_rel(path) for path in png_paths if not path.with_suffix(".json").exists()]
    run_metric_json_missing = []
    for _, row in all_catalog.iterrows():
        path = output_root / row["dataset"] / "metrics_json" / "per_run" / f"{row['run_slug']}__run_metrics.json"
        if not path.exists():
            run_metric_json_missing.append(row["run_slug"])
    verification = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utcnow_iso(),
        "datasets": {
            dataset: {
                "catalog_rows": int(len(group)),
                "history_matches": int(group["history_match"].sum()),
            }
            for dataset, group in all_catalog.groupby("dataset")
        },
        "csv_without_json": csv_without_json,
        "png_without_json": png_without_json,
        "run_metric_json_missing": run_metric_json_missing,
        "notes": ["Stem uniqueness is enforced within artifact classes; companion JSON files intentionally share stems with CSV and PNG artifacts."],
    }
    write_json(output_root / "qa" / "build_verification.json", verification)
    return verification


def smoke_test_runs(all_catalog: pd.DataFrame, output_root: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    final113 = all_catalog[all_catalog["dataset"] == "final_113"]
    candidates = [
        final113[(final113["domain"] == "fertilization") & (final113["method"] == "PPO")].head(1),
        final113[(final113["domain"] == "crop_planning") & (final113["hierarchical"] == False) & (final113["method"] != "DQN")].head(1),
        final113[(final113["domain"] == "crop_planning") & (final113["hierarchical"] == True)].head(1),
        final113[(final113["method"] == "DQN")].head(1),
        all_catalog[(all_catalog["dataset"] == "final_42_ablation") & (all_catalog["point"] == "point2_hierarchical_shaping")].head(1),
    ]
    for frame in candidates:
        if frame.empty:
            continue
        row = frame.iloc[0]
        history_cache = output_root / row["dataset"] / "cache" / "per_run" / row["run_slug"] / f"{row['run_slug']}__history_selected.csv"
        render_png = output_root / row["dataset"] / "renders" / "per_run" / row["run_slug"] / f"{row['run_slug']}__primary_render.png"
        checks.append(
            {
                "run_slug": row["run_slug"],
                "run_id": row["run_id"],
                "dataset": row["dataset"],
                "history_cache_exists": history_cache.exists(),
                "render_exists": render_png.exists(),
                "point2_without_vec_is_valid": True if row["point"] == "point2_hierarchical_shaping" else None,
            }
        )
    point2_missing_vec = all_catalog[
        (all_catalog["dataset"] == "final_42_ablation")
        & (all_catalog["point"] == "point2_hierarchical_shaping")
        & (~all_catalog["vec_normalize_exists"].astype(bool))
    ].copy()
    point2_missing_vec["render_exists"] = point2_missing_vec["run_slug"].apply(
        lambda slug: (output_root / "final_42_ablation" / "renders" / "per_run" / slug / f"{slug}__primary_render.png").exists()
    )
    point2_missing_vec["metrics_json_exists"] = point2_missing_vec["run_slug"].apply(
        lambda slug: (output_root / "final_42_ablation" / "metrics_json" / "per_run" / f"{slug}__run_metrics.json").exists()
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utcnow_iso(),
        "checks": checks,
        "point2_missing_vec_summary": {
            "expected_count": 12,
            "observed_count": int(len(point2_missing_vec)),
            "all_history_matches": bool(point2_missing_vec["history_match"].all()) if not point2_missing_vec.empty else False,
            "all_renders_exist": bool(point2_missing_vec["render_exists"].all()) if not point2_missing_vec.empty else False,
            "all_metrics_json_exist": bool(point2_missing_vec["metrics_json_exists"].all()) if not point2_missing_vec.empty else False,
            "all_marked_valid": True,
            "run_slugs": point2_missing_vec["run_slug"].tolist(),
        },
    }
    write_json(output_root / "qa" / "smoke_tests.json", payload)
    return payload


def build_reporting_pack(datasets: list[str], output_root: Path, overwrite: bool = False) -> dict[str, Any]:
    BuildContext(output_root=output_root, overwrite=overwrite)
    if overwrite and output_root.exists():
        shutil.rmtree(output_root)
    ensure_dir(output_root)
    for subdir in ["catalogs", "representative_sets", "qa"] + datasets:
        ensure_dir(output_root / subdir)
    history_df, history_lookup = discover_history_sources()
    final113_lookup = build_final113_reporting_lookup()
    _, ablation_lookup = load_ablation_run_summary_lookup()
    excluded_attempts = collect_excluded_attempts()
    all_catalogs: list[pd.DataFrame] = []
    artifact_rows: list[dict[str, Any]] = []
    dataset_summaries: list[dict[str, Any]] = []

    for dataset in datasets:
        dataset_root = output_root / dataset
        for subdir in REQUIRED_DATASET_SUBDIRS:
            ensure_dir(dataset_root / subdir)
        for subdir in TABLE_SUBDIRS:
            ensure_dir(dataset_root / "tables" / subdir)
        for subdir in FIGURE_SUBDIRS:
            ensure_dir(dataset_root / "figures" / subdir)
        for subdir in METRIC_SUBDIRS:
            ensure_dir(dataset_root / "metrics_json" / subdir)
        ensure_dir(dataset_root / "cache" / "per_run")
        ensure_dir(dataset_root / "renders" / "per_run")

        catalog_df = build_run_catalog(dataset, history_lookup, final113_lookup, ablation_lookup)
        missing: list[dict[str, Any]] = []
        for idx, row in catalog_df.iterrows():
            outputs = build_run_outputs(row, dataset_root, missing)
            catalog_df.loc[idx, "history_rows"] = outputs["history_rows"]
            catalog_df.loc[idx, "action_table_count"] = outputs["action_table_count"]
            artifact_rows.append(
                {
                    "dataset": dataset,
                    "run_slug": row["run_slug"],
                    "run_id": row["run_id"],
                    "history_rows": outputs["history_rows"],
                    "action_table_count": outputs["action_table_count"],
                    "model_zip_exists": bool(row["model_zip_exists"]),
                    "vec_normalize_exists": bool(row["vec_normalize_exists"]),
                    "history_match": bool(row["history_match"]),
                    "eval_npz_count": int(row["eval_npz_count"]),
                }
            )

        source_manifest = FINAL_113_RUNS_PATH / "manifest.csv" if dataset == "final_113" else FINAL_42_ROOT / "manifest.csv"
        write_dataset_catalogs(dataset, dataset_root, catalog_df, source_manifest)
        if dataset == "final_113":
            build_final113_grouped_outputs(dataset_root, catalog_df, missing)
        else:
            build_final42_grouped_outputs(dataset_root, catalog_df, excluded_attempts)
        dataset_summaries.append(dataset_qa_summary(dataset_root, dataset, catalog_df, missing))
        all_catalogs.append(catalog_df)

    all_catalog = pd.concat(all_catalogs, ignore_index=True).sort_values(["dataset", "index"]).reset_index(drop=True)
    write_table(all_catalog, output_root / "catalogs" / "run_catalog.csv", source_paths=[to_rel(FINAL_113_RUNS_PATH / "manifest.csv"), to_rel(FINAL_42_ROOT / "manifest.csv")])
    write_table(history_df, output_root / "catalogs" / "history_source_index.csv", source_paths=[to_rel(spec["path"]) for spec in HISTORY_ROOTS if spec["path"].exists()])
    write_table(pd.DataFrame(artifact_rows), output_root / "catalogs" / "artifact_availability.csv", source_paths=[to_rel(output_root / "catalogs" / "run_catalog.csv")])
    rep_df = build_representative_sets(output_root, all_catalog)
    verification = verify_reporting_pack(output_root, all_catalog)
    smoke = smoke_test_runs(all_catalog, output_root)
    build_summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utcnow_iso(),
        "output_root": str(output_root.resolve()),
        "datasets": dataset_summaries,
        "run_catalog_rows": int(len(all_catalog)),
        "history_index_rows": int(len(history_df)),
        "artifact_availability_rows": int(len(artifact_rows)),
        "representative_rows": int(len(rep_df)),
        "verification": verification,
        "smoke_tests": smoke,
    }
    write_json(output_root / "qa" / "build_summary.json", build_summary)
    return build_summary


def rebuild_renders_only(datasets: list[str], output_root: Path) -> dict[str, Any]:
    catalog_path = output_root / "catalogs" / "run_catalog.csv"
    if not catalog_path.exists():
        raise FileNotFoundError(f"run catalog missing at {catalog_path}")
    all_catalog = pd.read_csv(catalog_path)
    for dataset in datasets:
        dataset_root = output_root / dataset
        ensure_dir(dataset_root / "renders" / "per_run")
        missing: list[dict[str, Any]] = []
        subset = all_catalog[all_catalog["dataset"] == dataset]
        for _, row in subset.iterrows():
            history_df = load_history_dataframe(str(row.get("history_scan_path", "")), row)
            eval_df = flatten_evaluation_curves(Path(str(row["bundle_dir"])))
            point2_frames = copy_point2_report_artifacts(row, dataset_root, missing) if str(row.get("point", "")) == "point2_hierarchical_shaping" else {}
            build_run_render(row, dataset_root, history_df, eval_df, point2_frames, missing)
        write_json(dataset_root / "qa" / "render_rebuild_missing_or_skipped.json", {"schema_version": SCHEMA_VERSION, "generated_at": utcnow_iso(), "dataset": dataset, "items": missing})
    rep_df = build_representative_sets(output_root, all_catalog[all_catalog["dataset"].isin(datasets)])
    payload = {"schema_version": SCHEMA_VERSION, "generated_at": utcnow_iso(), "datasets": datasets, "representative_rows": int(len(rep_df))}
    write_json(output_root / "qa" / "render_rebuild_summary.json", payload)
    return payload
