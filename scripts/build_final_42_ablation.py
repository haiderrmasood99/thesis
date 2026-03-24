#!/usr/bin/env python3
"""Assemble a canonical 42-run low-hanging ablation bundle set.

This builds `artifacts/final_successful_runs/final_42_ablation/` from the
March 17 recovered materials without modifying or deleting the originals.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cyclesgym.utils.paths import FINAL_SUCCESSFUL_RUNS_PATH


RECOVERED_ROOT = FINAL_SUCCESSFUL_RUNS_PATH / "Recovered 17 March"
RECOVERED_THESIS_ROOT = RECOVERED_ROOT / "thesis"
RECOVERED_WANDB_ROOT = RECOVERED_THESIS_ROOT / "wandb"
RECOVERED_VEC_ROOT = RECOVERED_THESIS_ROOT / "runs"
RECOVERED_ABLATION_ROOT = (
    RECOVERED_THESIS_ROOT / "artifacts" / "final_successful_runs" / "low_hanging_ablation"
)
RECOVERED_EXPORT_ROOT = RECOVERED_ROOT / "wandb_full_backup"
RECOVERED_EXPORT_RUNS = RECOVERED_EXPORT_ROOT / "17-March-Runs"
EXPORT_MANIFEST = RECOVERED_EXPORT_ROOT / "all_runs_manifest.csv"

FINAL_42_ROOT = FINAL_SUCCESSFUL_RUNS_PATH / "final_42_ablation"
FINAL_42_BUNDLES = FINAL_42_ROOT / "bundles"
FINAL_42_REPORTING = FINAL_42_ROOT / "reporting"
FINAL_42_EXPORTS = FINAL_42_ROOT / "source_exports"
FINAL_42_MANIFEST = FINAL_42_ROOT / "manifest.csv"
FINAL_42_README = FINAL_42_ROOT / "README.md"

POINT_ORDER = {
    "point1_entropy_fertilization": 1,
    "point2_hierarchical_shaping": 2,
    "point3_nutrient_cost_weight": 3,
}

MANIFEST_FIELDS = [
    "index",
    "label",
    "point",
    "batch",
    "domain",
    "method",
    "run_id",
    "run_name",
    "bundle_dir",
    "summary_json_status",
    "run_summary_status",
    "ablation_log_status",
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
    "report_status",
    "recovered_export_status",
    "source_kind",
    "source_project",
    "source_run_name",
    "source_created",
    "source_summary_json",
    "source_log",
    "source_raw_wandb_dir",
    "source_export_dir",
    "source_report_dir",
    "notes",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return re.sub(r"_+", "_", slug)


def _bundle_dir_rel(dst_bundle_dir: Path) -> str:
    rel = Path("final_successful_runs") / "final_42_ablation" / "bundles" / dst_bundle_dir.name
    return str(rel)


def _notes_text(notes: list[str]) -> str:
    return ";".join(note for note in notes if note)


def _copy_file(src: Path | None, dst: Path) -> str:
    if src is None or not src.exists():
        return "missing"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return "copied"


def _copy_dir(src: Path | None, dst: Path) -> str:
    if src is None or not src.exists():
        return "missing"
    shutil.copytree(src, dst)
    return "copied"


def _copy_dir_contents(src: Path | None, dst: Path) -> str:
    if src is None or not src.exists():
        return "missing"
    dst.mkdir(parents=True, exist_ok=True)
    for child in sorted(src.iterdir()):
        child_dst = dst / child.name
        if child.is_dir():
            shutil.copytree(child, child_dst)
        else:
            shutil.copy2(child, child_dst)
    return "copied"


def _copy_globbed_files(src_dir: Path | None, pattern: str, dst_dir: Path) -> str:
    if src_dir is None or not src_dir.exists():
        return "missing"
    matches = sorted(src_dir.glob(pattern))
    if not matches:
        return "missing"
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in matches:
        shutil.copy2(src, dst_dir / src.name)
    return "copied"


def _copy_recovered_export_metadata(src_run_dir: Path, dst_bundle_dir: Path) -> str:
    export_root = dst_bundle_dir / "recovered_export"
    copied = False
    for filename in (
        "artifacts_manifest.csv",
        "config.json",
        "history_export_status.json",
        "metadata.json",
        "rawconfig.json",
        "run_core.json",
        "run_files_manifest.csv",
        "summary.json",
        "system_metrics.json",
    ):
        src = src_run_dir / filename
        if src.exists():
            export_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, export_root / filename)
            copied = True
    return "copied" if copied else "missing"


def _workspace_path_from_export(path_value: str) -> Path:
    posix = PurePosixPath(path_value)
    parts = list(posix.parts)
    try:
        idx = parts.index("thesis")
    except ValueError as exc:
        raise RuntimeError(f"Unexpected export path: {path_value}") from exc
    return RECOVERED_THESIS_ROOT.joinpath(*parts[idx + 1 :])


def _summary_path(row: dict[str, str]) -> Path:
    return _workspace_path_from_export(row["summary.summary_json_path"])


def _point_name(summary_path: Path) -> str:
    return summary_path.parent.parent.parent.name


def _batch_name(summary_path: Path) -> str:
    return summary_path.parent.parent.name


def _domain_for_point(point_name: str) -> str:
    if point_name == "point2_hierarchical_shaping":
        return "crop_planning"
    return "fertilization"


def _find_raw_run_dir(run_id: str) -> Path | None:
    matches = sorted(RECOVERED_WANDB_ROOT.glob(f"run-*-{run_id}"))
    return matches[0] if matches else None


def _find_export_run_dir(run_id: str) -> Path | None:
    matches = sorted(RECOVERED_EXPORT_RUNS.glob(f"{run_id}__*"))
    return matches[0] if matches else None


def _collect_rows() -> list[dict[str, str]]:
    rows = [row for row in _read_csv(EXPORT_MANIFEST) if row.get("state", "").strip().lower() == "finished"]
    rows.sort(key=lambda row: (
        POINT_ORDER.get(_point_name(_summary_path(row)), 99),
        _batch_name(_summary_path(row)),
        _summary_path(row).stem,
    ))
    return rows


def _write_bundle_metadata(
    dst_bundle_dir: Path,
    *,
    index: int,
    label: str,
    point: str,
    batch: str,
    domain: str,
    method: str,
    run_id: str,
    run_name: str,
    notes: list[str],
    source_summary_json: Path,
    source_raw_wandb_dir: Path,
    source_export_dir: Path,
    source_log: Path | None,
    source_report_dir: Path | None,
    move_status: dict[str, str],
) -> None:
    payload = {
        "index": index,
        "label": label,
        "point": point,
        "batch": batch,
        "domain": domain,
        "method": method,
        "run_id": run_id,
        "run_name": run_name,
        "bundle_dir": str(dst_bundle_dir),
        "source_summary_json": str(source_summary_json),
        "source_raw_wandb_dir": str(source_raw_wandb_dir),
        "source_export_dir": str(source_export_dir),
        "source_log": str(source_log) if source_log else "",
        "source_report_dir": str(source_report_dir) if source_report_dir and source_report_dir.exists() else "",
        "notes": notes,
        "move_status": move_status,
    }
    (dst_bundle_dir / "bundle_metadata.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_bundle(index: int, row: dict[str, str]) -> dict[str, str]:
    run_id = row["run_id"]
    run_name = row["run_name"]
    method = row["config.algo"]
    summary_path = _summary_path(row)
    point = _point_name(summary_path)
    batch = _batch_name(summary_path)
    domain = _domain_for_point(point)
    label = f"{point.replace('_', ' ')} | {summary_path.stem}"

    raw_run_dir = _find_raw_run_dir(run_id)
    export_run_dir = _find_export_run_dir(run_id)
    if raw_run_dir is None or export_run_dir is None:
        raise RuntimeError(f"Missing source directories for run_id={run_id}")

    log_path = summary_path.parent.parent / "logs" / f"{summary_path.stem}.log"
    run_summary_path = summary_path.parent.parent / "run_summary.csv"
    report_dir = summary_path.parent.parent / "thesis_reports" / summary_path.stem

    raw_files_dir = raw_run_dir / "files"
    bundle_name = f"{index:03d}_{_slugify(summary_path.stem)}"
    dst_bundle_dir = FINAL_42_BUNDLES / bundle_name
    dst_bundle_dir.mkdir(parents=True, exist_ok=True)

    run_record = next(raw_run_dir.glob("run-*.wandb"), None)
    model_zip_src = raw_files_dir / "model.zip"
    if not model_zip_src.exists():
        model_zip_src = export_run_dir / "run_files" / "model.zip"

    statuses = {
        "summary_json_status": _copy_file(summary_path, dst_bundle_dir / "summary" / summary_path.name),
        "run_summary_status": _copy_file(run_summary_path, dst_bundle_dir / "summary" / "run_summary.csv"),
        "ablation_log_status": _copy_file(log_path, dst_bundle_dir / "logs" / log_path.name),
        "config_status": _copy_file(raw_files_dir / "config.yaml", dst_bundle_dir / "wandb" / "config.yaml"),
        "wandb_summary_status": _copy_file(
            raw_files_dir / "wandb-summary.json", dst_bundle_dir / "wandb" / "wandb-summary.json"
        ),
        "wandb_metadata_status": _copy_file(
            raw_files_dir / "wandb-metadata.json", dst_bundle_dir / "wandb" / "wandb-metadata.json"
        ),
        "requirements_status": _copy_file(
            raw_files_dir / "requirements.txt", dst_bundle_dir / "wandb" / "requirements.txt"
        ),
        "diff_patch_status": _copy_globbed_files(raw_files_dir, "diff*.patch", dst_bundle_dir / "wandb"),
        "output_log_status": _copy_file(raw_files_dir / "output.log", dst_bundle_dir / "wandb" / "output.log"),
        "run_record_status": _copy_file(run_record, dst_bundle_dir / "wandb" / run_record.name) if run_record else "missing",
        "model_zip_status": _copy_file(model_zip_src, dst_bundle_dir / "models" / "model.zip"),
        "models_dir_status": _copy_dir_contents(raw_files_dir / "models", dst_bundle_dir / "models" / "checkpoints"),
        "vec_normalize_status": _copy_file(
            RECOVERED_VEC_ROOT / f"vec_normalize_{run_id}.pkl",
            dst_bundle_dir / "runtime" / f"vec_normalize_{run_id}.pkl",
        ),
        "report_status": _copy_dir(report_dir if report_dir.exists() else None, dst_bundle_dir / "reports" / report_dir.name),
        "recovered_export_status": _copy_recovered_export_metadata(export_run_dir, dst_bundle_dir),
    }

    notes = [
        "bundle_built_from_recovered_march17_raw_wandb_and_export_manifest",
    ]
    if point == "point2_hierarchical_shaping" and statuses["vec_normalize_status"] == "missing":
        notes.append("crop_planning_run_has_no_vec_normalize_sidecar_in_source_code")
    if statuses["models_dir_status"] == "missing":
        notes.append("raw_wandb_models_checkpoint_dir_missing")
    if report_dir.exists():
        notes.append("per_run_hierarchical_report_present")

    _write_bundle_metadata(
        dst_bundle_dir,
        index=index,
        label=label,
        point=point,
        batch=batch,
        domain=domain,
        method=method,
        run_id=run_id,
        run_name=run_name,
        notes=notes,
        source_summary_json=summary_path,
        source_raw_wandb_dir=raw_run_dir,
        source_export_dir=export_run_dir,
        source_log=log_path if log_path.exists() else None,
        source_report_dir=report_dir if report_dir.exists() else None,
        move_status=statuses,
    )

    return {
        "index": str(index),
        "label": label,
        "point": point,
        "batch": batch,
        "domain": domain,
        "method": method,
        "run_id": run_id,
        "run_name": run_name,
        "bundle_dir": _bundle_dir_rel(dst_bundle_dir),
        "summary_json_status": statuses["summary_json_status"],
        "run_summary_status": statuses["run_summary_status"],
        "ablation_log_status": statuses["ablation_log_status"],
        "config_status": statuses["config_status"],
        "wandb_summary_status": statuses["wandb_summary_status"],
        "wandb_metadata_status": statuses["wandb_metadata_status"],
        "requirements_status": statuses["requirements_status"],
        "diff_patch_status": statuses["diff_patch_status"],
        "output_log_status": statuses["output_log_status"],
        "run_record_status": statuses["run_record_status"],
        "model_zip_status": statuses["model_zip_status"],
        "models_dir_status": statuses["models_dir_status"],
        "vec_normalize_status": statuses["vec_normalize_status"],
        "report_status": statuses["report_status"],
        "recovered_export_status": statuses["recovered_export_status"],
        "source_kind": "recovered_march17_ablation",
        "source_project": "Recovered 17 March/wandb_full_backup/17-March-Runs",
        "source_run_name": run_name,
        "source_created": row.get("created_at", ""),
        "source_summary_json": str(summary_path),
        "source_log": str(log_path) if log_path.exists() else "",
        "source_raw_wandb_dir": str(raw_run_dir),
        "source_export_dir": str(export_run_dir),
        "source_report_dir": str(report_dir) if report_dir.exists() else "",
        "notes": _notes_text(notes),
    }


def _copy_source_exports() -> None:
    FINAL_42_EXPORTS.mkdir(parents=True, exist_ok=True)
    for path in (
        EXPORT_MANIFEST,
        RECOVERED_EXPORT_ROOT / "backup_manifest.json",
        RECOVERED_EXPORT_ROOT / "errors.json",
    ):
        if path.exists():
            shutil.copy2(path, FINAL_42_EXPORTS / path.name)
    for path in RECOVERED_ROOT.glob("17 March wandb_export*.csv"):
        shutil.copy2(path, FINAL_42_EXPORTS / path.name)


def _write_readme(manifest_rows: list[dict[str, str]]) -> None:
    bundle_count = len(manifest_rows)
    model_count = sum(1 for row in manifest_rows if row["model_zip_status"] != "missing")
    checkpoints_count = sum(1 for row in manifest_rows if row["models_dir_status"] != "missing")
    vec_count = sum(1 for row in manifest_rows if row["vec_normalize_status"] != "missing")
    report_count = sum(1 for row in manifest_rows if row["report_status"] != "missing")
    point_counts = {
        point: sum(1 for row in manifest_rows if row["point"] == point)
        for point in sorted(POINT_ORDER, key=POINT_ORDER.get)
    }

    lines = [
        "# Final 42 Ablation Runs",
        "",
        "This folder is the canonical frozen 42-run low-hanging ablation evidence set assembled from the March 17 recovered raw W&B folders plus the recovered export manifest.",
        "",
        f"- total bundles: `{bundle_count}`",
        f"- bundles with `model.zip`: `{model_count}`",
        f"- bundles with checkpoint directories beyond `model.zip`: `{checkpoints_count}`",
        f"- bundles with `vec_normalize` sidecars: `{vec_count}`",
        f"- bundles with hierarchical report directories: `{report_count}`",
        f"- point1 entropy fertilization bundles: `{point_counts['point1_entropy_fertilization']}`",
        f"- point2 hierarchical shaping bundles: `{point_counts['point2_hierarchical_shaping']}`",
        f"- point3 nutrient cost weight bundles: `{point_counts['point3_nutrient_cost_weight']}`",
        "",
        "## Layout",
        "",
        "- `bundles/`: one folder per recovered ablation run",
        "- `manifest.csv`: full inventory and completeness statuses for the 42 bundles",
        "- `reporting/low_hanging_ablation/`: recovered ablation summaries, logs, and per-run hierarchical reports",
        "- `source_exports/`: recovered W&B export CSV and backup manifest files used to assemble this set",
        "",
        "## Notes",
        "",
        "- `final_113/` remains the canonical final matrix folder for thesis-wide reporting.",
        "- The 12 point2 crop-planning hierarchical-shaping runs do not include `vec_normalize_*.pkl` sidecars because that code path uses `VecNormalize` in memory but does not persist a separate stats file.",
        "- The 30 fertilization runs do include `vec_normalize_*.pkl` sidecars and are copied into each bundle's `runtime/` folder.",
        "- Originals under `Recovered 17 March/` were left untouched.",
    ]
    FINAL_42_README.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if FINAL_42_ROOT.exists():
        raise SystemExit(f"Destination already exists, refusing to overwrite: {FINAL_42_ROOT}")

    rows = _collect_rows()
    if len(rows) != 42:
        raise RuntimeError(f"Expected 42 finished export rows, found {len(rows)}")

    FINAL_42_BUNDLES.mkdir(parents=True, exist_ok=True)
    shutil.copytree(RECOVERED_ABLATION_ROOT, FINAL_42_REPORTING / "low_hanging_ablation")
    _copy_source_exports()

    manifest_rows = [_build_bundle(index, row) for index, row in enumerate(rows, start=1)]
    _write_csv(FINAL_42_MANIFEST, manifest_rows, MANIFEST_FIELDS)
    _write_readme(manifest_rows)

    print(f"Built {len(manifest_rows)} bundles at {FINAL_42_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
