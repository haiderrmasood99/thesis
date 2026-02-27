from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
from stable_baselines3 import A2C, DQN, PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = Path(__file__).resolve().parent

FERT_EXP_DIR = ROOT / "experiments" / "fertilization"
if str(FERT_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(FERT_EXP_DIR))

from corn_soil_refined import CornSoilCropWeatherObs  # type: ignore
from cyclesgym.envs.common import PartialObsEnv
from cyclesgym.envs.corn import Corn
from cyclesgym.envs.weather_generator import FixedWeatherGenerator, WeatherShuffler
from cyclesgym.utils.paths import CYCLES_PATH


@dataclass
class InferenceResult:
    preset_id: str
    run_dir: str
    model_path: str
    method: str
    used_config: dict[str, Any]
    episode_summaries: list[dict[str, Any]]
    first_episode_actions_kg: list[float]
    first_episode_rewards: list[float]
    mean_total_reward: float
    mean_total_n_kg: float


def _trace(msg: str, enabled: bool = False):
    if not enabled:
        return
    out_dir = DEMO_DIR / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(f"[TRACE] {msg}", flush=True)
    with (out_dir / "inference_trace.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    s = str(value).strip().lower()
    if s in {"true", "1", "yes", "y"}:
        return True
    if s in {"false", "0", "no", "n"}:
        return False
    return default


def _to_int(value: Any, default: int) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _parse_wandb_config_yaml(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    values: dict[str, str] = {}

    for match in re.finditer(r"(?m)^([A-Za-z0-9_./-]+):\n\s+value:\s*(.+)$", text):
        key = match.group(1).strip()
        value = match.group(2).strip().strip('"').strip("'")
        values[key] = value

    code_path_match = re.search(r"codePath:\s*(experiments/[A-Za-z0-9_./-]+)", text)
    if code_path_match:
        values["codePath"] = code_path_match.group(1)

    return values


def load_presets() -> list[dict[str, Any]]:
    preset_file = DEMO_DIR / "model_presets.json"
    data = json.loads(preset_file.read_text(encoding="utf-8"))
    return data.get("presets", [])


def get_preset(preset_id: str) -> dict[str, Any]:
    for preset in load_presets():
        if preset["id"] == preset_id:
            return preset
    raise ValueError(f"Unknown preset_id: {preset_id}")


def list_fertilization_presets() -> list[dict[str, Any]]:
    return [p for p in load_presets() if p.get("domain") == "fertilization"]


def _resolve_config_and_model(preset: dict[str, Any]) -> tuple[Path, Path]:
    run_dir = preset["run_dir"]
    model_rel = preset["model_path"]

    config_path = ROOT / "wandb" / run_dir / "files" / "config.yaml"
    model_path = ROOT / model_rel

    if not config_path.exists():
        raise FileNotFoundError(f"Missing config.yaml for preset {preset['id']}: {config_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Missing model.zip for preset {preset['id']}: {model_path}")

    return config_path, model_path


def get_preset_runtime_info(preset_id: str) -> dict[str, Any]:
    preset = get_preset(preset_id)
    config_path, model_path = _resolve_config_and_model(preset)
    config = _parse_wandb_config_yaml(config_path)

    info = {
        "preset_id": preset["id"],
        "title": preset.get("title", preset["id"]),
        "notes": preset.get("notes", ""),
        "run_dir": preset["run_dir"],
        "model_path": str(model_path),
        "method": config.get("method", config.get("algo", "PPO")),
        "fixed_weather_default": _to_bool(config.get("fixed_weather"), default=False),
        "nonadaptive_default": _to_bool(config.get("nonadaptive"), default=False),
        "start_year_default": _to_int(config.get("start_year"), 2005),
        "end_year_default": _to_int(config.get("end_year"), 2005),
        "sampling_start_year_default": _to_int(config.get("sampling_start_year"), 2005),
        "sampling_end_year_default": _to_int(config.get("sampling_end_year"), 2018),
        "stats_path": config.get("stats_path", ""),
    }
    return info


def _load_model(method: str, model_path: Path, env: DummyVecEnv | VecNormalize):
    method_upper = str(method).upper()
    if method_upper == "PPO":
        return PPO.load(str(model_path), env=env, device="cpu")
    if method_upper == "A2C":
        return A2C.load(str(model_path), env=env, device="cpu")
    if method_upper == "DQN":
        return DQN.load(str(model_path), env=env, device="cpu")
    raise ValueError(f"Unsupported method: {method}")


def _load_vecnormalize_compat(stats_path: Path, vec_env: DummyVecEnv):
    """
    Load VecNormalize stats with compatibility shims for NumPy pickle paths.
    Some stats files were pickled in environments referencing `numpy._core`,
    which fails to import under older NumPy versions that expose `numpy.core`.
    """
    try:
        return VecNormalize.load(str(stats_path), vec_env)
    except ModuleNotFoundError as exc:
        # Compatibility for pickles that reference numpy._core
        if "numpy._core" in str(exc):
            try:
                import numpy.core as _np_core

                sys.modules.setdefault("numpy._core", _np_core)
                return VecNormalize.load(str(stats_path), vec_env)
            except Exception:
                raise
        raise


def _clamp_year(year: int) -> int:
    return max(2005, min(2019, year))


def _build_fertilization_vec_env(
    run_config: dict[str, str],
    start_year: int | None,
    end_year: int | None,
    fixed_weather_override: bool | None,
):
    method_nonadaptive = _to_bool(run_config.get("nonadaptive"), default=False)
    soil_env = _to_bool(run_config.get("soil_env"), default=True)
    with_obs_year = _to_bool(run_config.get("with_obs_year"), default=True)
    n_actions = _to_int(run_config.get("n_actions"), 11)
    n_weather_samples = _to_int(run_config.get("n_weather_samples"), 100)

    run_start_year = _to_int(run_config.get("start_year"), 2005)
    run_end_year = _to_int(run_config.get("end_year"), 2005)
    run_sampling_start = _to_int(run_config.get("sampling_start_year"), 2005)
    run_sampling_end = _to_int(run_config.get("sampling_end_year"), 2018)
    run_fixed_weather = _to_bool(run_config.get("fixed_weather"), default=False)

    sy = _clamp_year(start_year if start_year is not None else run_start_year)
    ey = _clamp_year(end_year if end_year is not None else run_end_year)
    if ey < sy:
        ey = sy

    sampling_start = max(2005, min(2019, run_sampling_start))
    sampling_end = max(sampling_start, min(2019, run_sampling_end))
    fixed_weather = run_fixed_weather if fixed_weather_override is None else fixed_weather_override

    def make_env():
        if soil_env:
            target_obs_adaptive = [
                "PP",
                "TX",
                "TN",
                "SOLAR",
                "RHX",
                "RHN",
                "STAGE",
                "CUM. BIOMASS",
                "N STRESS",
                "WATER STRESS",
                "ORG SOIL N",
                "PROF SOIL NO3",
                "PROF SOIL NH4",
                "Y",
                "DOY",
            ]
            target_obs_nonadaptive = [
                "Y",
                "DOY",
                "N TO DATE",
            ]

            if fixed_weather:
                weather_generator_class = FixedWeatherGenerator
                weather_generator_kwargs = {
                    "base_weather_file": CYCLES_PATH.joinpath("input", "Pakistan_Site_final.weather")
                }
            else:
                weather_generator_class = WeatherShuffler
                weather_generator_kwargs = dict(
                    n_weather_samples=n_weather_samples,
                    sampling_start_year=sampling_start,
                    sampling_end_year=sampling_end,
                    target_year_range=np.arange(sy, ey + 1),
                    base_weather_file=CYCLES_PATH.joinpath("input", "Pakistan_Site_final.weather"),
                )

            # Build only one underlying env and derive mask from its own observer names.
            full_env = CornSoilCropWeatherObs(
                delta=7,
                n_actions=n_actions,
                maxN=150,
                start_year=sy,
                end_year=ey,
                with_obs_year=with_obs_year,
                weather_generator_class=weather_generator_class,
                weather_generator_kwargs=weather_generator_kwargs,
            )
            obs_names = np.asarray(full_env.observer.obs_names)
            target = target_obs_nonadaptive if method_nonadaptive else target_obs_adaptive
            mask = np.isin(obs_names, target)
            env = PartialObsEnv(full_env, mask=mask)
        else:
            if fixed_weather:
                env = Corn(
                    delta=7,
                    maxN=150,
                    n_actions=n_actions,
                    start_year=sy,
                    end_year=ey,
                )
            else:
                target_year_range = np.arange(sy, ey + 1)
                weather_generator_kwargs = dict(
                    n_weather_samples=n_weather_samples,
                    sampling_start_year=sampling_start,
                    sampling_end_year=sampling_end,
                    target_year_range=target_year_range,
                    base_weather_file=CYCLES_PATH.joinpath("input", "Pakistan_Site_final.weather"),
                )
                env = Corn(
                    delta=7,
                    maxN=150,
                    n_actions=n_actions,
                    start_year=sy,
                    end_year=ey,
                    weather_generator_class=WeatherShuffler,
                    weather_generator_kwargs=weather_generator_kwargs,
                )

        env = gym.wrappers.RecordEpisodeStatistics(env)
        return env

    vec_env = DummyVecEnv([make_env])

    stats_path_raw = run_config.get("stats_path", "")
    stats_path = (ROOT / stats_path_raw) if stats_path_raw else None
    stats_loaded = False
    if stats_path is not None and stats_path.exists():
        try:
            vec_env = _load_vecnormalize_compat(stats_path, vec_env)
            vec_env.training = False
            vec_env.norm_reward = False
            stats_loaded = True
        except Exception as exc:
            # Keep demo runnable even if stats file cannot be loaded in current env.
            # In that case we continue without normalization stats.
            stats_loaded = False
            runtime_error = f"VecNormalize load failed: {type(exc).__name__}: {exc}"
    else:
        runtime_error = ""

    runtime = {
        "start_year": sy,
        "end_year": ey,
        "sampling_start_year": sampling_start,
        "sampling_end_year": sampling_end,
        "fixed_weather": fixed_weather,
        "nonadaptive": method_nonadaptive,
        "soil_env": soil_env,
        "with_obs_year": with_obs_year,
        "n_actions": n_actions,
        "stats_loaded": stats_loaded,
        "stats_path": str(stats_path) if stats_path is not None else "",
        "stats_load_error": runtime_error if not stats_loaded else "",
    }

    return vec_env, runtime


def run_fertilization_inference(
    preset_id: str,
    episodes: int = 3,
    deterministic: bool = True,
    start_year: int | None = None,
    end_year: int | None = None,
    fixed_weather_override: bool | None = None,
    max_steps_per_episode: int = 500,
    trace: bool = False,
) -> InferenceResult:
    _trace("run_fertilization_inference: start", trace)
    preset = get_preset(preset_id)
    if preset.get("domain") != "fertilization":
        raise ValueError(f"Preset {preset_id} is not a fertilization preset.")

    config_path, model_path = _resolve_config_and_model(preset)
    _trace(f"resolved config={config_path}", trace)
    _trace(f"resolved model={model_path}", trace)
    run_cfg = _parse_wandb_config_yaml(config_path)
    _trace("parsed config", trace)
    method = run_cfg.get("method", run_cfg.get("algo", "PPO"))
    _trace(f"method={method}", trace)

    vec_env, used_config = _build_fertilization_vec_env(
        run_config=run_cfg,
        start_year=start_year,
        end_year=end_year,
        fixed_weather_override=fixed_weather_override,
    )
    _trace("built vec env", trace)
    _trace(f"used_config={used_config}", trace)

    model = _load_model(method=method, model_path=model_path, env=vec_env)
    _trace("loaded model", trace)

    max_n = 150.0
    n_actions = used_config["n_actions"]
    denom = max(n_actions - 1, 1)

    episode_summaries: list[dict[str, Any]] = []
    first_episode_actions_kg: list[float] = []
    first_episode_rewards: list[float] = []

    for episode_idx in range(episodes):
        _trace(f"episode {episode_idx + 1}: reset", trace)
        obs = vec_env.reset()
        done = False
        steps = 0
        total_reward = 0.0
        total_n_kg = 0.0
        action_trace_kg: list[float] = []
        reward_trace: list[float] = []

        while not done and steps < max_steps_per_episode:
            action, _ = model.predict(obs, deterministic=deterministic)
            obs, rewards, dones, _infos = vec_env.step(action)

            action_idx = int(np.asarray(action).reshape(-1)[0])
            applied_n_kg = max_n * action_idx / denom
            reward_value = float(np.asarray(rewards).reshape(-1)[0])
            done = bool(np.asarray(dones).reshape(-1)[0])

            action_trace_kg.append(float(applied_n_kg))
            reward_trace.append(reward_value)
            total_n_kg += float(applied_n_kg)
            total_reward += reward_value
            steps += 1
            if trace and steps % 25 == 0:
                _trace(f"episode {episode_idx + 1}: step={steps}, total_reward={total_reward:.3f}", trace)

        summary = {
            "episode": episode_idx + 1,
            "steps": steps,
            "total_reward": round(total_reward, 4),
            "total_n_kg": round(total_n_kg, 4),
            "avg_n_kg_per_step": round(total_n_kg / steps, 4) if steps > 0 else 0.0,
        }
        episode_summaries.append(summary)

        if episode_idx == 0:
            first_episode_actions_kg = action_trace_kg
            first_episode_rewards = reward_trace
        _trace(f"episode {episode_idx + 1}: done, steps={steps}, reward={total_reward:.3f}", trace)

    mean_total_reward = float(np.mean([x["total_reward"] for x in episode_summaries])) if episode_summaries else 0.0
    mean_total_n_kg = float(np.mean([x["total_n_kg"] for x in episode_summaries])) if episode_summaries else 0.0
    _trace(f"completed all episodes: mean_reward={mean_total_reward:.3f}", trace)

    return InferenceResult(
        preset_id=preset_id,
        run_dir=preset["run_dir"],
        model_path=str(model_path),
        method=method,
        used_config=used_config,
        episode_summaries=episode_summaries,
        first_episode_actions_kg=first_episode_actions_kg,
        first_episode_rewards=first_episode_rewards,
        mean_total_reward=mean_total_reward,
        mean_total_n_kg=mean_total_n_kg,
    )


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def get_experiment_artifact_rows(file_name: str) -> list[dict[str, str]]:
    path = ROOT / "Experimentation and Results" / "artifacts" / file_name
    return load_csv_rows(path)
