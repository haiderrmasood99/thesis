from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parent
FIG_DIR = ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_exports() -> tuple[pd.DataFrame, pd.DataFrame]:
    files = sorted(ROOT.glob("wandb_export_*.csv"))
    if len(files) < 2:
        raise FileNotFoundError("Expected at least two wandb_export_*.csv files in wandb exports.")

    dfs = [pd.read_csv(f) for f in files]
    fert = None
    crop = None
    for df in dfs:
        if "nonadaptive" in df.columns and "total_years" in df.columns:
            fert = df.copy()
        elif "non_adaptive" in df.columns and "eval_det/mean_reward" in df.columns:
            crop = df.copy()

    if fert is None or crop is None:
        # fallback by size heuristic
        dfs_sorted = sorted(dfs, key=len, reverse=True)
        fert = fert if fert is not None else dfs_sorted[0].copy()
        crop = crop if crop is not None else dfs_sorted[-1].copy()

    return fert, crop


def _as_bool_label(series: pd.Series, true_label: str, false_label: str) -> pd.Series:
    s = series.astype(str).str.strip().str.lower()
    return s.map({"true": true_label, "false": false_label}).fillna("unknown")


def _save(fig_name: str):
    out = FIG_DIR / fig_name
    plt.tight_layout()
    plt.savefig(out, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"saved: {out}")


