from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
import faulthandler
from pathlib import Path


def _load_presets_from_json() -> list[str]:
    preset_file = Path(__file__).resolve().parent / "model_presets.json"
    data = json.loads(preset_file.read_text(encoding="utf-8"))
    return [p["id"] for p in data.get("presets", []) if p.get("domain") == "fertilization"]


def _append_trace_line(trace_file: Path, message: str):
    trace_file.parent.mkdir(parents=True, exist_ok=True)
    with trace_file.open("a", encoding="utf-8") as f:
        f.write(message + "\n")
        f.flush()
        os.fsync(f.fileno())


def _parse_weather_mode(value: str):
    v = value.strip().lower()
    if v == "default":
        return None
    if v == "fixed":
        return True
    if v == "random":
        return False
    raise ValueError("--weather-mode must be one of: default, fixed, random")


def _result_to_dict(result) -> dict:
    return {
        "preset_id": result.preset_id,
        "run_dir": result.run_dir,
        "model_path": result.model_path,
        "method": result.method,
        "used_config": result.used_config,
        "episode_summaries": result.episode_summaries,
        "first_episode_actions_kg": result.first_episode_actions_kg,
        "first_episode_rewards": result.first_episode_rewards,
        "mean_total_reward": result.mean_total_reward,
        "mean_total_n_kg": result.mean_total_n_kg,
    }


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    trace_file = script_dir / "output" / "cli_trace.log"
    _append_trace_line(trace_file, "[CLI] main() start")
    try:
        fh = trace_file.open("a", encoding="utf-8")
        faulthandler.enable(file=fh, all_threads=True)
        _append_trace_line(trace_file, "[CLI] faulthandler enabled")
    except Exception:
        fh = None

    preset_choices = _load_presets_from_json()

    parser = argparse.ArgumentParser(description="Run fertilization demo inference from a preset model.")
    parser.add_argument("--preset", required=True, choices=preset_choices, help="Preset model id.")
    parser.add_argument("--episodes", type=int, default=3, help="Number of episodes to run.")
    parser.add_argument("--deterministic", action="store_true", help="Use deterministic policy actions.")
    parser.add_argument("--stochastic", action="store_true", help="Use stochastic policy actions.")
    parser.add_argument("--start-year", type=int, default=None, help="Override simulation start year.")
    parser.add_argument("--end-year", type=int, default=None, help="Override simulation end year.")
    parser.add_argument(
        "--weather-mode",
        default="default",
        choices=["default", "fixed", "random"],
        help="Override weather mode: default uses run config.",
    )
    parser.add_argument("--trace", action="store_true", help="Enable detailed stage tracing.")
    parser.add_argument("--output", default="demo/output/latest_inference.json", help="Output JSON file path.")
    args = parser.parse_args()
    print("[INFO] Starting demo inference CLI...", flush=True)
    _append_trace_line(trace_file, f"[CLI] args parsed preset={args.preset} episodes={args.episodes}")

    if args.deterministic and args.stochastic:
        raise ValueError("Use only one of --deterministic or --stochastic.")

    deterministic = True
    if args.stochastic:
        deterministic = False
    elif args.deterministic:
        deterministic = True

    fixed_weather_override = _parse_weather_mode(args.weather_mode)

    try:
        from inference_engine import run_fertilization_inference
        _append_trace_line(trace_file, "[CLI] inference_engine imported")
    except ModuleNotFoundError as exc:
        missing = str(exc).split("'")[1] if "'" in str(exc) else str(exc)
        raise ModuleNotFoundError(
            f"Missing dependency: {missing}. Install demo requirements with: pip install -r demo/requirements.txt"
        ) from exc

    try:
        print("[INFO] Loading preset and running inference...", flush=True)
        _append_trace_line(trace_file, "[CLI] entering run_fertilization_inference")
        result = run_fertilization_inference(
            preset_id=args.preset,
            episodes=max(1, args.episodes),
            deterministic=deterministic,
            start_year=args.start_year,
            end_year=args.end_year,
            fixed_weather_override=fixed_weather_override,
            trace=True,
        )
        print("[INFO] Inference completed.", flush=True)
        _append_trace_line(trace_file, "[CLI] run_fertilization_inference completed")
    except Exception as exc:
        print(f"[ERROR] Inference failed: {type(exc).__name__}: {exc}", flush=True)
        _append_trace_line(trace_file, f"[CLI] inference failed: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return 1

    print("=== Demo Inference Summary ===", flush=True)
    print(f"Preset: {result.preset_id}", flush=True)
    print(f"Run Dir: {result.run_dir}", flush=True)
    print(f"Model: {result.model_path}", flush=True)
    print(f"Method: {result.method}", flush=True)
    print(f"Mean Total Reward: {result.mean_total_reward:.4f}", flush=True)
    print(f"Mean Total N (kg/ha): {result.mean_total_n_kg:.4f}", flush=True)
    print("Used Config:", flush=True)
    for key in sorted(result.used_config.keys()):
        print(f"  - {key}: {result.used_config[key]}", flush=True)

    print("Episode Summaries:", flush=True)
    for row in result.episode_summaries:
        print(
            f"  - Ep {row['episode']}: reward={row['total_reward']}, total_n_kg={row['total_n_kg']}, steps={row['steps']}",
            flush=True,
        )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_result_to_dict(result), indent=2), encoding="utf-8")
    print(f"Saved JSON output to: {output_path}", flush=True)
    _append_trace_line(trace_file, f"[CLI] output saved to {output_path}")
    if fh is not None:
        try:
            fh.flush()
            fh.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except KeyboardInterrupt:
        print("[ERROR] Interrupted by user.", flush=True)
        rc = 130
    except BaseException as exc:  # catches unexpected SystemExit paths too
        print(f"[FATAL] Unhandled exit: {type(exc).__name__}: {exc}", flush=True)
        traceback.print_exc()
        rc = 1
    sys.exit(rc)
