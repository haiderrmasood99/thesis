#!/usr/bin/env python3
"""Run only fertilization experiments that are NOT already covered by run_all_experiments.py.

Coverage logic:
- run_all_experiments.py already covers PPO with:
  total-years=5000, n-process=8, eval-freq=20000, seed=0
  for adaptive/nonadaptive x fixed/random weather (4 commands).
- This runner filters those out and runs only new variants.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
import time
from pathlib import Path


def parse_int_list(value: str) -> list[int]:
    out: list[int] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        out.append(int(token))
    return out


def is_covered_by_run_all_experiments(
    *,
    total_years: int,
    n_process: int,
    eval_freq: int,
    seed: int,
) -> bool:
    return (
        total_years == 5000
        and n_process == 8
        and eval_freq == 20000
        and seed == 0
    )


def build_unique_commands(
    py_exec: str,
    total_years_values: list[int],
    n_process: int,
    eval_freq: int,
    seeds: list[int],
) -> list[tuple[str, list[str]]]:
    commands: list[tuple[str, list[str]]] = []
    variants = [
        ("adaptive", True, False),
        ("adaptive", False, False),
        ("nonadaptive", True, True),
        ("nonadaptive", False, True),
    ]

    for total_years in total_years_values:
        for seed in seeds:
            for adaptive_name, fixed_weather, nonadaptive in variants:
                if is_covered_by_run_all_experiments(
                    total_years=total_years,
                    n_process=n_process,
                    eval_freq=eval_freq,
                    seed=seed,
                ):
                    continue

                cmd = [
                    py_exec,
                    "experiments/fertilization/train.py",
                    "--method",
                    "PPO",
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
                    f"Fertilization | PPO {adaptive_name} "
                    f"{'fixed weather' if fixed_weather else 'random weather'} "
                    f"| years={total_years} | seed={seed}"
                )
                commands.append((label, cmd))

    return commands


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-on-fail", action="store_true", help="Stop immediately if one command fails.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands only.")
    parser.add_argument(
        "--total-years",
        default="5000",
        help="Comma-separated training budgets in years (default: 5000).",
    )
    parser.add_argument("--n-process", type=int, default=8, help="Parallel environments (default: 8).")
    parser.add_argument("--eval-freq", type=int, default=20000, help="Evaluation frequency (default: 20000).")
    parser.add_argument(
        "--seeds",
        default="1,2",
        help="Comma-separated seeds for unique runs (default: 1,2; seed=0 is already covered).",
    )
    parser.add_argument(
        "--wandb-offline",
        action="store_true",
        help="Set WANDB_MODE=offline for all commands.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    commands = build_unique_commands(
        py_exec=sys.executable,
        total_years_values=parse_int_list(args.total_years),
        n_process=args.n_process,
        eval_freq=args.eval_freq,
        seeds=parse_int_list(args.seeds),
    )

    results: list[tuple[str, int, float]] = []
    total = len(commands)
    print(f"Unique commands to run (excluding run_all_experiments coverage): {total}")
    if total == 0:
        print("No unique commands to run with current arguments.")
        return 0

    env = None
    if args.wandb_offline:
        env = dict(**subprocess.os.environ)
        env["WANDB_MODE"] = "offline"

    for idx, (label, cmd) in enumerate(commands, start=1):
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        print(f"\n[{idx}/{total}] {label}")
        print(f"$ {cmd_str}\n")

        if args.dry_run:
            results.append((label, 0, 0.0))
            continue

        start = time.time()
        completed = subprocess.run(cmd, cwd=repo_root, env=env)
        elapsed = time.time() - start
        results.append((label, completed.returncode, elapsed))

        status = "OK" if completed.returncode == 0 else "FAILED"
        print(f"[{status}] {label} (exit={completed.returncode}, {elapsed:.1f}s)")

        if completed.returncode != 0 and args.stop_on_fail:
            break

    print("\n=== Summary ===")
    failures = 0
    for label, code, elapsed in results:
        status = "OK" if code == 0 else "FAILED"
        if code != 0:
            failures += 1
        print(f"{status:7s} | {elapsed:10.1f}s | {label}")

    if failures:
        print(f"\nCompleted with failures: {failures}/{len(results)}")
        return 1
    print(f"\nAll {len(results)} commands completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