def _prep_fertilization(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["method"] = d["method"].astype(str)
    d["State"] = d["State"].astype(str)
    d["fixed_weather_label"] = _as_bool_label(d["fixed_weather"], "fixed_weather", "random_weather")
    d["adaptive_label"] = _as_bool_label(d["nonadaptive"], "nonadaptive", "adaptive")
    d["seed_num"] = pd.to_numeric(d["seed"], errors="coerce")
    d["total_years_num"] = pd.to_numeric(d["total_years"], errors="coerce")

    for col in [
        "eval_test_det/mean_reward",
        "eval_test_sto/mean_reward",
        "deterministic_return",
        "stochastic_return_mean",
        "pak_holdout_return",
    ]:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")
    return d


def _prep_crop(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["method"] = d["method"].astype(str)
    d["State"] = d["State"].astype(str)
    d["fixed_weather_label"] = _as_bool_label(d["fixed_weather"], "fixed_weather", "random_weather")
    d["adaptive_label"] = _as_bool_label(d["non_adaptive"], "nonadaptive", "adaptive")
    d["seed_num"] = pd.to_numeric(d["seed"], errors="coerce")

    metric_cols = [c for c in d.columns if "mean_reward" in c]
    for col in metric_cols:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    return d


def fertilization_figures(df: pd.DataFrame):
    d = _prep_fertilization(df)
    finished = d[d["State"] == "finished"].copy()

    plt.figure(figsize=(8, 4))
    sns.countplot(data=d, x="State", order=d["State"].value_counts().index, palette="Set2")
    plt.title("Fertilization Runs by State")
    plt.xlabel("Run State")
    plt.ylabel("Count")
    _save("fert_01_run_state_counts.png")

    plt.figure(figsize=(9, 5))
    sns.countplot(data=d, x="method", hue="State", palette="tab20")
    plt.title("Fertilization: Method vs Run State")
    plt.xlabel("Method")
    plt.ylabel("Count")
    _save("fert_02_method_state_counts.png")

    if "eval_test_det/mean_reward" in finished.columns:
        plt.figure(figsize=(9, 5))
        sns.boxplot(data=finished, x="method", y="eval_test_det/mean_reward", palette="Set3")
        sns.stripplot(data=finished, x="method", y="eval_test_det/mean_reward", color="black", alpha=0.5, size=3)
        plt.title("Fertilization: Eval Test Deterministic Reward by Method (Finished Runs)")
        plt.xlabel("Method")
        plt.ylabel("eval_test_det/mean_reward")
        _save("fert_03_eval_test_det_by_method.png")

    agg = (
        finished.groupby(["adaptive_label", "fixed_weather_label"], dropna=False)["eval_test_det/mean_reward"]
        .mean()
        .unstack()
    )
    if not agg.empty:
        plt.figure(figsize=(7, 4))
        sns.heatmap(agg, annot=True, fmt=".2f", cmap="YlGnBu")
        plt.title("Fertilization: Mean Eval Test Deterministic Reward\nAdaptive Mode vs Weather Mode")
        plt.xlabel("Weather Mode")
        plt.ylabel("Policy Mode")
        _save("fert_04_adaptive_weather_heatmap.png")

    ppo = finished[finished["method"] == "PPO"].copy()
    if not ppo.empty:
        plt.figure(figsize=(10, 5))
        sns.lineplot(
            data=ppo,
            x="total_years_num",
            y="eval_test_det/mean_reward",
            hue="fixed_weather_label",
            style="adaptive_label",
            markers=True,
            dashes=False,
            estimator="mean",
            errorbar="sd",
        )
        plt.title("Fertilization PPO: Budget Trend (total_years) vs Eval Test Deterministic Reward")
        plt.xlabel("total_years")
        plt.ylabel("eval_test_det/mean_reward")
        _save("fert_05_ppo_budget_trend.png")

    hold = finished.dropna(subset=["pak_holdout_return", "eval_test_det/mean_reward"]).copy()
    if not hold.empty:
        plt.figure(figsize=(8, 5))
        sns.scatterplot(
            data=hold,
            x="eval_test_det/mean_reward",
            y="pak_holdout_return",
            hue="adaptive_label",
            style="fixed_weather_label",
            size="total_years_num",
            sizes=(30, 220),
            alpha=0.85,
        )
        plt.title("Fertilization: In-Sample vs Pakistan Holdout Performance")
        plt.xlabel("eval_test_det/mean_reward")
        plt.ylabel("pak_holdout_return")
        _save("fert_06_insample_vs_holdout.png")

    summary_cols = [
        "Name",
        "State",
        "method",
        "adaptive_label",
        "fixed_weather_label",
        "seed_num",
        "total_years_num",
        "eval_test_det/mean_reward",
        "eval_test_sto/mean_reward",
        "pak_holdout_return",
    ]
    avail = [c for c in summary_cols if c in d.columns]
    d[avail].to_csv(FIG_DIR / "fertilization_cleaned_summary.csv", index=False)
    print(f"saved: {FIG_DIR / 'fertilization_cleaned_summary.csv'}")


def crop_figures(df: pd.DataFrame):
    d = _prep_crop(df)
    finished = d[d["State"] == "finished"].copy()

    plt.figure(figsize=(8, 4))
    sns.countplot(data=d, x="State", order=d["State"].value_counts().index, palette="Set2")
    plt.title("Crop Planning Runs by State")
    plt.xlabel("Run State")
    plt.ylabel("Count")
    _save("crop_01_run_state_counts.png")

    plt.figure(figsize=(9, 5))
    sns.countplot(data=d, x="method", hue="State", palette="tab20")
    plt.title("Crop Planning: Method vs Run State")
    plt.xlabel("Method")
    plt.ylabel("Count")
    _save("crop_02_method_state_counts.png")

    if "eval_det/mean_reward" in finished.columns:
        plt.figure(figsize=(9, 5))
        sns.barplot(
            data=finished,
            x="method",
            y="eval_det/mean_reward",
            hue="fixed_weather_label",
            estimator="mean",
            errorbar="sd",
            palette="Set1",
        )
        plt.title("Crop Planning: Eval Deterministic Mean Reward by Method and Weather")
        plt.xlabel("Method")
        plt.ylabel("eval_det/mean_reward")
        _save("crop_03_eval_det_by_method_weather.png")

    agg = (
        finished.groupby(["adaptive_label", "fixed_weather_label"], dropna=False)["eval_det/mean_reward"]
        .mean()
        .unstack()
    )
    if not agg.empty:
        plt.figure(figsize=(7, 4))
        sns.heatmap(agg, annot=True, fmt=".2f", cmap="OrRd")
        plt.title("Crop Planning: Mean Eval Deterministic Reward\nAdaptive Mode vs Weather Mode")
        plt.xlabel("Weather Mode")
        plt.ylabel("Policy Mode")
        _save("crop_04_adaptive_weather_heatmap.png")

    eval_cols = [
        "eval_det/mean_reward",
        "eval_sto/mean_reward",
        "eval_det_new_years/mean_reward",
        "eval_sto_new_years/mean_reward",
        "eval_det_other_loc/mean_reward",
        "eval_sto_other_loc/mean_reward",
    ]
    available = [c for c in eval_cols if c in finished.columns]
    if available:
        long_df = finished.melt(
            id_vars=["method", "adaptive_label", "fixed_weather_label", "Name"],
            value_vars=available,
            var_name="metric",
            value_name="value",
        ).dropna(subset=["value"])
        plt.figure(figsize=(12, 5))
        sns.barplot(
            data=long_df,
            x="metric",
            y="value",
            hue="method",
            estimator="mean",
            errorbar=None,
            palette="Dark2",
        )
        plt.title("Crop Planning: Evaluation Metric Comparison by Method")
        plt.xlabel("Metric")
        plt.ylabel("Mean reward")
        plt.xticks(rotation=35, ha="right")
        _save("crop_05_eval_metric_comparison.png")

    summary_cols = [
        "Name",
        "State",
        "method",
        "adaptive_label",
        "fixed_weather_label",
        "seed_num",
        "eval_det/mean_reward",
        "eval_sto/mean_reward",
        "eval_det_new_years/mean_reward",
        "eval_sto_new_years/mean_reward",
    ]
    avail = [c for c in summary_cols if c in d.columns]
    d[avail].to_csv(FIG_DIR / "crop_planning_cleaned_summary.csv", index=False)
    print(f"saved: {FIG_DIR / 'crop_planning_cleaned_summary.csv'}")


def main():
    sns.set_theme(style="whitegrid")
    fert, crop = _load_exports()
    fertilization_figures(fert)
    crop_figures(crop)
    print(f"\nAll figures saved to: {FIG_DIR}")


if __name__ == "__main__":
    main()
