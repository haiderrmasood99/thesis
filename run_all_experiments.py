#!/usr/bin/env python3
"""Legacy compatibility wrapper.

This entrypoint now delegates to:
  run_experiments_7_3_2026.py

All CLI args are forwarded unchanged.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    target = repo_root / "run_experiments_7_3_2026.py"
    cmd = [sys.executable, str(target), *sys.argv[1:]]
    print("Delegating to run_experiments_7_3_2026.py")
    return subprocess.run(cmd, cwd=repo_root).returncode


if __name__ == "__main__":
    raise SystemExit(main())

