#!/usr/bin/env python3
"""Point 1: fertilization entropy-coefficient ablation (parallel launcher)."""

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
DEFAULT_BASE_OUTPUT = REPO_ROOT / "artifacts" / "final_successful_runs" / "low_hanging_ablation" / "point1_entropy_fertilization"


def build_cases(
    output_root: Path,
    py_exec: str,
    methods: list[str],
    seeds: list[int],
    weather_modes: list[bool],
    ent_coefs: list[float],
    include_nonadaptive: bool,
    total_years: int,
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
) -> list[AblationCase]:
    cases: list[AblationCase] = []
    adaptive_modes = [False, True] if include_nonadaptive else [False]
    case_index = 0

    for method in methods:
        for seed in seeds:
            for fixed_weather in weather_modes:
                for nonadaptive in adaptive_modes:
                    for ent_coef in ent_coefs:
                        case_index += 1
                        weather_label = "fixed_weather" if fixed_weather else "random_weather"
                        adaptive_label = "nonadaptive" if nonadaptive else "adaptive"
                        ent_label = slugify(f"{ent_coef:.6f}".rstrip("0").rstrip("."))
                        slug = (
                            f"p1_{method.lower()}_{adaptive_label}_{weather_label}_"
                            f"seed{seed}_ent{ent_label}"
                        )

                        summary_json = output_root / "summary_json" / f"{slug}.json"
                        case_log = output_root / "logs" / f"{slug}.log"
                        cmd = [
                            py_exec,
                            "experiments/fertilization/train.py",
                            "--method",
                            method,
                            "--seed",
                            str(seed),
                            "--total-years",
                            str(total_years),
                            "--n-process",
                            str(n_process),
                            "--eval-freq",
                            str(eval_freq),
                            "--ent-coef",
                            str(ent_coef),
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
                            "--summary-json",
                            str(summary_json),
                        ]
                        if fixed_weather:
                            cmd.append("--fixed-weather")
                        if nonadaptive:
                            cmd.append("--nonadaptive")
                        if without_tracking:
                            cmd.append("--without-tracking")

                        label = (
                            f"Point1 Entropy | {method} | {adaptive_label} | {weather_label} | "
                            f"seed={seed} | ent_coef={ent_coef}"
                        )
                        cases.append(
                            AblationCase(
                                case_id=f"{case_index:03d}",
                                label=label,
                                cmd=cmd,
                                summary_json=summary_json,
                                case_log=case_log,
                                metadata={
                                    "point": "point1_entropy",
                                    "domain": "fertilization",
                                    "method": method,
                                    "seed": seed,
                                    "fixed_weather": fixed_weather,
                                    "nonadaptive": nonadaptive,
                                    "ent_coef": ent_coef,
                                    "total_years": total_years,
                                    "nutrient_action_mode": nutrient_action_mode,
                                },
                            )
                        )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Point-1 entropy ablation in parallel.")
    parser.add_argument("--methods", default="PPO", help="Comma-separated methods (PPO,A2C,DQN).")
    parser.add_argument("--seeds", default="0,1,2", help="Comma-separated seeds.")
    parser.add_argument("--weather-modes", default="fixed,random", help="Comma-separated weather modes.")
    parser.add_argument("--ent-coefs", default="0.0,0.01", help="Comma-separated entropy coefficients.")
    parser.add_argument("--include-nonadaptive", action="store_true", help="Also run nonadaptive policy rows.")
    parser.add_argument("--total-years", type=int, default=1000, help="Fertilization training horizon (years).")
    parser.add_argument("--n-process", type=int, default=4, help="Vec env process count per training run.")
    parser.add_argument("--eval-freq", type=int, default=20000, help="Eval frequency for fertilization runs.")
    parser.add_argument("--nutrient-action-mode", type=str.upper, default="NPK", choices=["N", "NPK"])
    parser.add_argument("--price-profile", default="pakistan_baseline")
    parser.add_argument("--maxN", type=float, default=150.0)
    parser.add_argument("--maxP", type=float, default=80.0)
    parser.add_argument("--maxK", type=float, default=60.0)
    parser.add_argument("--p-actions", type=int, default=11)
    parser.add_argument("--k-actions", type=int, default=11)
    parser.add_argument("--n-nh4-rate", type=float, default=0.75)
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
    ent_coefs = parse_float_list(args.ent_coefs)

    run_tag = args.run_tag or timestamp_tag()
    output_root = Path(args.output_root) if args.output_root else DEFAULT_BASE_OUTPUT / run_tag
    output_root.mkdir(parents=True, exist_ok=True)

    cases = build_cases(
        output_root=output_root,
        py_exec=sys.executable,
        methods=methods,
        seeds=seeds,
        weather_modes=weather_modes,
        ent_coefs=ent_coefs,
        include_nonadaptive=bool(args.include_nonadaptive),
        total_years=int(args.total_years),
        n_process=int(args.n_process),
        eval_freq=int(args.eval_freq),
        nutrient_action_mode=args.nutrient_action_mode,
        price_profile=args.price_profile,
        maxN=float(args.maxN),
        maxP=float(args.maxP),
        maxK=float(args.maxK),
        p_actions=int(args.p_actions),
        k_actions=int(args.k_actions),
        n_nh4_rate=float(args.n_nh4_rate),
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

