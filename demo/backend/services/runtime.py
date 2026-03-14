from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
from stable_baselines3 import A2C, DQN, PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from demo.backend.config import PROJECT_ROOT
from demo.backend.services.bundles import BundleRecord, get_bundle_by_label

FERT_EXP_DIR = PROJECT_ROOT / "experiments" / "fertilization"
if str(FERT_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(FERT_EXP_DIR))

from corn_soil_refined import CornSoilCropWeatherObs  # type: ignore
from cyclesgym.envs.common import PartialObsEnv
from cyclesgym.envs.corn import Corn
from cyclesgym.envs.weather_generator import FixedWeatherGenerator, WeatherShuffler
from cyclesgym.utils.paths import CYCLES_PATH


@dataclass(frozen=True)
class NutrientVector:
    n: float
    p: float
    k: float


@dataclass(frozen=True)
class BundleRuntimeConfig:
    method: str
    observation_dim: int
    start_year: int
    end_year: int
    sampling_start_year: int
    sampling_end_year: int
    fixed_weather: bool
    nonadaptive: bool
    soil_env: bool
    with_obs_year: bool
    nutrient_action_mode: str
    n_actions: int
    p_actions: int
    k_actions: int
    maxN: float
    maxP: float
    maxK: float
    price_profile: str


@dataclass(frozen=True)
class EpisodeStep:
    week_number: int
    action: NutrientVector
    reward: float


@dataclass(frozen=True)
class EpisodeResult:
    bundle_label: str
    method: str
    steps: tuple[EpisodeStep, ...]
    total_reward: float
    stats_loaded: bool


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return default


def _to_int(value: Any, default: int) -> int:
    try:
        return int(float(str(value).strip()))
    except Exception:
        return default


def _to_float(value: Any, default: float) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return default


