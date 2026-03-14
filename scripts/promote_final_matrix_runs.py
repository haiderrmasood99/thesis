#!/usr/bin/env python3
"""Promote the successful final-matrix run artifacts into one curated location.

This script moves reusable artifacts out of the archive tree under
`Local Files and Folders/` into `artifacts/final_successful_runs/bundles/`.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cyclesgym.utils.paths import (
    FINAL_SUCCESSFUL_RUN_BUNDLES_PATH,
    FINAL_SUCCESSFUL_RUNS_PATH,
    LOCAL_ARCHIVE_PATH,
)


PLAN_SUMMARY = LOCAL_ARCHIVE_PATH / "runs" / "experiment_summaries" / "run_experiments_7_3_2026_summary.csv"
NON_HIER_SUMMARY = (
    LOCAL_ARCHIVE_PATH
    / "runs"
    / "experiment_summaries"
    / "non_hier_10_3_2026_20260309_193918"
    / "summary.csv"
)
HIER_SUMMARY = (
    LOCAL_ARCHIVE_PATH
    / "runs"
    / "experiment_summaries"
    / "hier_parallel_10_3_2026_20260309_194132"
    / "summary.csv"
)
CAMPAIGN_METRICS_DIR = (
    LOCAL_ARCHIVE_PATH / "runs" / "experiment_summaries" / "campaign_20260307_164340" / "metrics"
)
ARCHIVE_SUMMARIES_ROOT = LOCAL_ARCHIVE_PATH / "runs" / "experiment_summaries"
ARCHIVE_WANDB_ROOT = LOCAL_ARCHIVE_PATH / "wandb"
ARCHIVE_RUNS_ROOT = LOCAL_ARCHIVE_PATH / "runs"
MANIFEST_PATH = FINAL_SUCCESSFUL_RUNS_PATH / "manifest.csv"
MISSING_PATH = FINAL_SUCCESSFUL_RUNS_PATH / "missing_runs.csv"
README_PATH = FINAL_SUCCESSFUL_RUNS_PATH / "README.md"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return re.sub(r"_+", "_", slug)


def _move_path(src: Path, dst: Path) -> str:
    if dst.exists():
        return "already_present"
    if not src.exists():
        return "missing"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return "moved"


def _load_plan_rows() -> dict[int, dict[str, str]]:
    return {int(row["index"]): row for row in _read_csv(PLAN_SUMMARY)}


def _load_actual_status_rows() -> tuple[dict[int, dict[str, str]], dict[int, dict[str, str]]]:
    non_hier_rows = {int(row["index"]): row for row in _read_csv(NON_HIER_SUMMARY)}
    hier_rows = {int(row["index"]): row for row in _read_csv(HIER_SUMMARY)}
    return non_hier_rows, hier_rows


def _successful_indices(non_hier_rows: dict[int, dict[str, str]], hier_rows: dict[int, dict[str, str]]) -> list[int]:
    indices = list(range(1, 75))
    indices.extend(idx for idx, row in non_hier_rows.items() if row.get("status") == "OK")
    indices.extend(idx for idx, row in hier_rows.items() if row.get("status") == "OK")
    return sorted(set(indices))


def _missing_indices(non_hier_rows: dict[int, dict[str, str]], hier_rows: dict[int, dict[str, str]]) -> list[int]:
    missing: list[int] = []
    for idx, row in sorted(non_hier_rows.items()):
        if row.get("status") != "OK":
            missing.append(idx)
    for idx, row in sorted(hier_rows.items()):
        if row.get("status") != "OK":
            missing.append(idx)
    return sorted(set(missing))


def _summary_path_for_index(
    idx: int,
    non_hier_rows: dict[int, dict[str, str]],
    hier_rows: dict[int, dict[str, str]],
) -> Path | None:
    if idx <= 74:
        matches = sorted(CAMPAIGN_METRICS_DIR.glob(f"{idx:03d}_*.json"))
        return matches[0] if matches else None
    if idx in hier_rows and hier_rows[idx].get("status") == "OK":
        return LOCAL_ARCHIVE_PATH / Path(hier_rows[idx]["summary_json"])
    if idx in non_hier_rows and non_hier_rows[idx].get("status") == "OK":
        return LOCAL_ARCHIVE_PATH / Path(non_hier_rows[idx]["summary_json"])
    return None


def _wandb_run_dir(run_id: str) -> Path | None:
    matches = sorted(ARCHIVE_WANDB_ROOT.glob(f"run-*-{run_id}"))
    return matches[0] if matches else None


def _optional_move(moves: list[tuple[str, Path, Path]]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for key, src, dst in moves:
        statuses[key] = _move_path(src, dst)
    return statuses


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_readme(successful_rows: list[dict[str, str]], missing_rows: list[dict[str, str]]) -> None:
    moved_bundles = len(successful_rows)
    moved_models = sum(1 for row in successful_rows if row["model_zip_status"] == "moved" or row["models_dir_status"] == "moved")
    moved_vec = sum(1 for row in successful_rows if row["vec_normalize_status"] == "moved")
    moved_reports = sum(1 for row in successful_rows if row["hierarchical_report_status"] == "moved")
    text = "\n".join(
        [
            "# Final Successful Runs",
            "",
            "This folder contains the curated artifact bundles promoted out of `Local Files and Folders/`.",
            "",
            f"- successful matrix bundles promoted: `{moved_bundles}`",
            f"- bundles with checkpoint files moved: `{moved_models}`",
            f"- bundles with `vec_normalize` files moved: `{moved_vec}`",
            f"- bundles with hierarchical report folders moved: `{moved_reports}`",
            f"- planned matrix rows left out: `{len(missing_rows)}`",
            "",
            "## Layout",
            "",
            "- `bundles/`: one folder per successful final-matrix run",
            "- `manifest.csv`: promoted bundle inventory",
            "- `missing_runs.csv`: planned rows left out of promotion and why",
            "",
            "## Notes",
            "",
            "- The baseline-only run is included as a successful bundle even though it has no model checkpoint by design.",
            "- Crop-planning bundles do not include `vec_normalize` files because those files were not produced for those runs in the archive.",
            "- The four left-out rows are the failed DQN ablation slots from the actual matrix completion summary.",
            "",
        ]
    )
    README_PATH.write_text(text, encoding="utf-8")


def main() -> int:
    plan_rows = _load_plan_rows()
    non_hier_rows, hier_rows = _load_actual_status_rows()

    successful_rows: list[dict[str, str]] = []
    missing_rows: list[dict[str, str]] = []

    for idx in _successful_indices(non_hier_rows, hier_rows):
        plan_row = plan_rows[idx]
        summary_src = _summary_path_for_index(idx, non_hier_rows, hier_rows)
        if summary_src is None or not summary_src.exists():
            missing_rows.append(
                {
                    "index": str(idx),
                    "label": plan_row["label"],
                    "reason": "successful row has no summary JSON in archive",
                    "details": "",
                }
            )
            continue

        payload = json.loads(summary_src.read_text(encoding="utf-8"))
        run_id = str(payload.get("run_id", "")).strip()
        run_dir = _wandb_run_dir(run_id) if run_id else None
        if run_dir is None:
            missing_rows.append(
                {
                    "index": str(idx),
                    "label": plan_row["label"],
                    "reason": "successful row has no matching archived W&B run folder",
                    "details": run_id,
                }
            )
            continue

        bundle_dir = FINAL_SUCCESSFUL_RUN_BUNDLES_PATH / f"{idx:03d}_{_slugify(plan_row['label'])}"
        bundle_dir.mkdir(parents=True, exist_ok=True)

        files_dir = run_dir / "files"
        run_record_files = list(run_dir.glob("run-*.wandb"))
        vec_normalize_src = ARCHIVE_RUNS_ROOT / f"vec_normalize_{run_id}.pkl"
        hierarchical_report_src = ARCHIVE_RUNS_ROOT / "thesis_reports" / f"hierarchical_{run_id}"

        move_status = _optional_move(
            [
                ("summary_json_status", summary_src, bundle_dir / "summary" / summary_src.name),
                ("config_status", files_dir / "config.yaml", bundle_dir / "wandb" / "config.yaml"),
                ("wandb_summary_status", files_dir / "wandb-summary.json", bundle_dir / "wandb" / "wandb-summary.json"),
                ("wandb_metadata_status", files_dir / "wandb-metadata.json", bundle_dir / "wandb" / "wandb-metadata.json"),
                ("requirements_status", files_dir / "requirements.txt", bundle_dir / "wandb" / "requirements.txt"),
                ("diff_patch_status", files_dir / "diff.patch", bundle_dir / "wandb" / "diff.patch"),
                ("output_log_status", files_dir / "output.log", bundle_dir / "wandb" / "output.log"),
                ("model_zip_status", files_dir / "model.zip", bundle_dir / "models" / "model.zip"),
                ("models_dir_status", files_dir / "models", bundle_dir / "models" / "checkpoints"),
                ("vec_normalize_status", vec_normalize_src, bundle_dir / "runtime" / vec_normalize_src.name),
                ("hierarchical_report_status", hierarchical_report_src, bundle_dir / "reports" / hierarchical_report_src.name),
            ]
        )

        run_record_status = "missing"
        if run_record_files:
            run_record_status = _move_path(run_record_files[0], bundle_dir / "wandb" / run_record_files[0].name)

        notes: list[str] = []
        if plan_row["method"] == "BASELINE":
            notes.append("baseline_only_run_no_model_expected")
        if payload.get("domain") == "crop_planning":
            notes.append("crop_planning_run_has_no_vec_normalize_artifact")
        if payload.get("hierarchical") is True:
            notes.append("hierarchical_run_includes_report_bundle_when_available")

        metadata = {
            "index": idx,
            "label": plan_row["label"],
            "domain": payload.get("domain", plan_row["domain"]),
            "method": payload.get("method", plan_row["method"]),
            "run_id": run_id,
            "bundle_dir": str(bundle_dir),
            "notes": notes,
            "move_status": {**move_status, "run_record_status": run_record_status},
        }
        (bundle_dir / "bundle_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        successful_rows.append(
            {
                "index": str(idx),
                "label": plan_row["label"],
                "domain": str(payload.get("domain", plan_row["domain"])),
                "method": str(payload.get("method", plan_row["method"])),
                "run_id": run_id,
                "bundle_dir": str(bundle_dir.relative_to(FINAL_SUCCESSFUL_RUNS_PATH.parent)),
                "summary_json_status": move_status["summary_json_status"],
                "config_status": move_status["config_status"],
                "wandb_summary_status": move_status["wandb_summary_status"],
                "wandb_metadata_status": move_status["wandb_metadata_status"],
                "requirements_status": move_status["requirements_status"],
                "diff_patch_status": move_status["diff_patch_status"],
                "output_log_status": move_status["output_log_status"],
                "run_record_status": run_record_status,
                "model_zip_status": move_status["model_zip_status"],
                "models_dir_status": move_status["models_dir_status"],
                "vec_normalize_status": move_status["vec_normalize_status"],
                "hierarchical_report_status": move_status["hierarchical_report_status"],
                "notes": ";".join(notes),
            }
        )

    for idx in _missing_indices(non_hier_rows, hier_rows):
        plan_row = plan_rows[idx]
        actual_row = non_hier_rows.get(idx) or hier_rows.get(idx) or {}
        missing_rows.append(
            {
                "index": str(idx),
                "label": plan_row["label"],
                "reason": "planned matrix row failed in actual completion summary",
                "details": f"status={actual_row.get('status', '')}; exit_code={actual_row.get('exit_code', '')}",
            }
        )

    successful_rows.sort(key=lambda row: int(row["index"]))
    missing_rows.sort(key=lambda row: int(row["index"]))

    _write_csv(
        MANIFEST_PATH,
        successful_rows,
        [
            "index",
            "label",
            "domain",
            "method",
            "run_id",
            "bundle_dir",
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
            "notes",
        ],
    )
    _write_csv(
        MISSING_PATH,
        missing_rows,
        ["index", "label", "reason", "details"],
    )
    _write_readme(successful_rows, missing_rows)

    print(f"Promoted successful bundles: {len(successful_rows)}")
    print(f"Left out planned rows: {len(missing_rows)}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Missing: {MISSING_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
