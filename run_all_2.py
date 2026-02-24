#!/usr/bin/env python3
"""Thesis-focused experiment runner with reproducible experiment matrix and CSV summary.

Usage:
  python run_all_2.py

Common options:
  python run_all_2.py --stop-on-fail
  python run_all_2.py --seeds 0,1,2 --fert-total-years 1000,3000,5000
  python run_all_2.py --include-dqn --include-baseline
  python run_all_2.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Experiment:
    label: str
    cmd: list[str]
    domain: str
    method: str
    adaptive: str
    fixed_weather: str
    seed: str
    budget: str


def parse_int_list(value: str) -> list[int]:
    out: list[int] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        out.append(int(token))
    return out


def build_fertilization_core(
    py_exec: str,
    seeds: list[int],
    total_years_list: list[int],
    n_process: int,
    eval_freq: int,
) -> list[Experiment]:
    experiments: list[Experiment] = []
    methods = ["PPO", "A2C"]
    fixed_weather_values = [True, False]
    nonadaptive_values = [False, True]

    for method in methods:
        for total_years in total_years_list:
            for seed in seeds:
                for fixed_weather in fixed_weather_values:
                    for nonadaptive in nonadaptive_values:
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
                        ]
                        if fixed_weather:
                            cmd.append("--fixed-weather")
                        if nonadaptive:
                            cmd.append("--nonadaptive")

                        label = (
                            f"Fertilization | {method} | "
                            f"{'nonadaptive' if nonadaptive else 'adaptive'} | "
                            f"{'fixed_weather' if fixed_weather else 'random_weather'} | "
                            f"years={total_years} | seed={seed}"
                        )
                        experiments.append(
                            Experiment(
                                label=label,
                                cmd=cmd,
                                domain="fertilization",
                                method=method,
                                adaptive="False" if nonadaptive else "True",
                                fixed_weather=str(fixed_weather),
                                seed=str(seed),
                                budget=f"total_years={total_years}",
                            )
                        )

    return experiments


def build_crop_planning_core(py_exec: str, seeds: list[int]) -> list[Experiment]:
    experiments: list[Experiment] = []
    methods = ["PPO", "A2C"]
    fixed_weather_values = [True, False]
    nonadaptive_values = [False, True]

    for method in methods:
        for seed in seeds:
            for fixed_weather in fixed_weather_values:
                for nonadaptive in nonadaptive_values:
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
                    label = (
                        f"Crop planning | {method} | "
                        f"{'nonadaptive' if nonadaptive else 'adaptive'} | "
                        f"{'fixed_weather' if fixed_weather else 'random_weather'} | "
                        f"seed={seed}"
                    )
                    experiments.append(
                        Experiment(
                            label=label,
                            cmd=cmd,
                            domain="crop_planning",
                            method=method,
                            adaptive="False" if nonadaptive else "True",
                            fixed_weather=str(fixed_weather),
                            seed=str(seed),
                            budget="total_timesteps=500(default)",
                        )
                    )

    return experiments


def build_dqn_ablations(
    py_exec: str,
    dqn_seed: int,
    dqn_total_years: int,
    n_process: int,
    eval_freq: int,
) -> list[Experiment]:
    experiments: list[Experiment] = []

    # Fertilization DQN ablations (adaptive only, fixed and random weather)
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
        ]
        if fixed_weather:
            cmd.append("--fixed-weather")
        experiments.append(
            Experiment(
                label=(
                    f"Fertilization | DQN ablation | adaptive | "
                    f"{'fixed_weather' if fixed_weather else 'random_weather'} | "
                    f"years={dqn_total_years} | seed={dqn_seed}"
                ),
                cmd=cmd,
                domain="fertilization",
                method="DQN",
                adaptive="True",
                fixed_weather=str(fixed_weather),
                seed=str(dqn_seed),
                budget=f"total_years={dqn_total_years}",
            )
        )

    # Crop planning DQN ablations
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
        experiments.append(
            Experiment(
                label=(
                    f"Crop planning | DQN ablation | nonadaptive | "
                    f"{'fixed_weather' if fixed_weather else 'random_weather'} | "
                    f"seed={dqn_seed}"
                ),
                cmd=cmd,
                domain="crop_planning",
                method="DQN",
                adaptive="False",
                fixed_weather=str(fixed_weather),
                seed=str(dqn_seed),
                budget="total_timesteps=500(default)",
            )
        )

    return experiments


def build_baseline(py_exec: str) -> list[Experiment]:
    return [
        Experiment(
            label="Fertilization | Baseline only | end-year=2005",
            cmd=[py_exec, "experiments/fertilization/train.py", "--end-year", "2005", "--baseline"],
            domain="fertilization",
            method="BASELINE",
            adaptive="n/a",
            fixed_weather="n/a",
            seed="n/a",
            budget="n/a",
        )
    ]


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
        "fixed_weather",
        "seed",
        "budget",
        "command",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


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
    parser.add_argument("--fert-n-process", type=int, default=8, help="Number of parallel envs for fertilization.")
    parser.add_argument("--fert-eval-freq", type=int, default=20000, help="Eval frequency for fertilization.")
    parser.add_argument("--include-dqn", action="store_true", help="Include DQN ablation runs.")
    parser.add_argument("--dqn-seed", type=int, default=0, help="Seed for DQN ablations.")
    parser.add_argument("--dqn-total-years", type=int, default=5000, help="Fertilization total-years for DQN.")
    parser.add_argument("--include-baseline", action="store_true", help="Include fertilization baseline run.")
    parser.add_argument(
        "--summary-csv",
        default="runs/experiment_summaries/run_all_2_summary.csv",
        help="CSV output path for run summary.",
    )
    args = parser.parse_args()

    seeds = parse_int_list(args.seeds)
    total_years_list = parse_int_list(args.fert_total_years)

    repo_root = Path(__file__).resolve().parent
    py_exec = sys.executable

    experiments: list[Experiment] = []
    experiments.extend(
        build_fertilization_core(
            py_exec=py_exec,
            seeds=seeds,
            total_years_list=total_years_list,
            n_process=args.fert_n_process,
            eval_freq=args.fert_eval_freq,
        )
    )
    experiments.extend(build_crop_planning_core(py_exec=py_exec, seeds=seeds))

    if args.include_dqn:
        experiments.extend(
            build_dqn_ablations(
                py_exec=py_exec,
                dqn_seed=args.dqn_seed,
                dqn_total_years=args.dqn_total_years,
                n_process=args.fert_n_process,
                eval_freq=args.fert_eval_freq,
            )
        )
    if args.include_baseline:
        experiments.extend(build_baseline(py_exec=py_exec))

    total = len(experiments)
    print("=== run_all_2 experiment plan ===")
    print(f"Total commands: {total}")
    print(
        f"Core: fertilization(PPO/A2C, adaptive/nonadaptive, fixed/random, years={total_years_list}, seeds={seeds}) "
        f"+ crop_planning(PPO/A2C, adaptive/nonadaptive, fixed/random, seeds={seeds})"
    )
    if args.include_dqn:
        print("Includes DQN ablations.")
    if args.include_baseline:
        print("Includes fertilization baseline.")

    results: list[dict[str, str]] = []
    failed = 0

    for idx, exp in enumerate(experiments, start=1):
        cmd_str = " ".join(shlex.quote(c) for c in exp.cmd)
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
                    "fixed_weather": exp.fixed_weather,
                    "seed": exp.seed,
                    "budget": exp.budget,
                    "command": cmd_str,
                }
            )
            continue

        start = time.time()
        completed = subprocess.run(exp.cmd, cwd=repo_root)
        elapsed = time.time() - start
        status = "OK" if completed.returncode == 0 else "FAILED"
        if completed.returncode != 0:
            failed += 1

        print(f"[{status}] {exp.label} (exit={completed.returncode}, {elapsed:.1f}s)")

        results.append(
            {
                "index": str(idx),
                "status": status,
                "exit_code": str(completed.returncode),
                "elapsed_seconds": f"{elapsed:.3f}",
                "label": exp.label,
                "domain": exp.domain,
                "method": exp.method,
                "adaptive": exp.adaptive,
                "fixed_weather": exp.fixed_weather,
                "seed": exp.seed,
                "budget": exp.budget,
                "command": cmd_str,
            }
        )

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

