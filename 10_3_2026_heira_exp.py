#!/usr/bin/env python3
"""Run hierarchical experiments from the 7_3_2026 matrix, starting at index 75, in parallel.

This script reuses experiment definitions from run_experiments_7_3_2026.py,
filters to hierarchical cases with index >= start-index, and executes them in
parallel subprocesses.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import re
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from types import ModuleType


def _load_base_runner(repo_root: Path) -> ModuleType:
    path = repo_root / "run_experiments_7_3_2026.py"
    spec = importlib.util.spec_from_file_location("run_experiments_7_3_2026_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load base runner from: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _is_true(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _sanitize_filename(value: str, max_len: int = 120) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return cleaned[:max_len] if cleaned else "run"


def _write_summary_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "index",
        "status",
        "exit_code",
        "elapsed_seconds",
        "label",
        "domain",
        "method",
        "adaptive",
        "hierarchical",
        "fixed_weather",
        "seed",
        "budget",
        "summary_json",
        "case_log",
        "deterministic_return",
        "stochastic_return_mean",
        "stochastic_return_std",
        "baseline_best_return",
        "uplift_vs_best_baseline_det",
        "pak_holdout_return",
        "command",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start-index", type=int, default=75, help="Only run experiment index >= this value.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands only, do not execute.")

    parser.add_argument("--seeds", default="0,1,2", help="Comma-separated seeds for core runs.")
    parser.add_argument(
        "--fert-total-years",
        default="1000,3000,5000",
        help="Comma-separated fertilization training budgets (total-years).",
    )
    parser.add_argument("--fert-n-process", type=int, default=8, help="Parallel env count for fertilization.")
    parser.add_argument("--fert-eval-freq", type=int, default=20000, help="Eval frequency for fertilization.")
    parser.add_argument(
        "--fert-nutrient-action-mode",
        type=str.upper,
        choices=["N", "NPK"],
        default="NPK",
        help="Fertilization action mode for matrix runs.",
    )
    parser.add_argument("--fert-price-profile", default="pakistan_baseline", help="Economics profile for fert runs.")
    parser.add_argument("--fert-maxN", type=float, default=150.0, help="Max N kg/ha per action.")
    parser.add_argument("--fert-maxP", type=float, default=80.0, help="Max P kg/ha per action.")
    parser.add_argument("--fert-maxK", type=float, default=60.0, help="Max K kg/ha per action.")
    parser.add_argument("--fert-p-actions", type=int, default=11, help="Discrete bins for P channel.")
    parser.add_argument("--fert-k-actions", type=int, default=11, help="Discrete bins for K channel.")
    parser.add_argument("--fert-n-nh4-rate", type=float, default=0.75, help="Fraction of N mapped to NH4.")

    parser.add_argument("--hierarchical-price-profile", default="pakistan_baseline", help="Price profile for hierarchical runs.")

    parser.add_argument(
        "--include-dqn",
        dest="include_dqn",
        action="store_true",
        default=True,
        help="Include DQN ablation runs.",
    )
    parser.add_argument(
        "--no-dqn",
        dest="include_dqn",
        action="store_false",
        help="Exclude DQN ablation runs.",
    )
    parser.add_argument("--dqn-seed", type=int, default=0, help="Seed for DQN ablations.")
    parser.add_argument("--dqn-total-years", type=int, default=5000, help="Fertilization total-years for DQN.")

    parser.add_argument(
        "--include-baseline",
        dest="include_baseline",
        action="store_true",
        default=True,
        help="Include fertilization baseline run.",
    )
    parser.add_argument(
        "--no-baseline",
        dest="include_baseline",
        action="store_false",
        help="Exclude fertilization baseline run.",
    )

    parser.add_argument(
        "--wandb-project",
        default="Thesis-Final",
        help="W&B project used for all runs (default: Thesis-Final).",
    )
    parser.add_argument("--wandb-entity", default="", help="Optional W&B entity override.")
    parser.add_argument("--wandb-offline", action="store_true", help="Set WANDB_MODE=offline for all commands.")
    parser.add_argument(
        "--without-tracking",
        action="store_true",
        default=False,
        help="Pass --without-tracking to train scripts (no-op W&B in script).",
    )

    parser.add_argument(
        "--max-parallel",
        type=int,
        default=0,
        help="Max parallel jobs. 0 means run all selected hierarchical jobs at once.",
    )
    parser.add_argument(
        "--summary-csv",
        default="runs/experiment_summaries/10_3_2026_hier_parallel_summary.csv",
        help="CSV output path for run summary.",
    )
    parser.add_argument(
        "--summary-json-dir",
        default="runs/experiment_summaries/metrics_10_3_2026_hier_parallel",
        help="Directory where standardized summary JSON files are written.",
    )
    parser.add_argument(
        "--case-log-dir",
        default="runs/experiment_summaries/10_3_2026_hier_case_logs",
        help="Directory for per-experiment stdout/stderr logs.",
    )


def _run_case(
    base: ModuleType,
    repo_root: Path,
    run_env: dict[str, str],
    summary_json_dir: Path,
    case_log_dir: Path,
    idx: int,
    exp: object,
) -> dict[str, str]:
    seed_token = str(getattr(exp, "seed", "na")).replace("/", "_").replace(" ", "_")
    summary_json_path = summary_json_dir / (
        f"{idx:03d}_{getattr(exp, 'domain', 'exp')}_{str(getattr(exp, 'method', 'run')).lower()}_"
        f"seed{seed_token}_h{getattr(exp, 'hierarchical', 'False')}.json"
    )
    cmd = list(getattr(exp, "cmd"))
    if "--summary-json" not in cmd:
        cmd += ["--summary-json", str(summary_json_path)]

    cmd_str = " ".join(shlex.quote(c) for c in cmd)
    safe_label = _sanitize_filename(str(getattr(exp, "label", f"exp_{idx}")))
    case_log_path = case_log_dir / f"{idx:03d}_{safe_label}.log"

    start = time.time()
    with case_log_path.open("w", encoding="utf-8") as log_fh:
        log_fh.write(f"$ {cmd_str}\n\n")
        log_fh.flush()
        completed = subprocess.run(cmd, cwd=repo_root, env=run_env, stdout=log_fh, stderr=subprocess.STDOUT)
    elapsed = time.time() - start

    status = "OK" if completed.returncode == 0 else "FAILED"
    row = {
        "index": str(idx),
        "status": status,
        "exit_code": str(completed.returncode),
        "elapsed_seconds": f"{elapsed:.3f}",
        "label": str(getattr(exp, "label")),
        "domain": str(getattr(exp, "domain")),
        "method": str(getattr(exp, "method")),
        "adaptive": str(getattr(exp, "adaptive")),
        "hierarchical": str(getattr(exp, "hierarchical")),
        "fixed_weather": str(getattr(exp, "fixed_weather")),
        "seed": str(getattr(exp, "seed")),
        "budget": str(getattr(exp, "budget")),
        "summary_json": str(summary_json_path),
        "case_log": str(case_log_path),
        "deterministic_return": "",
        "stochastic_return_mean": "",
        "stochastic_return_std": "",
        "baseline_best_return": "",
        "uplift_vs_best_baseline_det": "",
        "pak_holdout_return": "",
        "command": cmd_str,
    }
    row.update(base._read_summary_metrics(summary_json_path))
    return row


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    base = _load_base_runner(repo_root)

    parser = argparse.ArgumentParser()
    _add_common_args(parser)
    args = parser.parse_args()

    seeds = base.parse_int_list(args.seeds)
    total_years_list = base.parse_int_list(args.fert_total_years)

    py_exec = sys.executable
    run_env = base._build_run_env(args)

    experiments: list[object] = []
    experiments.extend(
        base.build_fertilization_core(
            py_exec=py_exec,
            seeds=seeds,
            total_years_list=total_years_list,
            n_process=args.fert_n_process,
            eval_freq=args.fert_eval_freq,
            nutrient_action_mode=args.fert_nutrient_action_mode,
            price_profile=args.fert_price_profile,
            maxN=args.fert_maxN,
            maxP=args.fert_maxP,
            maxK=args.fert_maxK,
            p_actions=args.fert_p_actions,
            k_actions=args.fert_k_actions,
            n_nh4_rate=args.fert_n_nh4_rate,
            without_tracking=args.without_tracking,
        )
    )
    experiments.extend(
        base.build_crop_planning_core(
            py_exec=py_exec,
            seeds=seeds,
            include_hierarchical=True,
            hierarchical_price_profile=args.hierarchical_price_profile,
            without_tracking=args.without_tracking,
        )
    )
    if args.include_dqn:
        experiments.extend(
            base.build_dqn_ablations(
                py_exec=py_exec,
                dqn_seed=args.dqn_seed,
                dqn_total_years=args.dqn_total_years,
                n_process=args.fert_n_process,
                eval_freq=args.fert_eval_freq,
                nutrient_action_mode=args.fert_nutrient_action_mode,
                price_profile=args.fert_price_profile,
                maxN=args.fert_maxN,
                maxP=args.fert_maxP,
                maxK=args.fert_maxK,
                p_actions=args.fert_p_actions,
                k_actions=args.fert_k_actions,
                n_nh4_rate=args.fert_n_nh4_rate,
                without_tracking=args.without_tracking,
            )
        )
    if args.include_baseline:
        experiments.extend(
            base.build_baseline(
                py_exec=py_exec,
                nutrient_action_mode=args.fert_nutrient_action_mode,
                price_profile=args.fert_price_profile,
                maxN=args.fert_maxN,
                maxP=args.fert_maxP,
                maxK=args.fert_maxK,
                p_actions=args.fert_p_actions,
                k_actions=args.fert_k_actions,
                n_nh4_rate=args.fert_n_nh4_rate,
                without_tracking=args.without_tracking,
            )
        )

    selected: list[tuple[int, object]] = []
    for idx, exp in enumerate(experiments, start=1):
        if idx < args.start_index:
            continue
        if not _is_true(getattr(exp, "hierarchical", "False")):
            continue
        selected.append((idx, exp))

    summary_json_dir = Path(args.summary_json_dir)
    summary_json_dir.mkdir(parents=True, exist_ok=True)
    case_log_dir = Path(args.case_log_dir)
    case_log_dir.mkdir(parents=True, exist_ok=True)

    print("=== 10_3_2026_heira_exp plan ===")
    print(f"Total commands in base matrix: {len(experiments)}")
    print(f"Selected hierarchical commands (index >= {args.start_index}): {len(selected)}")
    print(f"W&B project: {args.wandb_project}")

    if not selected:
        summary_path = Path(args.summary_csv)
        _write_summary_csv(summary_path, [])
        print(f"No selected commands. Empty summary CSV written to: {summary_path}")
        return 0

    max_workers = args.max_parallel if args.max_parallel > 0 else len(selected)
    max_workers = max(1, min(max_workers, len(selected)))
    print(f"Parallel workers: {max_workers}")

    if args.dry_run:
        rows: list[dict[str, str]] = []
        for idx, exp in selected:
            seed_token = str(getattr(exp, "seed", "na")).replace("/", "_").replace(" ", "_")
            summary_json_path = summary_json_dir / (
                f"{idx:03d}_{getattr(exp, 'domain', 'exp')}_{str(getattr(exp, 'method', 'run')).lower()}_"
                f"seed{seed_token}_h{getattr(exp, 'hierarchical', 'False')}.json"
            )
            cmd = list(getattr(exp, "cmd"))
            if "--summary-json" not in cmd:
                cmd += ["--summary-json", str(summary_json_path)]
            cmd_str = " ".join(shlex.quote(c) for c in cmd)
            print(f"[base_index={idx}] {getattr(exp, 'label')}")
            print(f"$ {cmd_str}\n")
            rows.append(
                {
                    "index": str(idx),
                    "status": "DRY_RUN",
                    "exit_code": "0",
                    "elapsed_seconds": "0.0",
                    "label": str(getattr(exp, "label")),
                    "domain": str(getattr(exp, "domain")),
                    "method": str(getattr(exp, "method")),
                    "adaptive": str(getattr(exp, "adaptive")),
                    "hierarchical": str(getattr(exp, "hierarchical")),
                    "fixed_weather": str(getattr(exp, "fixed_weather")),
                    "seed": str(getattr(exp, "seed")),
                    "budget": str(getattr(exp, "budget")),
                    "summary_json": str(summary_json_path),
                    "case_log": "",
                    "deterministic_return": "",
                    "stochastic_return_mean": "",
                    "stochastic_return_std": "",
                    "baseline_best_return": "",
                    "uplift_vs_best_baseline_det": "",
                    "pak_holdout_return": "",
                    "command": cmd_str,
                }
            )
        rows.sort(key=lambda r: int(r["index"]))
        summary_path = Path(args.summary_csv)
        _write_summary_csv(summary_path, rows)
        print(f"Dry-run summary CSV written to: {summary_path}")
        return 0

    results: list[dict[str, str]] = []
    failed = 0

    print("\nLaunching parallel hierarchical runs...")
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {
            pool.submit(_run_case, base, repo_root, run_env, summary_json_dir, case_log_dir, idx, exp): (idx, exp)
            for idx, exp in selected
        }
        completed_count = 0
        for future in as_completed(future_map):
            row = future.result()
            completed_count += 1
            results.append(row)
            if row["status"] != "OK":
                failed += 1
            print(
                f"[{row['status']}] {completed_count}/{len(selected)} | base_index={row['index']} | "
                f"{row['label']} | {float(row['elapsed_seconds']):.1f}s"
            )

    results.sort(key=lambda r: int(r["index"]))
    summary_path = Path(args.summary_csv)
    _write_summary_csv(summary_path, results)

    print("\n=== Summary ===")
    for row in results:
        print(
            f"{row['status']:7s} | {float(row['elapsed_seconds']):10.1f}s | "
            f"{row['domain']:13s} | {row['method']:8s} | {row['label']}"
        )
    print(f"\nSummary CSV written to: {summary_path}")
    print(f"Per-case logs dir: {case_log_dir}")

    if failed:
        print(f"Completed with failures: {failed}/{len(results)} commands failed.")
        return 1
    print(f"All {len(results)} selected commands completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