def _parse_wandb_config_yaml(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    values: dict[str, str] = {}
    for match in re.finditer(r"(?m)^([A-Za-z0-9_./-]+):\n\s+value:\s*(.+)$", text):
        key = match.group(1).strip()
        value = match.group(2).strip().strip('"').strip("'")
        values[key] = value
    return values


def build_runtime_config(bundle: BundleRecord) -> BundleRuntimeConfig:
    config = _parse_wandb_config_yaml(bundle.config_path)
    observation_match = re.search(r"\((\d+),\)", config.get("observation_space", ""))
    observation_dim = int(observation_match.group(1)) if observation_match else 0
    raw_with_obs_year = _to_bool(config.get("with_obs_year"), default=True)
    inferred_with_obs_year = raw_with_obs_year
    if observation_dim in {14, 2}:
        inferred_with_obs_year = False
    elif observation_dim in {15, 3}:
        inferred_with_obs_year = True
    return BundleRuntimeConfig(
        method=config.get("method", config.get("algo", bundle.method)),
        observation_dim=observation_dim,
        start_year=_to_int(config.get("start_year"), 2005),
        end_year=_to_int(config.get("end_year"), 2005),
        sampling_start_year=_to_int(config.get("sampling_start_year"), 2005),
        sampling_end_year=_to_int(config.get("sampling_end_year"), 2023),
        fixed_weather=_to_bool(config.get("fixed_weather"), default=False),
        nonadaptive=_to_bool(config.get("nonadaptive"), default=False),
        soil_env=_to_bool(config.get("soil_env"), default=True),
        with_obs_year=inferred_with_obs_year,
        nutrient_action_mode=str(config.get("nutrient_action_mode", "N")).upper(),
        n_actions=_to_int(config.get("n_actions", config.get("fert_n_actions")), 11),
        p_actions=_to_int(config.get("p_actions"), 11),
        k_actions=_to_int(config.get("k_actions"), 11),
        maxN=_to_float(config.get("maxN"), 150.0),
        maxP=_to_float(config.get("maxP"), 80.0),
        maxK=_to_float(config.get("maxK"), 60.0),
        price_profile=str(config.get("price_profile", "pakistan_baseline")),
    )


def decode_action_to_amounts(
    action: np.ndarray | list[int] | tuple[int, ...],
    config: BundleRuntimeConfig,
) -> NutrientVector:
    flat = np.asarray(action).reshape(-1)
    if config.nutrient_action_mode == "NPK":
        n_idx = int(flat[0]) if flat.size > 0 else 0
        p_idx = int(flat[1]) if flat.size > 1 else 0
        k_idx = int(flat[2]) if flat.size > 2 else 0
        n_denom = max(config.n_actions - 1, 1)
        p_denom = max(config.p_actions - 1, 1)
        k_denom = max(config.k_actions - 1, 1)
        return NutrientVector(
            n=config.maxN * n_idx / n_denom,
            p=config.maxP * p_idx / p_denom,
            k=config.maxK * k_idx / k_denom,
        )

    n_idx = int(flat[0]) if flat.size > 0 else 0
    n_denom = max(config.n_actions - 1, 1)
    return NutrientVector(n=config.maxN * n_idx / n_denom, p=0.0, k=0.0)


def _load_model(method: str, model_path: Path, env: DummyVecEnv | VecNormalize):
    method_upper = str(method).upper()
    loaders = {
        "PPO": PPO.load,
        "A2C": A2C.load,
        "DQN": DQN.load,
    }
    if method_upper not in loaders:
        raise ValueError(f"Unsupported method: {method}")
    loader = loaders[method_upper]
    custom_objects = {
        "ep_info_buffer": None,
        # These schedule helpers are only needed for training state restore.
        "clip_range": lambda _progress: 0.2,
        "lr_schedule": lambda _progress: 0.0,
    }
    try:
        return loader(str(model_path), env=env, device="cpu", custom_objects=custom_objects)
    except ModuleNotFoundError as exc:
        if "numpy._core" in str(exc):
            import numpy.core as numpy_core

            sys.modules.setdefault("numpy._core", numpy_core)
            sys.modules.setdefault("numpy._core.numeric", numpy_core.numeric)
            return loader(str(model_path), env=env, device="cpu", custom_objects=custom_objects)
        raise


def _load_vecnormalize_compat(stats_path: Path, vec_env: DummyVecEnv):
    try:
        return VecNormalize.load(str(stats_path), vec_env)
    except ModuleNotFoundError as exc:
        if "numpy._core" in str(exc):
            import numpy.core as numpy_core

            sys.modules.setdefault("numpy._core", numpy_core)
            return VecNormalize.load(str(stats_path), vec_env)
        raise


def _build_masked_soil_env(config: BundleRuntimeConfig):
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
    target_obs_nonadaptive = ["Y", "DOY", "N TO DATE"]

    if config.fixed_weather:
        weather_generator_class = FixedWeatherGenerator
        weather_generator_kwargs = {
            "base_weather_file": CYCLES_PATH.joinpath("input", "Pakistan_Site_final.weather")
        }
    else:
        weather_generator_class = WeatherShuffler
        weather_generator_kwargs = dict(
            n_weather_samples=100,
            sampling_start_year=config.sampling_start_year,
            sampling_end_year=config.sampling_end_year,
            target_year_range=np.arange(config.start_year, config.end_year + 1),
            base_weather_file=CYCLES_PATH.joinpath("input", "Pakistan_Site_final.weather"),
        )

    full_env = CornSoilCropWeatherObs(
        delta=7,
        n_actions=config.n_actions,
        maxN=config.maxN,
        nutrient_action_mode=config.nutrient_action_mode,
        maxP=config.maxP,
        maxK=config.maxK,
        p_actions=config.p_actions,
        k_actions=config.k_actions,
        price_profile=config.price_profile,
        start_year=config.start_year,
        end_year=config.end_year,
        use_reinit=False,
        with_obs_year=config.with_obs_year,
        weather_generator_class=weather_generator_class,
        weather_generator_kwargs=weather_generator_kwargs,
    )
    full_env.reset()
    obs_names = np.asarray(full_env.observer.obs_names)
    target = target_obs_nonadaptive if config.nonadaptive else target_obs_adaptive
    mask = np.isin(obs_names, target)
    return PartialObsEnv(full_env, mask=mask)


def _build_plain_corn_env(config: BundleRuntimeConfig):
    if config.fixed_weather:
        return Corn(
            delta=7,
            n_actions=config.n_actions,
            maxN=config.maxN,
            nutrient_action_mode=config.nutrient_action_mode,
            maxP=config.maxP,
            maxK=config.maxK,
            p_actions=config.p_actions,
            k_actions=config.k_actions,
            price_profile=config.price_profile,
            start_year=config.start_year,
            end_year=config.end_year,
            use_reinit=False,
        )

    weather_generator_kwargs = dict(
        n_weather_samples=100,
        sampling_start_year=config.sampling_start_year,
        sampling_end_year=config.sampling_end_year,
        target_year_range=np.arange(config.start_year, config.end_year + 1),
        base_weather_file=CYCLES_PATH.joinpath("input", "Pakistan_Site_final.weather"),
    )
    return Corn(
        delta=7,
        n_actions=config.n_actions,
        maxN=config.maxN,
        nutrient_action_mode=config.nutrient_action_mode,
        maxP=config.maxP,
        maxK=config.maxK,
        p_actions=config.p_actions,
        k_actions=config.k_actions,
        price_profile=config.price_profile,
        start_year=config.start_year,
        end_year=config.end_year,
        use_reinit=False,
        weather_generator_class=WeatherShuffler,
        weather_generator_kwargs=weather_generator_kwargs,
    )


def _build_fertilization_vec_env(
    bundle: BundleRecord,
    config: BundleRuntimeConfig,
) -> tuple[DummyVecEnv | VecNormalize, bool]:
    def make_env():
        env = _build_masked_soil_env(config) if config.soil_env else _build_plain_corn_env(config)
        return gym.wrappers.RecordEpisodeStatistics(env)

    vec_env = DummyVecEnv([make_env])
    stats_loaded = False
    if bundle.stats_path and bundle.stats_path.exists():
        try:
            vec_env = _load_vecnormalize_compat(bundle.stats_path, vec_env)
            vec_env.training = False
            vec_env.norm_reward = False
            stats_loaded = True
        except Exception:
            stats_loaded = False
    return vec_env, stats_loaded


def _build_fertilization_env(config: BundleRuntimeConfig):
    base_env = _build_masked_soil_env(config) if config.soil_env else _build_plain_corn_env(config)
    return gym.wrappers.RecordEpisodeStatistics(base_env)


def _run_plain_fertilization_episode(
    bundle: BundleRecord,
    config: BundleRuntimeConfig,
    deterministic: bool,
) -> EpisodeResult:
    env = _build_fertilization_env(config)
    try:
        reset_result = env.reset()
        if isinstance(reset_result, tuple):
            obs, _info = reset_result
        else:
            obs = reset_result

        model = _load_model(config.method, bundle.model_path, env)

        done = False
        total_reward = 0.0
        step_counter = 0
        steps: list[EpisodeStep] = []

        while not done and step_counter < 80:
            action, _ = model.predict(obs, deterministic=deterministic)
            step_result = env.step(action)
            if len(step_result) == 5:
                obs, reward, terminated, truncated, _info = step_result
                done = bool(terminated or truncated)
            else:
                obs, reward, done, _info = step_result
            step_counter += 1
            reward_value = float(reward)
            total_reward += reward_value
            steps.append(
                EpisodeStep(
                    week_number=step_counter,
                    action=decode_action_to_amounts(action, config),
                    reward=reward_value,
                )
            )
    finally:
        env.close()

    return EpisodeResult(
        bundle_label=bundle.label,
        method=config.method,
        steps=tuple(steps),
        total_reward=total_reward,
        stats_loaded=False,
    )


@lru_cache(maxsize=6)
def run_cached_fertilization_episode(
    bundle_label: str,
    deterministic: bool = True,
) -> EpisodeResult:
    bundle = get_bundle_by_label(bundle_label)
    config = build_runtime_config(bundle)
    # Saved SB3 metadata and VecNormalize pickles are not fully portable back to
    # the repo's legacy Python 3.8 environment. Use a plain-env rollout there.
    if sys.version_info < (3, 10):
        return _run_plain_fertilization_episode(bundle, config, deterministic)

    vec_env, stats_loaded = _build_fertilization_vec_env(bundle, config)
    try:
        model = _load_model(config.method, bundle.model_path, vec_env)

        obs = vec_env.reset()
        done = False
        total_reward = 0.0
        step_counter = 0
        steps: list[EpisodeStep] = []

        while not done and step_counter < 80:
            action, _ = model.predict(obs, deterministic=deterministic)
            obs, rewards, dones, _infos = vec_env.step(action)
            total_reward += float(np.asarray(rewards).reshape(-1)[0])
            done = bool(np.asarray(dones).reshape(-1)[0])
            step_counter += 1
            steps.append(
                EpisodeStep(
                    week_number=step_counter,
                    action=decode_action_to_amounts(action, config),
                    reward=float(np.asarray(rewards).reshape(-1)[0]),
                )
            )
    finally:
        vec_env.close()

    return EpisodeResult(
        bundle_label=bundle.label,
        method=config.method,
        steps=tuple(steps),
        total_reward=total_reward,
        stats_loaded=stats_loaded,
    )


def load_bundle_summary(bundle: BundleRecord) -> dict[str, Any]:
    if not bundle.summary_path or not bundle.summary_path.exists():
        return {}
    return json.loads(bundle.summary_path.read_text(encoding="utf-8"))
