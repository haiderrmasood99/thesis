#!/usr/bin/env python3
"""Run guarded hierarchical crop-planning reruns in parallel.

This launcher is intentionally separate from the completed March 2026 matrix.
Use it only for post-hoc hierarchical stabilization reruns.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExperimentCase:
    label: str
    method: str
    fixed_weather: bool
    seed: int
    cmd: list[str]
    summary_json: Path
    thesis_report_dir: Path
    case_log: Path


def parse_int_list(value: str) -> list[int]:
    out: list[int] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        out.append(int(token))
    if not out:
        raise ValueError(f"Expected a comma-separated int list, got: {value!r}")
    return out


def parse_method_list(value: str) -> list[str]:
    methods = []
    for token in value.split(","):
        token = token.strip().upper()
        if not token:
            continue
        if token not in {"PPO", "A2C", "DQN"}:
            raise ValueError(f"Unsupported method: {token}")
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
        if token in {"fixed", "fixed_weather", "true"}:
            out.append(True)
            continue
        if token in {"random", "random_weather", "false"}:
            out.append(False)
            continue
        raise ValueError(f"Unsupported weather mode: {token}")
    if not out:
        raise ValueError(f"Expected at least one weather mode, got: {value!r}")
    return out


def _read_summary_metrics(summary_json_path: Path) -> dict[str, str]:
    if not summary_json_path.exists():
        return {}
    try:
        payload = json.loads(summary_json_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
    baseline_best = metrics.get("baseline_best_return")
    return {
        "summary_json": str(summary_json_path),
        "deterministic_return": str(metrics.get("deterministic_return", "")),
        "stochastic_return_mean": str(metrics.get("stochastic_return_mean", "")),
        "stochastic_return_std": str(metrics.get("stochastic_return_std", "")),
        "baseline_best_return": str(baseline_best if baseline_best is not None else ""),
        "uplift_vs_best_baseline_det": str(metrics.get("uplift_vs_best_baseline_det", "")),
        "pak_holdout_return": str(metrics.get("pak_holdout_return", "")),
    }


def _write_summary_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "status",
        "exit_code",
        "elapsed_seconds",
        "label",
        "method",
        "fixed_weather",
        "seed",
        "summary_json",
        "thesis_report_dir",
        "case_log",
        "deterministic_return",
        "stochastic_return_mean",
        "stochastic_return_std",
        "baseline_best_return",
        "uplift_vs_best_baseline_det",
        "pak_holdout_return",
        "command",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _build_run_env(args: argparse.Namespace) -> dict[str, str]:
    env = dict(os.environ)
    env["WANDB_PROJECT"] = args.wandb_project
    env["WANDB_PROJECT_CROP_PLANNING"] = args.wandb_project
    if args.wandb_entity:
        env["WANDB_ENTITY"] = args.wandb_entity
    if args.wandb_offline:
        env["WANDB_MODE"] = "offline"

    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("NUMEXPR_NUM_THREADS", "1")
    env.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    return env


def _build_case(
    repo_root: Path,
    py_exec: str,
    args: argparse.Namespace,
    method: str,
    fixed_weather: bool,
    seed: int,
) -> ExperimentCase:
    weather_label = "fixed_weather" if fixed_weather else "random_weather"
    slug = f"{method.lower()}_{'fixed' if fixed_weather else 'random'}_seed{seed}"

    summary_json = repo_root / args.summary_json_dir / f"{slug}.json"
    thesis_report_dir = repo_root / args.thesis_report_dir_root / slug
    case_log = repo_root / args.case_log_dir / f"{slug}.log"

    cmd = [
        py_exec,
        "experiments/crop_planning/train.py",
        "--method",
        method,
        "--fixed_weather",
        str(fixed_weather),
        "--hierarchical",
        "True",
        "--non_adaptive",
        "False",
        "--use_pakistan_crop_calendar",
        "True",
        "--price_profile",
        args.price_profile,
        "--enforce_calendar_windows",
        "True" if args.enforce_calendar_windows else "False",
        "--limit_fertilizer_to_season",
        "True" if args.limit_fertilizer_to_season else "False",
        "--preplant_fertilizer_days",
        str(args.preplant_fertilizer_days),
        "--postplant_fertilizer_days",
        str(args.postplant_fertilizer_days),
        "--annual_n_budget",
        str(args.annual_n_budget),
        "--annual_p_budget",
        str(args.annual_p_budget),
        "--annual_k_budget",
        str(args.annual_k_budget),
        "--enable-thesis-reporting",
        "True",
        "--thesis-report-dir",
        str(thesis_report_dir),
        "--summary-json",
        str(summary_json),
        "--seed",
        str(seed),
    ]
    if args.without_tracking:
        cmd.append("--without-tracking")

    label = f"Hierarchical rerun | {method} | {weather_label} | seed={seed}"
    return ExperimentCase(
        label=label,
        method=method,
        fixed_weather=fixed_weather,
        seed=seed,
        cmd=cmd,
        summary_json=summary_json,
        thesis_report_dir=thesis_report_dir,
        case_log=case_log,
    )


def _run_case(repo_root: Path, run_env: dict[str, str], case: ExperimentCase) -> dict[str, str]:
    case.case_log.parent.mkdir(parents=True, exist_ok=True)
    case.summary_json.parent.mkdir(parents=True, exist_ok=True)
    case.thesis_report_dir.parent.mkdir(parents=True, exist_ok=True)

    cmd_str = " ".join(shlex.quote(token) for token in case.cmd)
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

    row = {
        "status": "OK" if completed.returncode == 0 else "FAILED",
        "exit_code": str(completed.returncode),
        "elapsed_seconds": f"{elapsed:.3f}",
        "label": case.label,
        "method": case.method,
        "fixed_weather": str(case.fixed_weather),
        "seed": str(case.seed),
        "summary_json": str(case.summary_json),
        "thesis_report_dir": str(case.thesis_report_dir),
        "case_log": str(case.case_log),
        "deterministic_return": "",
        "stochastic_return_mean": "",
        "stochastic_return_std": "",
        "baseline_best_return": "",
        "uplift_vs_best_baseline_det": "",
        "pak_holdout_return": "",
        "command": cmd_str,
    }
    row.update(_read_summary_metrics(case.summary_json))
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Run guarded hierarchical reruns in parallel.")
    parser.add_argument("--methods", default="PPO,A2C", help="Comma-separated methods, e.g. PPO,A2C")
    parser.add_argument("--seeds", default="0,1,2", help="Comma-separated seeds")
    parser.add_argument(
        "--weather-modes",
        default="fixed,random",
        help="Comma-separated weather modes: fixed,random",
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=4,
        help="Parallel workers. Use 0 to launch all selected runs at once.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands only.")
    parser.add_argument("--price-profile", default="pakistan_baseline", help="Hierarchical price profile")
    parser.add_argument(
        "--enforce-calendar-windows",
        dest="enforce_calendar_windows",
        action="store_true",
        default=True,
        help="Sanitize crop choices to crops with defined calendar windows",
    )
    parser.add_argument(
        "--no-enforce-calendar-windows",
        dest="enforce_calendar_windows",
        action="store_false",
        help="Disable crop-window sanitization",
    )
    parser.add_argument(
        "--limit-fertilizer-to-season",
        dest="limit_fertilizer_to_season",
        action="store_true",
        default=True,
        help="Block fertilizer outside the active crop-season window",
    )
    parser.add_argument(
        "--no-limit-fertilizer-to-season",
        dest="limit_fertilizer_to_season",
        action="store_false",
        help="Disable crop-season fertilizer gating",
    )
    parser.add_argument("--preplant-fertilizer-days", type=int, default=14)
    parser.add_argument("--postplant-fertilizer-days", type=int, default=120)
    parser.add_argument("--annual-n-budget", type=float, default=150.0)
    parser.add_argument("--annual-p-budget", type=float, default=80.0)
    parser.add_argument("--annual-k-budget", type=float, default=60.0)
    parser.add_argument(
        "--wandb-project",
        default="Thesis-Final-Hierarchical-Rerun",
        help="W&B project for these reruns",
    )
    parser.add_argument("--wandb-entity", default="", help="Optional W&B entity override")
    parser.add_argument("--wandb-offline", action="store_true", help="Set WANDB_MODE=offline")
    parser.add_argument(
        "--without-tracking",
        action="store_true",
        default=False,
        help="Disable W&B tracking and use the local no-op tracker in the train script",
    )
    parser.add_argument(
        "--summary-csv",
        default="runs/experiment_summaries/hierarchical_guarded_parallel_summary.csv",
        help="Aggregated CSV summary for this rerun batch",
    )
    parser.add_argument(
        "--summary-json-dir",
        default="runs/experiment_summaries/hierarchical_guarded_metrics",
        help="Per-run summary JSON directory",
    )
    parser.add_argument(
        "--case-log-dir",
        default="runs/experiment_summaries/hierarchical_guarded_case_logs",
        help="Per-run stdout/stderr log directory",
    )
    parser.add_argument(
        "--thesis-report-dir-root",
        default="runs/thesis_reports/hierarchical_guarded_reruns",
        help="Root directory for per-run hierarchical thesis-report artifacts",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    py_exec = sys.executable
    run_env = _build_run_env(args)

    methods = parse_method_list(args.methods)
    seeds = parse_int_list(args.seeds)
    weather_modes = parse_weather_modes(args.weather_modes)

    cases: list[ExperimentCase] = []
    for method in methods:
        for fixed_weather in weather_modes:
            for seed in seeds:
                cases.append(
                    _build_case(
                        repo_root=repo_root,
                        py_exec=py_exec,
                        args=args,
                        method=method,
                        fixed_weather=fixed_weather,
                        seed=seed,
                    )
                )

    if not cases:
        summary_path = repo_root / args.summary_csv
        _write_summary_csv(summary_path, [])
        print(f"No cases selected. Empty summary written to: {summary_path}")
        return 0

    max_workers = args.max_parallel if args.max_parallel > 0 else len(cases)
    max_workers = max(1, min(max_workers, len(cases)))

    print("=== Hierarchical guarded parallel plan ===")
    print(f"Selected runs: {len(cases)}")
    print(f"Methods: {', '.join(methods)}")
    print(f"Seeds: {', '.join(str(seed) for seed in seeds)}")
    print(
        "Weather modes: "
        + ", ".join("fixed_weather" if mode else "random_weather" for mode in weather_modes)
    )
    print(f"Parallel workers: {max_workers}")
    print(f"W&B project: {args.wandb_project}")

    if args.dry_run:
        rows: list[dict[str, str]] = []
        for case in cases:
            cmd_str = " ".join(shlex.quote(token) for token in case.cmd)
            print(f"[DRY_RUN] {case.label}")
            print(f"$ {cmd_str}\n")
            rows.append(
                {
                    "status": "DRY_RUN",
                    "exit_code": "0",
                    "elapsed_seconds": "0.0",
                    "label": case.label,
                    "method": case.method,
                    "fixed_weather": str(case.fixed_weather),
                    "seed": str(case.seed),
                    "summary_json": str(case.summary_json),
                    "thesis_report_dir": str(case.thesis_report_dir),
                    "case_log": str(case.case_log),
                    "deterministic_return": "",
                    "stochastic_return_mean": "",
                    "stochastic_return_std": "",
                    "baseline_best_return": "",
                    "uplift_vs_best_baseline_det": "",
                    "pak_holdout_return": "",
                    "command": cmd_str,
                }
            )
        summary_path = repo_root / args.summary_csv
        _write_summary_csv(summary_path, rows)
        print(f"Dry-run summary CSV written to: {summary_path}")
        return 0

    results: list[dict[str, str]] = []
    failed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {pool.submit(_run_case, repo_root, run_env, case): case for case in cases}
        completed_count = 0
        for future in as_completed(future_map):
            row = future.result()
            completed_count += 1
            results.append(row)
            if row["status"] != "OK":
                failed += 1
            print(
                f"[{row['status']}] {completed_count}/{len(cases)} | "
                f"{row['label']} | {float(row['elapsed_seconds']):.1f}s"
            )

    results.sort(key=lambda row: (row["method"], row["fixed_weather"], int(row["seed"])))
    summary_path = repo_root / args.summary_csv
    _write_summary_csv(summary_path, results)

    print(f"\nSummary CSV written to: {summary_path}")
    print(f"Case logs: {repo_root / args.case_log_dir}")
    print(f"Thesis reports: {repo_root / args.thesis_report_dir_root}")

    if failed:
        print(f"Completed with failures: {failed}/{len(results)} runs failed.")
        return 1

    print(f"All {len(results)} hierarchical reruns completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
