#!/usr/bin/env python3
"""Legacy compatibility wrapper for run_all_2 behavior.

This delegates execution to:
  run_experiments_7_3_2026.py

Compatibility defaults preserved from legacy run_all_2:
- DQN ablations disabled unless explicitly enabled
- baseline run disabled unless explicitly enabled
- summary output paths kept as legacy defaults unless explicitly overridden
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _has_flag(user_args: list[str], flag: str) -> bool:
    return any(arg == flag or arg.startswith(flag + "=") for arg in user_args)


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    target = repo_root / "run_experiments_7_3_2026.py"
    user_args = list(sys.argv[1:])

    cmd = [sys.executable, str(target)]

    # Keep legacy run_all_2 defaults unless caller explicitly sets include/no flags.
    if not (_has_flag(user_args, "--include-dqn") or _has_flag(user_args, "--no-dqn")):
        cmd.append("--no-dqn")
    if not (_has_flag(user_args, "--include-baseline") or _has_flag(user_args, "--no-baseline")):
        cmd.append("--no-baseline")

    if not _has_flag(user_args, "--summary-csv"):
        cmd += ["--summary-csv", "runs/experiment_summaries/run_all_2_summary.csv"]
    if not _has_flag(user_args, "--summary-json-dir"):
        cmd += ["--summary-json-dir", "runs/experiment_summaries/metrics"]

    cmd.extend(user_args)
    print("Delegating to run_experiments_7_3_2026.py")
    return subprocess.run(cmd, cwd=repo_root).returncode


if __name__ == "__main__":
    raise SystemExit(main())

