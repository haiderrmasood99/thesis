#!/usr/bin/env python3
"""Shared helpers for low-hanging ablation launchers."""

from __future__ import annotations

import csv
import json
import os
import shlex
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class AblationCase:
    case_id: str
    label: str
    cmd: list[str]
    summary_json: Path
    case_log: Path
    thesis_report_dir: Optional[Path] = None
    metadata: dict[str, Any] = field(default_factory=dict)


def timestamp_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def slugify(value: str) -> str:
    cleaned = []
    for ch in str(value):
        if ch.isalnum():
            cleaned.append(ch.lower())
        elif ch in {"_", "-", "."}:
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned).strip("_")


def parse_int_list(value: str) -> list[int]:
    out: list[int] = []
    for token in value.split(","):
        token = token.strip()
        if token:
            out.append(int(token))
    if not out:
        raise ValueError(f"Expected comma-separated integers, got: {value!r}")
    return out


def parse_float_list(value: str) -> list[float]:
    out: list[float] = []
    for token in value.split(","):
        token = token.strip()
        if token:
            out.append(float(token))
    if not out:
        raise ValueError(f"Expected comma-separated floats, got: {value!r}")
    return out


def parse_method_list(value: str, allowed: set[str]) -> list[str]:
    methods: list[str] = []
    for token in value.split(","):
        token = token.strip().upper()
        if not token:
            continue
        if token not in allowed:
            raise ValueError(f"Unsupported method: {token}. Allowed: {sorted(allowed)}")
        methods.append(token)
    if not methods:
        raise ValueError(f"Expected at least one method, got: {value!r}")
    return methods


def parse_weather_modes(value: str) -> list[bool]:
    out: list[bool] = []
    for token in value.split(","):
        token = token.strip().lower()
        if not token:
            continue
        if token in {"fixed", "fixed_weather", "true", "1"}:
            out.append(True)
            continue
        if token in {"random", "random_weather", "false", "0"}:
            out.append(False)
            continue
        raise ValueError(f"Unsupported weather mode token: {token!r}")
    if not out:
        raise ValueError(f"Expected at least one weather mode, got: {value!r}")
    return out


def make_run_env(
    wandb_project: str,
    wandb_entity: str = "",
    wandb_offline: bool = False,
) -> dict[str, str]:
    env = dict(os.environ)
    env["WANDB_PROJECT"] = wandb_project
    env["WANDB_PROJECT_FERTILIZATION"] = wandb_project
    env["WANDB_PROJECT_CROP_PLANNING"] = wandb_project
    if wandb_entity:
        env["WANDB_ENTITY"] = wandb_entity
    if wandb_offline:
        env["WANDB_MODE"] = "offline"

    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("NUMEXPR_NUM_THREADS", "1")
    env.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    return env


def _safe_float(payload: dict[str, Any], key: str) -> Optional[float]:
    if key not in payload:
        return None
    value = payload.get(key)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_summary_metrics(summary_json_path: Path) -> dict[str, Any]:
    if not summary_json_path.exists():
        return {}
    try:
        payload = json.loads(summary_json_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
    return {
        "deterministic_return": _safe_float(metrics, "deterministic_return"),
        "stochastic_return_mean": _safe_float(metrics, "stochastic_return_mean"),
        "stochastic_return_std": _safe_float(metrics, "stochastic_return_std"),
        "pak_holdout_return": _safe_float(metrics, "pak_holdout_return"),
        "baseline_best_return": _safe_float(metrics, "baseline_best_return"),
        "uplift_vs_best_baseline_det": _safe_float(metrics, "uplift_vs_best_baseline_det"),
        "eval_det_mean_reward": _safe_float(metrics, "eval_det/mean_reward"),
        "eval_sto_mean_reward": _safe_float(metrics, "eval_sto/mean_reward"),
    }


def _run_case(
    repo_root: Path,
    case: AblationCase,
    run_env: dict[str, str],
    dry_run: bool,
) -> dict[str, Any]:
    case.summary_json.parent.mkdir(parents=True, exist_ok=True)
    case.case_log.parent.mkdir(parents=True, exist_ok=True)
    if case.thesis_report_dir is not None:
        case.thesis_report_dir.mkdir(parents=True, exist_ok=True)

    cmd_str = " ".join(shlex.quote(token) for token in case.cmd)
    base_row: dict[str, Any] = {
        "case_id": case.case_id,
        "label": case.label,
        "summary_json": str(case.summary_json),
        "thesis_report_dir": str(case.thesis_report_dir) if case.thesis_report_dir else "",
        "case_log": str(case.case_log),
        "command": cmd_str,
        **case.metadata,
    }

    if dry_run:
        return {
            **base_row,
            "status": "DRY_RUN",
            "exit_code": 0,
            "elapsed_seconds": 0.0,
        }

    start = time.time()
    with case.case_log.open("w", encoding="utf-8") as log_fh:
        log_fh.write(f"$ {cmd_str}\n\n")
        log_fh.flush()
        completed = subprocess.run(
            case.cmd,
            cwd=repo_root,
            env=run_env,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
        )
    elapsed = time.time() - start

    row: dict[str, Any] = {
        **base_row,
        "status": "OK" if completed.returncode == 0 else "FAILED",
        "exit_code": int(completed.returncode),
        "elapsed_seconds": round(elapsed, 3),
    }
    row.update(read_summary_metrics(case.summary_json))
    return row


def write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    base_fields = [
        "status",
        "exit_code",
        "elapsed_seconds",
        "case_id",
        "label",
        "summary_json",
        "thesis_report_dir",
        "case_log",
        "deterministic_return",
        "stochastic_return_mean",
        "stochastic_return_std",
        "pak_holdout_return",
        "baseline_best_return",
        "uplift_vs_best_baseline_det",
        "eval_det_mean_reward",
        "eval_sto_mean_reward",
        "command",
    ]
    discovered = set()
    for row in rows:
        discovered.update(row.keys())
    extra_fields = sorted(k for k in discovered if k not in set(base_fields))
    fields = [*base_fields, *extra_fields]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_cases_parallel(
    repo_root: Path,
    cases: list[AblationCase],
    run_env: dict[str, str],
    max_workers: int,
    dry_run: bool,
    summary_csv: Path,
) -> int:
    if not cases:
        raise ValueError("No cases to run.")
    workers = max(1, min(int(max_workers), len(cases)))
    print(f"Running {len(cases)} cases with max_workers={workers}")

    rows: list[dict[str, Any]] = []
    if dry_run:
        for case in cases:
            row = _run_case(repo_root=repo_root, case=case, run_env=run_env, dry_run=True)
            rows.append(row)
            print(f"[DRY_RUN] {case.case_id} :: {case.label}")
        write_summary_csv(summary_csv, rows)
        return 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(_run_case, repo_root, case, run_env, False): case
            for case in cases
        }
        for future in as_completed(future_map):
            case = future_map[future]
            row = future.result()
            rows.append(row)
            print(
                f"[{row['status']}] {case.case_id} :: {case.label} "
                f"(exit={row['exit_code']}, elapsed_s={row['elapsed_seconds']})"
            )

    rows.sort(key=lambda r: str(r.get("case_id", "")))
    write_summary_csv(summary_csv, rows)
    failures = sum(1 for row in rows if row.get("status") != "OK")
    print(f"Summary CSV: {summary_csv}")
    print(f"Completed={len(rows)} Failed={failures}")
    return 1 if failures else 0

