#!/usr/bin/env python3
"""Run points 1/2/3 ablation launchers, optionally in parallel."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_OUTPUT = REPO_ROOT / "artifacts" / "final_successful_runs" / "low_hanging_ablation" / "run_all"


def _run_cmd(cmd: list[str], cwd: Path, log_path: Path) -> tuple[int, float]:
    start = time.time()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_fh:
        log_fh.write("$ " + " ".join(cmd) + "\n\n")
        log_fh.flush()
        completed = subprocess.run(cmd, cwd=cwd, stdout=log_fh, stderr=subprocess.STDOUT)
    elapsed = time.time() - start
    return completed.returncode, elapsed


def _point_cmd(
    py_exec: str,
    script_name: str,
    run_tag: str,
    output_root: Path,
    max_workers: int,
    args: argparse.Namespace,
) -> list[str]:
    cmd = [
        py_exec,
        str(SCRIPT_DIR / script_name),
        "--run-tag",
        run_tag,
        "--output-root",
        str(output_root),
        "--max-workers",
        str(max_workers),
        "--seeds",
        args.seeds,
        "--weather-modes",
        args.weather_modes,
        "--wandb-project",
        args.wandb_project,
    ]
    if args.wandb_entity:
        cmd += ["--wandb-entity", args.wandb_entity]
    if args.wandb_offline:
        cmd.append("--wandb-offline")
    if args.without_tracking:
        cmd.append("--without-tracking")
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Run low-hanging ablation points 1/2/3.")
    parser.add_argument("--include-point1", action="store_true", default=True)
    parser.add_argument("--no-point1", action="store_false", dest="include_point1")
    parser.add_argument("--include-point2", action="store_true", default=True)
    parser.add_argument("--no-point2", action="store_false", dest="include_point2")
    parser.add_argument("--include-point3", action="store_true", default=True)
    parser.add_argument("--no-point3", action="store_false", dest="include_point3")
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--weather-modes", default="fixed,random")
    parser.add_argument("--point-workers", type=int, default=2, help="Workers inside each point script.")
    parser.add_argument("--parallel-points", type=int, default=2, help="How many point scripts to run together.")
    parser.add_argument("--wandb-project", default="Thesis-Final")
    parser.add_argument("--wandb-entity", default="")
    parser.add_argument("--wandb-offline", action="store_true")
    parser.add_argument("--without-tracking", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-tag", default="", help="Optional shared run tag prefix.")
    parser.add_argument("--output-root", default="", help="Optional custom run-all output root.")

    parser.add_argument("--point1-methods", default="PPO")
    parser.add_argument("--point1-ent-coefs", default="0.0,0.01")
    parser.add_argument("--point1-total-years", type=int, default=1000)
    parser.add_argument("--point1-include-nonadaptive", action="store_true")

    parser.add_argument("--point2-methods", default="PPO,A2C")
    parser.add_argument("--point2-blocked-penalties", default="0.0,0.02,0.05")
    parser.add_argument("--point2-nutrient-cost-weight", type=float, default=1.0)

    parser.add_argument("--point3-methods", default="PPO")
    parser.add_argument("--point3-cost-weights", default="0.8,1.0,1.2")
    parser.add_argument("--point3-total-years", type=int, default=1000)
    parser.add_argument("--point3-include-nonadaptive", action="store_true")
    args = parser.parse_args()

    run_tag = args.run_tag or datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output = Path(args.output_root) if args.output_root else DEFAULT_BASE_OUTPUT / run_tag
    base_output.mkdir(parents=True, exist_ok=True)

    points: list[tuple[str, list[str], Path, Path]] = []

    if args.include_point1:
        point1_output = base_output / "point1_entropy"
        cmd = _point_cmd(
            py_exec=sys.executable,
            script_name="run_point1_entropy_ablation.py",
            run_tag=f"{run_tag}_p1",
            output_root=point1_output,
            max_workers=max(1, int(args.point_workers)),
            args=args,
        )
        cmd += [
            "--methods",
            args.point1_methods,
            "--ent-coefs",
            args.point1_ent_coefs,
            "--total-years",
            str(args.point1_total_years),
        ]
        if args.point1_include_nonadaptive:
            cmd.append("--include-nonadaptive")
        points.append(("point1_entropy", cmd, point1_output, base_output / "logs" / "point1_entropy.log"))

    if args.include_point2:
        point2_output = base_output / "point2_hierarchical"
        cmd = _point_cmd(
            py_exec=sys.executable,
            script_name="run_point2_hierarchical_shaping_ablation.py",
            run_tag=f"{run_tag}_p2",
            output_root=point2_output,
            max_workers=max(1, int(args.point_workers)),
            args=args,
        )
        cmd += [
            "--methods",
            args.point2_methods,
            "--blocked-penalties",
            args.point2_blocked_penalties,
            "--nutrient-cost-weight",
            str(args.point2_nutrient_cost_weight),
        ]
        points.append(("point2_hierarchical", cmd, point2_output, base_output / "logs" / "point2_hierarchical.log"))

    if args.include_point3:
        point3_output = base_output / "point3_cost_weight"
        cmd = _point_cmd(
            py_exec=sys.executable,
            script_name="run_point3_nutrient_cost_weight_ablation.py",
            run_tag=f"{run_tag}_p3",
            output_root=point3_output,
            max_workers=max(1, int(args.point_workers)),
            args=args,
        )
        cmd += [
            "--methods",
            args.point3_methods,
            "--cost-weights",
            args.point3_cost_weights,
            "--total-years",
            str(args.point3_total_years),
        ]
        if args.point3_include_nonadaptive:
            cmd.append("--include-nonadaptive")
        points.append(("point3_cost_weight", cmd, point3_output, base_output / "logs" / "point3_cost_weight.log"))

    if not points:
        print("No points selected. Nothing to run.")
        return 0

    rows: list[dict[str, object]] = []
    parallel_points = max(1, min(int(args.parallel_points), len(points)))
    print(f"Running {len(points)} point script(s) with parallel_points={parallel_points}")

    with ThreadPoolExecutor(max_workers=parallel_points) as executor:
        future_map = {
            executor.submit(_run_cmd, cmd, REPO_ROOT, log_path): (name, cmd, output_dir, log_path)
            for (name, cmd, output_dir, log_path) in points
        }
        for future in as_completed(future_map):
            name, cmd, output_dir, log_path = future_map[future]
            exit_code, elapsed = future.result()
            status = "OK" if exit_code == 0 else "FAILED"
            row = {
                "point": name,
                "status": status,
                "exit_code": exit_code,
                "elapsed_seconds": round(elapsed, 3),
                "output_dir": str(output_dir),
                "log_path": str(log_path),
                "command": " ".join(cmd),
            }
            rows.append(row)
            print(f"[{status}] {name} (exit={exit_code}, elapsed_s={elapsed:.3f})")

    summary_csv = base_output / "run_all_summary.csv"
    fields = ["point", "status", "exit_code", "elapsed_seconds", "output_dir", "log_path", "command"]
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda x: str(x["point"])))

    failures = sum(1 for row in rows if row["status"] != "OK")
    print(f"Run-all summary CSV: {summary_csv}")
    print(f"Points completed={len(rows)} failed={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

