#!/usr/bin/env python3
"""Point 2: hierarchical blocked-nutrient shaping ablation (parallel launcher)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import (
    AblationCase,
    make_run_env,
    parse_float_list,
    parse_int_list,
    parse_method_list,
    parse_weather_modes,
    run_cases_parallel,
    slugify,
    timestamp_tag,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_OUTPUT = REPO_ROOT / "artifacts" / "final_successful_runs" / "low_hanging_ablation" / "point2_hierarchical_shaping"


def build_cases(
    output_root: Path,
    py_exec: str,
    methods: list[str],
    seeds: list[int],
    weather_modes: list[bool],
    blocked_penalties: list[float],
    nutrient_cost_weight: float,
    price_profile: str,
    without_tracking: bool,
) -> list[AblationCase]:
    cases: list[AblationCase] = []
    case_index = 0
    for method in methods:
        for seed in seeds:
            for fixed_weather in weather_modes:
                for blocked_penalty in blocked_penalties:
                    case_index += 1
                    weather_label = "fixed_weather" if fixed_weather else "random_weather"
                    penalty_label = slugify(f"{blocked_penalty:.6f}".rstrip("0").rstrip("."))
                    slug = (
                        f"p2_{method.lower()}_{weather_label}_seed{seed}_"
                        f"blockpen{penalty_label}"
                    )
                    summary_json = output_root / "summary_json" / f"{slug}.json"
                    case_log = output_root / "logs" / f"{slug}.log"
                    thesis_report_dir = output_root / "thesis_reports" / slug

                    cmd = [
                        py_exec,
                        "experiments/crop_planning/train.py",
                        "--method",
                        method,
                        "--seed",
                        str(seed),
                        "--fixed_weather",
                        str(fixed_weather),
                        "--hierarchical",
                        "True",
                        "--non_adaptive",
                        "False",
                        "--use_pakistan_crop_calendar",
                        "True",
                        "--price_profile",
                        price_profile,
                        "--nutrient-cost-weight",
                        str(nutrient_cost_weight),
                        "--blocked-nutrient-penalty-per-kg",
                        str(blocked_penalty),
                        "--enforce_calendar_windows",
                        "True",
                        "--limit_fertilizer_to_season",
                        "True",
                        "--preplant_fertilizer_days",
                        "14",
                        "--postplant_fertilizer_days",
                        "120",
                        "--enable-thesis-reporting",
                        "True",
                        "--thesis-report-dir",
                        str(thesis_report_dir),
                        "--summary-json",
                        str(summary_json),
                    ]
                    if without_tracking:
                        cmd.append("--without-tracking")

                    label = (
                        f"Point2 Hierarchical Shaping | {method} | {weather_label} | "
                        f"seed={seed} | blocked_penalty={blocked_penalty}"
                    )
                    cases.append(
                        AblationCase(
                            case_id=f"{case_index:03d}",
                            label=label,
                            cmd=cmd,
                            summary_json=summary_json,
                            case_log=case_log,
                            thesis_report_dir=thesis_report_dir,
                            metadata={
                                "point": "point2_hierarchical_shaping",
                                "domain": "crop_planning_hierarchical",
                                "method": method,
                                "seed": seed,
                                "fixed_weather": fixed_weather,
                                "blocked_nutrient_penalty_per_kg": blocked_penalty,
                                "nutrient_cost_weight": nutrient_cost_weight,
                            },
                        )
                    )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Point-2 hierarchical shaping ablation in parallel.")
    parser.add_argument("--methods", default="PPO,A2C", help="Comma-separated methods (PPO,A2C,DQN).")
    parser.add_argument("--seeds", default="0,1,2", help="Comma-separated seeds.")
    parser.add_argument("--weather-modes", default="fixed,random", help="Comma-separated weather modes.")
    parser.add_argument(
        "--blocked-penalties",
        default="0.0,0.02,0.05",
        help="Comma-separated blocked nutrient penalties (per kg).",
    )
    parser.add_argument("--nutrient-cost-weight", type=float, default=1.0)
    parser.add_argument("--price-profile", default="pakistan_baseline")
    parser.add_argument("--max-workers", type=int, default=2, help="Parallel subprocess workers.")
    parser.add_argument("--wandb-project", default="Thesis-Final")
    parser.add_argument("--wandb-entity", default="")
    parser.add_argument("--wandb-offline", action="store_true")
    parser.add_argument("--without-tracking", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-tag", default="", help="Optional run tag for output folder.")
    parser.add_argument("--output-root", default="", help="Optional custom output folder.")
    args = parser.parse_args()

    methods = parse_method_list(args.methods, allowed={"PPO", "A2C", "DQN"})
    seeds = parse_int_list(args.seeds)
    weather_modes = parse_weather_modes(args.weather_modes)
    blocked_penalties = [max(0.0, p) for p in parse_float_list(args.blocked_penalties)]

    run_tag = args.run_tag or timestamp_tag()
    output_root = Path(args.output_root) if args.output_root else DEFAULT_BASE_OUTPUT / run_tag
    output_root.mkdir(parents=True, exist_ok=True)

    cases = build_cases(
        output_root=output_root,
        py_exec=sys.executable,
        methods=methods,
        seeds=seeds,
        weather_modes=weather_modes,
        blocked_penalties=blocked_penalties,
        nutrient_cost_weight=max(0.0, float(args.nutrient_cost_weight)),
        price_profile=args.price_profile,
        without_tracking=bool(args.without_tracking),
    )
    run_env = make_run_env(
        wandb_project=args.wandb_project,
        wandb_entity=args.wandb_entity,
        wandb_offline=bool(args.wandb_offline),
    )
    summary_csv = output_root / "run_summary.csv"
    return run_cases_parallel(
        repo_root=REPO_ROOT,
        cases=cases,
        run_env=run_env,
        max_workers=max(1, int(args.max_workers)),
        dry_run=bool(args.dry_run),
        summary_csv=summary_csv,
    )


if __name__ == "__main__":
    raise SystemExit(main())

