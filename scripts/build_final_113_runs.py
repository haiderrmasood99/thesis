#!/usr/bin/env python3
"""Assemble the corrected final 113-run bundle set.

This script builds a frozen bundle set under
`artifacts/final_successful_runs/final_113/` by:

- copying the already-curated non-replaced bundles from
  `artifacts/final_successful_runs/bundles/`
- replacing the 12 hierarchical slots with the downloaded reruns from
  `Recovered/wandb_full_backup/Thesis-Final-Hierarchical-Rerun/`
- filling the 4 failed DQN matrix slots with the successful reruns from
  `Recovered/wandb_full_backup/Thesis-Final/`
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
    ARTIFACTS_PATH,
    FINAL_113_BUNDLES_PATH,
    FINAL_113_RUNS_PATH,
    FINAL_SUCCESSFUL_RUNS_PATH,
    LOCAL_ARCHIVE_PATH,
)


PLAN_SUMMARY = (
    LOCAL_ARCHIVE_PATH / "runs" / "experiment_summaries" / "run_experiments_7_3_2026_summary.csv"
)
CURRENT_MANIFEST = FINAL_SUCCESSFUL_RUNS_PATH / "manifest.csv"
RECOVERED_ROOT = FINAL_SUCCESSFUL_RUNS_PATH / "Recovered"
RECOVERED_BACKUP_ROOT = RECOVERED_ROOT / "wandb_full_backup"
THESIS_FINAL_RECOVERED_ROOT = RECOVERED_BACKUP_ROOT / "Thesis-Final"
HIERARCHICAL_RERUN_ROOT = RECOVERED_BACKUP_ROOT / "Thesis-Final-Hierarchical-Rerun"
FINAL_MANIFEST = FINAL_113_RUNS_PATH / "manifest.csv"
FINAL_REPLACEMENTS = FINAL_113_RUNS_PATH / "replacement_map.csv"
FINAL_README = FINAL_113_RUNS_PATH / "README.md"

HIERARCHICAL_BY_SUMMARY = {
    "ppo_fixed_seed0.json": 75,
    "ppo_random_seed0.json": 78,
    "ppo_fixed_seed1.json": 81,
    "ppo_random_seed1.json": 84,
    "ppo_fixed_seed2.json": 87,
    "ppo_random_seed2.json": 90,
    "a2c_fixed_seed0.json": 93,
    "a2c_random_seed0.json": 96,
    "a2c_fixed_seed1.json": 99,
    "a2c_random_seed1.json": 102,
    "a2c_fixed_seed2.json": 105,
    "a2c_random_seed2.json": 108,
}

DQN_BY_SUMMARY = {
    "fertilization_zk7g2z05.json": 109,
    "fertilization_vfgm40w7.json": 110,
    "crop_planning_mn4hg3h6.json": 111,
    "crop_planning_s6td3gfc.json": 112,
}

REPLACED_INDICES = set(HIERARCHICAL_BY_SUMMARY.values()) | set(DQN_BY_SUMMARY.values())

MANIFEST_FIELDS = [
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
    "source_kind",
    "source_project",
    "source_run_name",
    "source_created",
    "notes",
]

REPLACEMENT_FIELDS = [
    "index",
    "label",
    "source_kind",
    "source_project",
    "previous_run_id",
    "new_run_id",
    "new_run_name",
    "reason",
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
    rel = Path("final_successful_runs") / "final_113" / "bundles" / dst_bundle_dir.name
    return str(rel)


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


def _boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _coerce_number(value: object) -> object:
    if isinstance(value, (int, float)) or value is None:
        return value
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return value
        try:
            if "." in text:
                return float(text)
            return int(text)
        except ValueError:
            return value
    return value


def _basename(path_value: str) -> str:
    if not path_value:
        return ""
    normalized = str(path_value).replace("\\", "/")
    return normalized.rsplit("/", 1)[-1]


def _notes_text(notes: list[str]) -> str:
    filtered = [note for note in notes if note]
    return ";".join(filtered)


def _load_plan_rows() -> dict[int, dict[str, str]]:
    return {int(row["index"]): row for row in _read_csv(PLAN_SUMMARY)}


def _load_current_manifest_rows() -> dict[int, dict[str, str]]:
    return {int(row["index"]): row for row in _read_csv(CURRENT_MANIFEST)}


def _load_recovered_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(RECOVERED_ROOT.glob("wandb_export*.csv")):
        rows.extend(_read_csv(path))
    return rows


def _collect_recovered_replacements(
    recovered_rows: list[dict[str, str]],
) -> tuple[dict[int, dict[str, str]], dict[int, dict[str, str]]]:
    hierarchical_rows: dict[int, dict[str, str]] = {}
    dqn_rows: dict[int, dict[str, str]] = {}

    for row in recovered_rows:
        state = str(row.get("State", "")).strip().lower()
        if state != "finished":
            continue

        summary_name = _basename(row.get("summary_json_path", ""))
        if summary_name in HIERARCHICAL_BY_SUMMARY:
            hierarchical_rows[HIERARCHICAL_BY_SUMMARY[summary_name]] = row
        if summary_name in DQN_BY_SUMMARY:
            dqn_rows[DQN_BY_SUMMARY[summary_name]] = row

    missing_hier = sorted(set(HIERARCHICAL_BY_SUMMARY.values()) - set(hierarchical_rows))
    missing_dqn = sorted(set(DQN_BY_SUMMARY.values()) - set(dqn_rows))
    if missing_hier or missing_dqn:
        raise RuntimeError(
            f"Recovered backup is incomplete. Missing hierarchical={missing_hier}, missing_dqn={missing_dqn}"
        )

    return hierarchical_rows, dqn_rows


def _recovered_wandb_id(recovered_row: dict[str, str]) -> str:
    tensorboard_log = str(recovered_row.get("tensorboard_log", "")).replace("\\", "/")
    match = re.search(r"run-[^/]+-([a-z0-9]+)(?:/files)?$", tensorboard_log)
    if match:
        return match.group(1)
    raw_run_id = str(recovered_row.get("run_id", "")).strip()
    if raw_run_id and raw_run_id != "0":
        return raw_run_id
    return ""


def _find_recovered_run_dir(project_root: Path, recovered_row: dict[str, str]) -> Path:
    candidates: list[Path] = []
    wandb_id = _recovered_wandb_id(recovered_row)
    run_name = str(recovered_row.get("Name", "")).strip()

    if wandb_id:
        candidates.extend(sorted(project_root.glob(f"{wandb_id}__*")))
    if run_name:
        candidates.extend(sorted(project_root.glob(f"*__{run_name}")))

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        if path not in seen:
            deduped.append(path)
            seen.add(path)

    if len(deduped) != 1:
        raise RuntimeError(
            "Expected exactly one recovered folder for "
            f"wandb_id={wandb_id!r}, run_name={run_name!r} under {project_root}"
        )
    return deduped[0]


def _find_named_file(root: Path, filename: str) -> Path | None:
    if not filename:
        return None
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    return matches[0] if matches else None


def _find_named_dir(root: Path, dirname: str) -> Path | None:
    if not dirname:
        return None
    matches = sorted(path for path in root.rglob(dirname) if path.is_dir())
    return matches[0] if matches else None


def _copy_best_models(run_dir: Path, dst_bundle_dir: Path) -> str:
    best_models = sorted(run_dir.rglob("best_model.zip"))
    if not best_models:
        return "missing"

    checkpoints_root = dst_bundle_dir / "models" / "checkpoints"
    for best_model in best_models:
        rel_parts = best_model.relative_to(run_dir).parts
        target = checkpoints_root.joinpath(*rel_parts[-3:])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best_model, target)
    return "copied"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _generated_summary_payload(
    plan_row: dict[str, str],
    recovered_row: dict[str, str],
    config_payload: dict[str, object],
    summary_payload: dict[str, object],
) -> dict[str, object]:
    domain = plan_row["domain"]
    method = str(config_payload.get("method") or config_payload.get("algo") or plan_row["method"])
    run_id = _recovered_wandb_id(recovered_row)
    payload: dict[str, object] = {
        "timestamp": recovered_row.get("Created", ""),
        "run_id": run_id,
        "domain": domain,
        "method": method,
        "seed": _coerce_number(config_payload.get("seed", recovered_row.get("seed", ""))),
        "fixed_weather": _boolish(config_payload.get("fixed_weather", False)),
    }

    if domain == "fertilization":
        payload["nonadaptive"] = _boolish(config_payload.get("nonadaptive", False))
        payload["total_years"] = _coerce_number(config_payload.get("total_years", ""))
        payload["baseline"] = _boolish(config_payload.get("baseline", False))
        payload["nutrient_action_mode"] = config_payload.get("nutrient_action_mode", "")
        payload["price_profile"] = config_payload.get("price_profile", "")
    else:
        payload["non_adaptive"] = _boolish(config_payload.get("non_adaptive", False))
        payload["hierarchical"] = _boolish(config_payload.get("hierarchical", False))
        payload["price_profile"] = config_payload.get("price_profile", "")

    metrics: dict[str, object] = {}
    for key in (
        "deterministic_return",
        "stochastic_return_mean",
        "stochastic_return_std",
        "baseline_returns",
        "baseline_best_return",
        "uplift_vs_best_baseline_det",
        "pak_holdout_return",
    ):
        if key in summary_payload:
            metrics[key] = summary_payload[key]
    payload["metrics"] = metrics
    return payload


def _copy_recovered_export_metadata(run_dir: Path, dst_bundle_dir: Path) -> None:
    export_root = dst_bundle_dir / "recovered_export"
    for filename in ("config.json", "rawconfig.json", "metadata.json", "summary.json", "run_core.json"):
        src = run_dir / filename
        if src.exists():
            export_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, export_root / filename)


def _write_bundle_metadata(
    dst_bundle_dir: Path,
    *,
    index: int,
    label: str,
    domain: str,
    method: str,
    run_id: str,
    source_kind: str,
    source_project: str,
    source_run_name: str,
    notes: list[str],
) -> None:
    payload = {
        "index": index,
        "label": label,
        "domain": domain,
        "method": method,
        "run_id": run_id,
        "bundle_dir": str(dst_bundle_dir),
        "source_kind": source_kind,
        "source_project": source_project,
        "source_run_name": source_run_name,
        "notes": notes,
    }
    (dst_bundle_dir / "bundle_metadata.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_existing_bundle(
    idx: int,
    plan_row: dict[str, str],
    current_row: dict[str, str],
) -> dict[str, str]:
    src_bundle_dir = ARTIFACTS_PATH / Path(current_row["bundle_dir"])
    dst_bundle_dir = FINAL_113_BUNDLES_PATH / f"{idx:03d}_{_slugify(plan_row['label'])}"
    shutil.copytree(src_bundle_dir, dst_bundle_dir)

    method = plan_row["method"] if idx == 113 else current_row["method"]
    notes = [current_row.get("notes", "")]
    if idx == 113 and "baseline_only_run_no_model_expected" not in notes[0]:
        notes.append("baseline_only_run_no_model_expected")

    _write_bundle_metadata(
        dst_bundle_dir,
        index=idx,
        label=plan_row["label"],
        domain=plan_row["domain"],
        method=method,
        run_id=current_row["run_id"],
        source_kind="existing_curated_bundle",
        source_project="artifacts/final_successful_runs/bundles",
        source_run_name="",
        notes=[note for note in notes if note],
    )

    row = dict(current_row)
    row["label"] = plan_row["label"]
    row["domain"] = plan_row["domain"]
    row["method"] = method
    row["bundle_dir"] = _bundle_dir_rel(dst_bundle_dir)
    row["source_kind"] = "existing_curated_bundle"
    row["source_project"] = "artifacts/final_successful_runs/bundles"
    row["source_run_name"] = ""
    row["source_created"] = ""
    row["notes"] = _notes_text([current_row.get("notes", "")])
    return row


def _build_recovered_bundle(
    idx: int,
    plan_row: dict[str, str],
    recovered_row: dict[str, str],
    *,
    project_root: Path,
    source_kind: str,
    source_project: str,
) -> dict[str, str]:
    run_id = _recovered_wandb_id(recovered_row)
    run_name = str(recovered_row.get("Name", ""))
    run_dir = _find_recovered_run_dir(project_root, recovered_row)
    dst_bundle_dir = FINAL_113_BUNDLES_PATH / f"{idx:03d}_{_slugify(plan_row['label'])}"
    dst_bundle_dir.mkdir(parents=True, exist_ok=True)

    config_payload = _load_json(run_dir / "config.json")
    summary_payload = _load_json(run_dir / "summary.json")
    generated_summary = _generated_summary_payload(plan_row, recovered_row, config_payload, summary_payload)
    summary_filename = _basename(plan_row["summary_json"])
    summary_target = dst_bundle_dir / "summary" / summary_filename
    summary_target.parent.mkdir(parents=True, exist_ok=True)
    summary_target.write_text(json.dumps(generated_summary, indent=2), encoding="utf-8")

    run_files = run_dir / "run_files"
    statuses = {
        "summary_json_status": "generated",
        "config_status": _copy_file(run_files / "config.yaml", dst_bundle_dir / "wandb" / "config.yaml"),
        "wandb_summary_status": _copy_file(
            run_files / "wandb-summary.json",
            dst_bundle_dir / "wandb" / "wandb-summary.json",
        ),
        "wandb_metadata_status": _copy_file(
            run_files / "wandb-metadata.json",
            dst_bundle_dir / "wandb" / "wandb-metadata.json",
        ),
        "requirements_status": _copy_file(
            run_files / "requirements.txt",
            dst_bundle_dir / "wandb" / "requirements.txt",
        ),
        "diff_patch_status": _copy_file(run_files / "diff.patch", dst_bundle_dir / "wandb" / "diff.patch"),
        "output_log_status": _copy_file(run_files / "output.log", dst_bundle_dir / "wandb" / "output.log"),
        "model_zip_status": _copy_file(run_files / "model.zip", dst_bundle_dir / "models" / "model.zip"),
        "models_dir_status": _copy_best_models(run_dir, dst_bundle_dir),
        "vec_normalize_status": "missing",
        "hierarchical_report_status": "missing",
        "run_record_status": "missing",
    }

    run_record = next(run_dir.rglob("*.wandb"), None)
    if run_record is not None:
        statuses["run_record_status"] = _copy_file(run_record, dst_bundle_dir / "wandb" / run_record.name)
    elif (run_dir / "run_core.json").exists():
        _copy_file(run_dir / "run_core.json", dst_bundle_dir / "wandb" / "run_core.json")
        statuses["run_record_status"] = "copied_run_core_json"

    stats_name = _basename(str(config_payload.get("stats_path", "")))
    stats_src = _find_named_file(RECOVERED_ROOT, stats_name)
    if stats_src is not None:
        statuses["vec_normalize_status"] = _copy_file(stats_src, dst_bundle_dir / "runtime" / stats_src.name)

    report_dir_name = _basename(str(config_payload.get("thesis_report_dir", "")))
    report_src = _find_named_dir(RECOVERED_ROOT, report_dir_name)
    if report_src is not None:
        statuses["hierarchical_report_status"] = _copy_dir(report_src, dst_bundle_dir / "reports" / report_src.name)

    _copy_recovered_export_metadata(run_dir, dst_bundle_dir)

    notes = [
        "summary_json_reconstructed_from_recovered_export",
        "recovered_wandb_export_bundle",
    ]
    if statuses["models_dir_status"] == "missing":
        notes.append("recovered_backup_has_no_models_checkpoint_dir")
    if statuses["vec_normalize_status"] == "missing" and plan_row["domain"] == "fertilization":
        notes.append("vec_normalize_not_present_in_recovered_backup")
    if statuses["hierarchical_report_status"] == "missing" and idx in HIERARCHICAL_BY_SUMMARY.values():
        notes.append("hierarchical_report_dir_not_present_in_recovered_backup")

    method = plan_row["method"]
    _write_bundle_metadata(
        dst_bundle_dir,
        index=idx,
        label=plan_row["label"],
        domain=plan_row["domain"],
        method=method,
        run_id=run_id,
        source_kind=source_kind,
        source_project=source_project,
        source_run_name=run_name,
        notes=notes,
    )

    return {
        "index": str(idx),
        "label": plan_row["label"],
        "domain": plan_row["domain"],
        "method": method,
        "run_id": run_id,
        "bundle_dir": _bundle_dir_rel(dst_bundle_dir),
        "summary_json_status": statuses["summary_json_status"],
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
        "hierarchical_report_status": statuses["hierarchical_report_status"],
        "source_kind": source_kind,
        "source_project": source_project,
        "source_run_name": run_name,
        "source_created": recovered_row.get("Created", ""),
        "notes": _notes_text(notes),
    }


def _write_readme(
    manifest_rows: list[dict[str, str]],
    replacement_rows: list[dict[str, str]],
) -> None:
    bundle_count = len(manifest_rows)
    existing_count = sum(1 for row in manifest_rows if row["source_kind"] == "existing_curated_bundle")
    hier_count = sum(1 for row in manifest_rows if row["source_kind"] == "recovered_hierarchical_rerun")
    dqn_count = sum(1 for row in manifest_rows if row["source_kind"] == "recovered_dqn_rerun")
    model_count = sum(1 for row in manifest_rows if row["model_zip_status"] != "missing")
    vec_count = sum(1 for row in manifest_rows if row["vec_normalize_status"] != "missing")
    report_count = sum(1 for row in manifest_rows if row["hierarchical_report_status"] != "missing")
    models_dir_count = sum(1 for row in manifest_rows if row["models_dir_status"] != "missing")

    lines = [
        "# Final Correct 113 Runs",
        "",
        "This folder contains the corrected final-matrix bundle set assembled from the curated archive plus the downloaded recovered reruns.",
        "",
        f"- total bundles: `{bundle_count}`",
        f"- copied from existing curated bundles: `{existing_count}`",
        f"- hierarchical rerun replacements: `{hier_count}`",
        f"- DQN rerun replacements: `{dqn_count}`",
        f"- bundles with `model.zip`: `{model_count}`",
        f"- bundles with checkpoint directories beyond `model.zip`: `{models_dir_count}`",
        f"- bundles with `vec_normalize` state: `{vec_count}`",
        f"- bundles with hierarchical report directories: `{report_count}`",
        "",
        "## Layout",
        "",
        "- `bundles/`: one folder per final matrix row",
        "- `manifest.csv`: full inventory for the corrected 113 bundles",
        "- `replacement_map.csv`: which rows were swapped to recovered reruns",
        "",
        "## Notes",
        "",
        "- The recovered W&B export did not include the repo's original `runs/experiment_summaries/*.json` files for the reruns, so those summary JSON files were reconstructed from the recovered export metadata.",
        "- The recovered rerun exports currently include `model.zip` but not the old `models/.../best_model.zip` checkpoint directories.",
        "- The recovered fertilization DQN reruns do not currently include `vec_normalize_*.pkl` files in the downloaded backup.",
        "- The recovered hierarchical rerun project does not currently include the thesis report directories in the downloaded backup.",
        "- The baseline-only row remains included without a model checkpoint by design.",
        "",
        f"- replacement rows recorded: `{len(replacement_rows)}`",
        "",
    ]
    FINAL_README.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    plan_rows = _load_plan_rows()
    current_rows = _load_current_manifest_rows()
    recovered_rows = _load_recovered_rows()
    hierarchical_replacements, dqn_replacements = _collect_recovered_replacements(recovered_rows)

    if FINAL_113_RUNS_PATH.exists():
        shutil.rmtree(FINAL_113_RUNS_PATH)
    FINAL_113_BUNDLES_PATH.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, str]] = []
    replacement_rows: list[dict[str, str]] = []

    for idx in range(1, 114):
        plan_row = plan_rows[idx]

        if idx in HIERARCHICAL_BY_SUMMARY.values():
            prior_run_id = current_rows[idx]["run_id"]
            manifest_rows.append(
                _build_recovered_bundle(
                    idx,
                    plan_row,
                    hierarchical_replacements[idx],
                    project_root=HIERARCHICAL_RERUN_ROOT,
                    source_kind="recovered_hierarchical_rerun",
                    source_project="Recovered/wandb_full_backup/Thesis-Final-Hierarchical-Rerun",
                )
            )
            replacement_rows.append(
                {
                    "index": str(idx),
                    "label": plan_row["label"],
                    "source_kind": "recovered_hierarchical_rerun",
                    "source_project": "Recovered/wandb_full_backup/Thesis-Final-Hierarchical-Rerun",
                    "previous_run_id": prior_run_id,
                    "new_run_id": _recovered_wandb_id(hierarchical_replacements[idx]),
                    "new_run_name": hierarchical_replacements[idx].get("Name", ""),
                    "reason": "replace_older_hierarchical_bundle_with_recovered_hierarchical_rerun",
                }
            )
            continue

        if idx in DQN_BY_SUMMARY.values():
            manifest_rows.append(
                _build_recovered_bundle(
                    idx,
                    plan_row,
                    dqn_replacements[idx],
                    project_root=THESIS_FINAL_RECOVERED_ROOT,
                    source_kind="recovered_dqn_rerun",
                    source_project="Recovered/wandb_full_backup/Thesis-Final",
                )
            )
            replacement_rows.append(
                {
                    "index": str(idx),
                    "label": plan_row["label"],
                    "source_kind": "recovered_dqn_rerun",
                    "source_project": "Recovered/wandb_full_backup/Thesis-Final",
                    "previous_run_id": "",
                    "new_run_id": _recovered_wandb_id(dqn_replacements[idx]),
                    "new_run_name": dqn_replacements[idx].get("Name", ""),
                    "reason": "fill_failed_matrix_slot_with_successful_recovered_dqn_rerun",
                }
            )
            continue

        if idx not in current_rows:
            raise RuntimeError(f"Current curated manifest has no bundle for index={idx}")
        manifest_rows.append(_build_existing_bundle(idx, plan_row, current_rows[idx]))

    manifest_rows.sort(key=lambda row: int(row["index"]))
    replacement_rows.sort(key=lambda row: int(row["index"]))

    _write_csv(FINAL_MANIFEST, manifest_rows, MANIFEST_FIELDS)
    _write_csv(FINAL_REPLACEMENTS, replacement_rows, REPLACEMENT_FIELDS)
    _write_readme(manifest_rows, replacement_rows)

    print(f"Built corrected final bundles: {len(manifest_rows)}")
    print(
        "Replacements: "
        f"hierarchical={sum(1 for row in replacement_rows if row['source_kind'] == 'recovered_hierarchical_rerun')}, "
        f"dqn={sum(1 for row in replacement_rows if row['source_kind'] == 'recovered_dqn_rerun')}"
    )
    print(f"Output: {FINAL_113_RUNS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
