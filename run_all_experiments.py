#!/usr/bin/env python3
"""Run all requested training commands sequentially.

Usage (Linux/Jupyter terminal):
  python run_all_experiments.py

Optional:
  python run_all_experiments.py --stop-on-fail
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
import time
from pathlib import Path


def build_commands(py_exec: str) -> list[tuple[str, list[str]]]:
    return [
        # (
        #     "Fertilization | PPO adaptive fixed weather",
        #     [
        #         py_exec,
        #         "experiments/fertilization/train.py",
        #         "--total-years",
        #         "5000",
        #         "--n-process",
        #         "8",
        #         "--eval-freq",
        #         "20000",
        #         "--fixed-weather",
        #     ],
        # ),
        (
            "Fertilization | PPO adaptive random weather",
            [
                py_exec,
                "experiments/fertilization/train.py",
                "--total-years",
                "5000",
                "--n-process",
                "8",
                "--eval-freq",
                "20000",
            ],
        ),
        # (
        #     "Fertilization | PPO non-adaptive fixed weather",
        #     [
        #         py_exec,
        #         "experiments/fertilization/train.py",
        #         "--total-years",
        #         "5000",
        #         "--n-process",
        #         "8",
        #         "--eval-freq",
        #         "20000",
        #         "--nonadaptive",
        #         "--fixed-weather",
        #     ],
        # ),
        (
            "Fertilization | PPO non-adaptive random weather",
            [
                py_exec,
                "experiments/fertilization/train.py",
                "--total-years",
                "5000",
                "--n-process",
                "8",
                "--eval-freq",
                "20000",
                "--nonadaptive",
            ],
        ),
        (
            "Fertilization | PPO non-adaptive entropy 0.01",
            [
                py_exec,
                "experiments/fertilization/train.py",
                "--total-years",
                "5000",
                "--n-process",
                "8",
                "--eval-freq",
                "20000",
                "--ent-coef",
                "0.01",
                "--nonadaptive",
            ],
        ),
        (
            "Fertilization | Baseline only end-year 2005",
            [
                py_exec,
                "experiments/fertilization/train.py",
                "--end-year",
                "2005",
                "--baseline",
            ],
        ),
        (
            "Crop planning | PPO adaptive fixed weather",
            [
                py_exec,
                "experiments/crop_planning/train.py",
                "--fixed_weather",
                "True",
                "--non_adaptive",
                "False",
                "--seed",
                "1",
            ],
        ),
        (
            "Crop planning | PPO adaptive random weather",
            [
                py_exec,
                "experiments/crop_planning/train.py",
                "--fixed_weather",
                "False",
                "--non_adaptive",
                "False",
                "--seed",
                "1",
            ],
        ),
        (
            "Crop planning | PPO non-adaptive fixed weather",
            [
                py_exec,
                "experiments/crop_planning/train.py",
                "--fixed_weather",
                "True",
                "--non_adaptive",
                "True",
                "--seed",
                "1",
            ],
        ),
        (
            "Crop planning | PPO non-adaptive random weather",
            [
                py_exec,
                "experiments/crop_planning/train.py",
                "--fixed_weather",
                "False",
                "--non_adaptive",
                "True",
                "--seed",
                "1",
            ],
        ),
        (
            "Fertilization | A2C",
            [
                py_exec,
                "experiments/fertilization/train.py",
                "--method",
                "A2C",
                "--total-years",
                "5000",
                "--n-process",
                "8",
                "--eval-freq",
                "20000",
            ],
        ),
        (
            "Fertilization | DQN",
            [
                py_exec,
                "experiments/fertilization/train.py",
                "--method",
                "DQN",
                "--total-years",
                "5000",
                "--n-process",
                "8",
                "--eval-freq",
                "20000",
            ],
        ),
        (
            "Crop planning | A2C",
            [
                py_exec,
                "experiments/crop_planning/train.py",
                "--method",
                "A2C",
                "--fixed_weather",
                "True",
                "--non_adaptive",
                "False",
                "--seed",
                "1",
            ],
        ),
        (
            "Crop planning | DQN",
            [
                py_exec,
                "experiments/crop_planning/train.py",
                "--method",
                "DQN",
                "--fixed_weather",
                "False",
                "--non_adaptive",
                "True",
                "--seed",
                "1",
            ],
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="Stop immediately when a command fails.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    commands = build_commands(sys.executable)

    results: list[tuple[str, int, float, str]] = []
    total = len(commands)

    for idx, (label, cmd) in enumerate(commands, start=1):
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        print(f"\n[{idx}/{total}] {label}")
        print(f"$ {cmd_str}\n")
        start = time.time()
        completed = subprocess.run(cmd, cwd=repo_root)
        elapsed = time.time() - start
        results.append((label, completed.returncode, elapsed, cmd_str))
        status = "OK" if completed.returncode == 0 else "FAILED"
        print(f"[{status}] {label} (exit={completed.returncode}, {elapsed:.1f}s)")
        if completed.returncode != 0 and args.stop_on_fail:
            break

    print("\n=== Summary ===")
    failed = 0
    for label, code, elapsed, _ in results:
        status = "OK" if code == 0 else "FAILED"
        if code != 0:
            failed += 1
        print(f"{status:7s} | {elapsed:16.1f}s | {label}")

    if failed:
        print(f"\nCompleted with failures: {failed}/{len(results)} commands failed.")
        return 1

    print(f"\nAll {len(results)} commands completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
