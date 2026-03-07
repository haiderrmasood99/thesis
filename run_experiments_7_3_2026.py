#!/usr/bin/env python3
"""Unified thesis experiment runner (March 7, 2026).

This script consolidates the old runner variants into one configurable entrypoint.
It supports:
- fertilization core matrix (PPO/A2C, adaptive/nonadaptive, fixed/random weather)
- crop-planning core matrix (PPO/A2C, adaptive/nonadaptive, fixed/random weather)
- optional hierarchical crop-planning runs
- optional DQN ablations
- optional fertilization baseline run
- standardized per-run summary JSON + aggregated CSV

By default, it routes runs to W&B project "Thesis-Final".

Examples:
  python run_experiments_7_3_2026.py --dry-run
  python run_experiments_7_3_2026.py
  python run_experiments_7_3_2026.py --no-hierarchical --no-dqn --no-baseline
  python run_experiments_7_3_2026.py --seeds 0 --fert-total-years 1000 --dry-run
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
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExperimentCase:
    label: str
    domain: str
    method: str
    adaptive: str
    fixed_weather: str
    seed: str
    budget: str
    cmd: list[str]
    hierarchical: str = "False"


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


def _append_tracking_flag(cmd: list[str], without_tracking: bool) -> list[str]:
    if without_tracking and "--without-tracking" not in cmd:
        return [*cmd, "--without-tracking"]
    return cmd


def build_fertilization_core(
    py_exec: str,
    seeds: list[int],
    total_years_list: list[int],
    n_process: int,
    eval_freq: int,
    nutrient_action_mode: str,
    price_profile: str,
    maxN: float,
    maxP: float,
    maxK: float,
    p_actions: int,
    k_actions: int,
    n_nh4_rate: float,
    without_tracking: bool,
) -> list[ExperimentCase]:
    cases: list[ExperimentCase] = []
    methods = ["PPO", "A2C"]

    for method in methods:
        for total_years in total_years_list:
            for seed in seeds:
                for fixed_weather in [True, False]:
                    for nonadaptive in [False, True]:
                        cmd = [
                            py_exec,
                            "experiments/fertilization/train.py",
                            "--method",
                            method,
                            "--total-years",
                            str(total_years),
                            "--n-process",
                            str(n_process),
                            "--eval-freq",
                            str(eval_freq),
                            "--seed",
                            str(seed),
                            "--nutrient-action-mode",
                            nutrient_action_mode,
                            "--price-profile",
                            price_profile,
                            "--maxN",
                            str(maxN),
                            "--maxP",
                            str(maxP),
                            "--maxK",
                            str(maxK),
                            "--p-actions",
                            str(p_actions),
                            "--k-actions",
                            str(k_actions),
                            "--n-nh4-rate",
                            str(n_nh4_rate),
                        ]
                        if fixed_weather:
                            cmd.append("--fixed-weather")
                        if nonadaptive:
                            cmd.append("--nonadaptive")
                        cmd = _append_tracking_flag(cmd, without_tracking)

                        label = (
                            f"Fertilization | {method} | "
                            f"{'nonadaptive' if nonadaptive else 'adaptive'} | "
                            f"{'fixed_weather' if fixed_weather else 'random_weather'} | "
                            f"years={total_years} | seed={seed}"
                        )
                        cases.append(
                            ExperimentCase(
                                label=label,
                                domain="fertilization",
                                method=method,
                                adaptive="False" if nonadaptive else "True",
                                fixed_weather=str(fixed_weather),
                                seed=str(seed),
                                budget=f"total_years={total_years}",
                                cmd=cmd,
                            )
                        )
    return cases


def build_crop_planning_core(
    py_exec: str,
    seeds: list[int],
    include_hierarchical: bool,
    hierarchical_price_profile: str,
    without_tracking: bool,
) -> list[ExperimentCase]:
    cases: list[ExperimentCase] = []
    methods = ["PPO", "A2C"]

    for method in methods:
        for seed in seeds:
            for fixed_weather in [True, False]:
                for nonadaptive in [False, True]:
                    cmd = [
                        py_exec,
                        "experiments/crop_planning/train.py",
                        "--method",
                        method,
                        "--fixed_weather",
                        str(fixed_weather),
                        "--non_adaptive",
                        str(nonadaptive),
                        "--seed",
                        str(seed),
                    ]
                    cmd = _append_tracking_flag(cmd, without_tracking)
                    label = (
                        f"Crop planning | {method} | "
                        f"{'nonadaptive' if nonadaptive else 'adaptive'} | "
                        f"{'fixed_weather' if fixed_weather else 'random_weather'} | "
                        f"seed={seed}"
                    )
                    cases.append(
                        ExperimentCase(
                            label=label,
                            domain="crop_planning",
                            method=method,
                            adaptive="False" if nonadaptive else "True",
                            fixed_weather=str(fixed_weather),
                            seed=str(seed),
                            budget="total_timesteps=500(default)",
                            cmd=cmd,
                        )
                    )

                if include_hierarchical:
                    h_cmd = [
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
                        hierarchical_price_profile,
                        "--seed",
                        str(seed),
                    ]
                    h_cmd = _append_tracking_flag(h_cmd, without_tracking)
                    h_label = (
                        f"Crop planning hierarchical | {method} | "
                        f"{'fixed_weather' if fixed_weather else 'random_weather'} | "
                        f"seed={seed} | profile={hierarchical_price_profile}"
                    )
                    cases.append(
                        ExperimentCase(
                            label=h_label,
                            domain="crop_planning",
                            method=method,
                            adaptive="hierarchical",
                            fixed_weather=str(fixed_weather),
                            seed=str(seed),
                            budget="total_timesteps=500(default)",
                            cmd=h_cmd,
                            hierarchical="True",
                        )
                    )
    return cases


def build_dqn_ablations(
    py_exec: str,
    dqn_seed: int,
    dqn_total_years: int,
    n_process: int,
    eval_freq: int,
    nutrient_action_mode: str,
    price_profile: str,
    maxN: float,
    maxP: float,
    maxK: float,
    p_actions: int,
    k_actions: int,
    n_nh4_rate: float,
    without_tracking: bool,
) -> list[ExperimentCase]:
    cases: list[ExperimentCase] = []

    # Fertilization DQN (adaptive only), fixed + random weather
    for fixed_weather in [True, False]:
        cmd = [
            py_exec,
            "experiments/fertilization/train.py",
            "--method",
            "DQN",
            "--total-years",
            str(dqn_total_years),
            "--n-process",
            str(n_process),
            "--eval-freq",
            str(eval_freq),
            "--seed",
            str(dqn_seed),
            "--nutrient-action-mode",
            nutrient_action_mode,
            "--price-profile",
            price_profile,
            "--maxN",
            str(maxN),
            "--maxP",
            str(maxP),
            "--maxK",
            str(maxK),
            "--p-actions",
            str(p_actions),
            "--k-actions",
            str(k_actions),
            "--n-nh4-rate",
            str(n_nh4_rate),
        ]
        if fixed_weather:
            cmd.append("--fixed-weather")
        cmd = _append_tracking_flag(cmd, without_tracking)

        cases.append(
            ExperimentCase(
                label=(
                    f"Fertilization | DQN ablation | adaptive | "
                    f"{'fixed_weather' if fixed_weather else 'random_weather'} | "
                    f"years={dqn_total_years} | seed={dqn_seed}"
                ),
                domain="fertilization",
                method="DQN",
                adaptive="True",
                fixed_weather=str(fixed_weather),
                seed=str(dqn_seed),
                budget=f"total_years={dqn_total_years}",
                cmd=cmd,
            )
        )

    # Crop planning DQN (nonadaptive), fixed + random weather
    for fixed_weather in [True, False]:
        cmd = [
            py_exec,
            "experiments/crop_planning/train.py",
            "--method",
            "DQN",
            "--fixed_weather",
            str(fixed_weather),
            "--non_adaptive",
            "True",
            "--seed",
            str(dqn_seed),
        ]
        cmd = _append_tracking_flag(cmd, without_tracking)
        cases.append(
            ExperimentCase(
                label=(
                    f"Crop planning | DQN ablation | nonadaptive | "
                    f"{'fixed_weather' if fixed_weather else 'random_weather'} | "
                    f"seed={dqn_seed}"
                ),
                domain="crop_planning",
                method="DQN",
                adaptive="False",
                fixed_weather=str(fixed_weather),
                seed=str(dqn_seed),
                budget="total_timesteps=500(default)",
                cmd=cmd,
            )
        )

    return cases


def build_baseline(
    py_exec: str,
    nutrient_action_mode: str,
    price_profile: str,
    maxN: float,
    maxP: float,
    maxK: float,
    p_actions: int,
    k_actions: int,
    n_nh4_rate: float,
    without_tracking: bool,
) -> list[ExperimentCase]:
    cmd = [
        py_exec,
        "experiments/fertilization/train.py",
        "--end-year",
        "2005",
        "--baseline",
        "--nutrient-action-mode",
        nutrient_action_mode,
        "--price-profile",
        price_profile,
        "--maxN",
        str(maxN),
        "--maxP",
        str(maxP),
        "--maxK",
        str(maxK),
        "--p-actions",
        str(p_actions),
        "--k-actions",
        str(k_actions),
        "--n-nh4-rate",
        str(n_nh4_rate),
    ]
    cmd = _append_tracking_flag(cmd, without_tracking)
    return [
        ExperimentCase(
            label="Fertilization | Baseline only | end-year=2005",
            domain="fertilization",
            method="BASELINE",
            adaptive="n/a",
            fixed_weather="n/a",
            seed="n/a",
            budget="n/a",
            cmd=cmd,
        )
    ]


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


def write_summary_csv(path: Path, rows: list[dict[str, str]]) -> None:
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
        "deterministic_return",
        "stochastic_return_mean",
        "stochastic_return_std",
        "baseline_best_return",
        "uplift_vs_best_baseline_det",
        "pak_holdout_return",
        "command",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _build_run_env(args: argparse.Namespace) -> dict[str, str]:
    env = dict(os.environ)

    # Route both domains to one project by default.
    env["WANDB_PROJECT"] = args.wandb_project
    env["WANDB_PROJECT_FERTILIZATION"] = args.wandb_project
    env["WANDB_PROJECT_CROP_PLANNING"] = args.wandb_project
    if args.wandb_entity:
        env["WANDB_ENTITY"] = args.wandb_entity
    if args.wandb_offline:
        env["WANDB_MODE"] = "offline"

    return env


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-on-fail", action="store_true", help="Stop immediately when a command fails.")
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

    parser.add_argument(
        "--include-hierarchical",
        dest="include_hierarchical",
        action="store_true",
        default=True,
        help="Include hierarchical crop-planning runs.",
    )
    parser.add_argument(
        "--no-hierarchical",
        dest="include_hierarchical",
        action="store_false",
        help="Exclude hierarchical crop-planning runs.",
    )
    parser.add_argument(
        "--hierarchical-price-profile",
        default="pakistan_baseline",
        help="Price profile for hierarchical runs.",
    )

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
        "--summary-csv",
        default="runs/experiment_summaries/run_experiments_7_3_2026_summary.csv",
        help="CSV output path for run summary.",
    )
    parser.add_argument(
        "--summary-json-dir",
        default="runs/experiment_summaries/metrics_7_3_2026",
        help="Directory where standardized summary JSON files are written.",
    )
    args = parser.parse_args()

    seeds = parse_int_list(args.seeds)
    total_years_list = parse_int_list(args.fert_total_years)

    repo_root = Path(__file__).resolve().parent
    py_exec = sys.executable
    run_env = _build_run_env(args)

    experiments: list[ExperimentCase] = []
    experiments.extend(
        build_fertilization_core(
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
        build_crop_planning_core(
            py_exec=py_exec,
            seeds=seeds,
            include_hierarchical=args.include_hierarchical,
            hierarchical_price_profile=args.hierarchical_price_profile,
            without_tracking=args.without_tracking,
        )
    )

    if args.include_dqn:
        experiments.extend(
            build_dqn_ablations(
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
            build_baseline(
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

    total = len(experiments)
    summary_json_dir = Path(args.summary_json_dir)
    summary_json_dir.mkdir(parents=True, exist_ok=True)

    print("=== run_experiments_7_3_2026 plan ===")
    print(f"Total commands: {total}")
    print(f"W&B project: {args.wandb_project}")
    print(f"Seeds: {seeds}")
    print(f"Fertilization years: {total_years_list}")
    print(f"Include hierarchical: {args.include_hierarchical}")
    print(f"Include DQN: {args.include_dqn}")
    print(f"Include baseline: {args.include_baseline}")
    if args.without_tracking:
        print("Tracking mode: --without-tracking enabled in train scripts")
    elif args.wandb_offline:
        print("Tracking mode: WANDB_MODE=offline")

    results: list[dict[str, str]] = []
    failed = 0

    for idx, exp in enumerate(experiments, start=1):
        seed_token = exp.seed.replace("/", "_").replace(" ", "_")
        summary_json_path = summary_json_dir / (
            f"{idx:03d}_{exp.domain}_{exp.method.lower()}_seed{seed_token}_h{exp.hierarchical}.json"
        )
        cmd = [*exp.cmd]
        if "--summary-json" not in cmd:
            cmd += ["--summary-json", str(summary_json_path)]

        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        print(f"\n[{idx}/{total}] {exp.label}")
        print(f"$ {cmd_str}\n")

        if args.dry_run:
            results.append(
                {
                    "index": str(idx),
                    "status": "DRY_RUN",
                    "exit_code": "0",
                    "elapsed_seconds": "0.0",
                    "label": exp.label,
                    "domain": exp.domain,
                    "method": exp.method,
                    "adaptive": exp.adaptive,
                    "hierarchical": exp.hierarchical,
                    "fixed_weather": exp.fixed_weather,
                    "seed": exp.seed,
                    "budget": exp.budget,
                    "summary_json": str(summary_json_path),
                    "deterministic_return": "",
                    "stochastic_return_mean": "",
                    "stochastic_return_std": "",
                    "baseline_best_return": "",
                    "uplift_vs_best_baseline_det": "",
                    "pak_holdout_return": "",
                    "command": cmd_str,
                }
            )
            continue

        start = time.time()
        completed = subprocess.run(cmd, cwd=repo_root, env=run_env)
        elapsed = time.time() - start
        status = "OK" if completed.returncode == 0 else "FAILED"
        if completed.returncode != 0:
            failed += 1

        print(f"[{status}] {exp.label} (exit={completed.returncode}, {elapsed:.1f}s)")

        row = {
            "index": str(idx),
            "status": status,
            "exit_code": str(completed.returncode),
            "elapsed_seconds": f"{elapsed:.3f}",
            "label": exp.label,
            "domain": exp.domain,
            "method": exp.method,
            "adaptive": exp.adaptive,
            "hierarchical": exp.hierarchical,
            "fixed_weather": exp.fixed_weather,
            "seed": exp.seed,
            "budget": exp.budget,
            "summary_json": str(summary_json_path),
            "deterministic_return": "",
            "stochastic_return_mean": "",
            "stochastic_return_std": "",
            "baseline_best_return": "",
            "uplift_vs_best_baseline_det": "",
            "pak_holdout_return": "",
            "command": cmd_str,
        }
        row.update(_read_summary_metrics(summary_json_path))
        results.append(row)

        if completed.returncode != 0 and args.stop_on_fail:
            break

    summary_path = Path(args.summary_csv)
    write_summary_csv(summary_path, results)

    print("\n=== Summary ===")
    for row in results:
        print(
            f"{row['status']:7s} | {float(row['elapsed_seconds']):10.1f}s | "
            f"{row['domain']:13s} | {row['method']:8s} | {row['label']}"
        )
    print(f"\nSummary CSV written to: {summary_path}")

    if failed:
        print(f"Completed with failures: {failed}/{len(results)} commands failed.")
        return 1
    print(f"All {len(results)} commands completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

