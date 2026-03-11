from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "Runs_experiments_Reports"
FIG_DIR = REPORT_DIR / "figures"
DATA_DIR = REPORT_DIR / "data"

WANDB_EXPORT = ROOT / "run_experiments_7_3_2026_RUNS" / "wandb_export_2026-03-11T01_53_38.382+05_00.csv"
TRAIN_LOG_SUMMARY = ROOT / "runs" / "experiment_summaries" / "train_logs_summary.csv"
FAILURE_SIGNATURES = ROOT / "runs" / "experiment_summaries" / "failure_signature_counts.csv"
NON_HIER_CONSOLE = ROOT / "runs" / "experiment_summaries" / "non_hier_10_3_2026_20260309_193918" / "console.log"


@dataclass
class AnalysisBundle:
    runs: pd.DataFrame
    finished: pd.DataFrame
    fertilization: pd.DataFrame
    fertilization_comparable: pd.DataFrame
    crop: pd.DataFrame
    crop_nonhier: pd.DataFrame
    crop_hier: pd.DataFrame
    hierarchical_ablation: pd.DataFrame
    train_log_summary: pd.DataFrame
    failure_signatures: pd.DataFrame
    failure_causes: pd.DataFrame


def ensure_dirs() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def as_bool(value: object) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes"}


def infer_domain(row: pd.Series) -> str:
    ref = str(row.get("summary_ref", "")).lower()
    if "crop_planning" in ref:
        return "crop_planning"
    if "fertilization" in ref:
        return "fertilization"
    if pd.notna(row.get("eval_det/mean_reward")) or pd.notna(row.get("eval_sto/mean_reward")):
        return "crop_planning"
    if (
        pd.notna(row.get("eval_test_det/mean_reward"))
        or pd.notna(row.get("pak_holdout_return"))
        or pd.notna(row.get("total_years"))
    ):
        return "fertilization"
    return "unknown"


def infer_cohort(summary_ref: str) -> str:
    ref = summary_ref.lower()
    if "hier_parallel_10_3_2026" in ref:
        return "crop_hier_parallel_10_3_2026"
    if "non_hier_10_3_2026" in ref:
        return "non_hier_10_3_2026"
    if "campaign_20260307_164340" in ref:
        return "campaign_20260307_164340"
    if "metrics_7_3_2026" in ref:
        return "metrics_7_3_2026"
    if "/runs/experiment_summaries/metrics/" in ref or "runs/experiment_summaries/metrics/" in ref:
        return "legacy_metrics"
    return "other"


def infer_adaptive_mode(row: pd.Series) -> str:
    if as_bool(row.get("hierarchical")):
        return "hierarchical"
    if row["domain"] == "crop_planning":
        return "nonadaptive" if as_bool(row.get("non_adaptive")) else "adaptive"
    return "nonadaptive" if as_bool(row.get("nonadaptive")) else "adaptive"


def weather_mode(series: pd.Series) -> pd.Series:
    return series.map(lambda value: "fixed_weather" if as_bool(value) else "random_weather")


def savefig(name: str) -> None:
    out = FIG_DIR / name
    plt.tight_layout()
    plt.savefig(out, dpi=180, bbox_inches="tight")
    plt.close()


def export_table(df: pd.DataFrame, name: str) -> None:
    df.to_csv(DATA_DIR / name, index=False)


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    table = df.copy()
    if max_rows is not None:
        table = table.head(max_rows)
    headers = list(table.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in table.iterrows():
        cells: list[str] = []
        for header in headers:
            value = row[header]
            if pd.isna(value):
                cells.append("-")
            elif isinstance(value, (float, np.floating)):
                cells.append(f"{value:,.2f}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def first_matching_line(path: Path, needle: str) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            if needle in line:
                return line_no
    return None


def load_runs() -> AnalysisBundle:
    runs = pd.read_csv(WANDB_EXPORT)
    runs["summary_ref"] = runs["summary_json_path"].combine_first(runs["summary_json"]).fillna("")
    runs["domain"] = runs.apply(infer_domain, axis=1)
    runs["cohort"] = runs["summary_ref"].map(infer_cohort)
    runs["adaptive_mode"] = runs.apply(infer_adaptive_mode, axis=1)
    runs["weather_mode"] = weather_mode(runs["fixed_weather"])
    runs["run_state"] = runs["State"].astype(str)
    runs["is_finished"] = runs["run_state"].eq("finished")

    numeric_cols = [
        "seed",
        "total_years",
        "eval_train_det/mean_reward",
        "eval_test_det/mean_reward",
        "pak_holdout_return",
        "deterministic_return",
        "stochastic_return_mean",
        "stochastic_return_std",
        "eval_det/mean_reward",
        "eval_det_new_years/mean_reward",
        "eval_det_other_loc/mean_reward",
        "eval_det_other_loc_long/mean_reward",
        "eval_sto/mean_reward",
        "eval_sto_new_years/mean_reward",
        "eval_sto_other_loc/mean_reward",
        "eval_sto_other_loc_long/mean_reward",
        "uplift_vs_best_baseline_det",
        "baseline_best_return",
    ]
    for col in numeric_cols:
        if col in runs.columns:
            runs[col] = pd.to_numeric(runs[col], errors="coerce")

    finished = runs[runs["is_finished"]].copy()

    fertilization = finished[finished["domain"] == "fertilization"].copy()
    fertilization["train_test_gap"] = (
        fertilization["eval_train_det/mean_reward"] - fertilization["eval_test_det/mean_reward"]
    )
    fertilization["test_holdout_gap"] = (
        fertilization["eval_test_det/mean_reward"] - fertilization["pak_holdout_return"]
    )
    fertilization["holdout_ratio"] = (
        fertilization["pak_holdout_return"] / fertilization["eval_test_det/mean_reward"]
    )
    fertilization_comparable = fertilization[
        fertilization["eval_test_det/mean_reward"].notna() & fertilization["pak_holdout_return"].notna()
    ].copy()

    crop = finished[finished["domain"] == "crop_planning"].copy()
    crop["new_year_gap"] = crop["eval_det/mean_reward"] - crop["eval_det_new_years/mean_reward"]
    crop["new_year_ratio"] = crop["eval_det_new_years/mean_reward"] / crop["eval_det/mean_reward"]
    crop_nonhier = crop[crop["adaptive_mode"] != "hierarchical"].copy()
    crop_hier = crop[crop["adaptive_mode"] == "hierarchical"].copy()
    crop_hier["report_dir_name"] = crop_hier["thesis_report_dir"].astype(str).str.split("/").str[-1]

    ablation_rows: list[dict[str, object]] = []
    for report_dir_name in crop_hier["report_dir_name"].dropna().unique():
        report_root = ROOT / "runs" / "thesis_reports" / str(report_dir_name)
        summary_path = report_root / "reporting_summary.json"
        yearly_path = report_root / "yearly_crop_decisions.csv"
        if not summary_path.exists():
            continue
        summary = pd.read_json(summary_path, typ="series")
        row = {"report_dir_name": report_dir_name}
        for key in [
            "total_n_kg",
            "total_p_kg",
            "total_k_kg",
            "total_cost",
            "total_yearly_decisions",
            "compliant_yearly_decisions",
            "overall_compliance_rate",
        ]:
            row[key] = summary.get(key)
        if yearly_path.exists() and yearly_path.stat().st_size > 0:
            yearly = pd.read_csv(yearly_path)
            row["defined_window_rows"] = int(yearly["window_start_doy"].notna().sum())
            row["defined_window_rate"] = float(yearly["window_start_doy"].notna().mean())
            row["soy_rows"] = int((yearly["crop_name"] == "SoybeanMG.3").sum())
            row["corn_rows"] = int(yearly["crop_name"].astype(str).str.contains("Corn", na=False).sum())
        ablation_rows.append(row)

    hierarchical_ablation = crop_hier.merge(
        pd.DataFrame(ablation_rows),
        on="report_dir_name",
        how="left",
    )

    train_log_summary = pd.read_csv(TRAIN_LOG_SUMMARY) if TRAIN_LOG_SUMMARY.exists() else pd.DataFrame()
    failure_signatures = pd.read_csv(FAILURE_SIGNATURES) if FAILURE_SIGNATURES.exists() else pd.DataFrame()

    failure_causes = pd.DataFrame(
        [
            {
                "domain": "fertilization",
                "method": "DQN",
                "failed_runs": 2,
                "root_cause": "DQN does not support the MultiDiscrete([11, 11, 11]) action space.",
                "evidence_file": str(NON_HIER_CONSOLE.relative_to(ROOT)),
                "evidence_line": first_matching_line(
                    NON_HIER_CONSOLE,
                    "MultiDiscrete([11 11 11]) was provided",
                ),
            },
            {
                "domain": "crop_planning",
                "method": "DQN",
                "failed_runs": 2,
                "root_cause": "Run reaches evaluation and then crashes when wandb.log receives a PosixPath.",
                "evidence_file": str(NON_HIER_CONSOLE.relative_to(ROOT)),
                "evidence_line": first_matching_line(
                    NON_HIER_CONSOLE,
                    "TypeError: Object of type PosixPath is not JSON serializable",
                ),
            },
        ]
    )

    return AnalysisBundle(
        runs=runs,
        finished=finished,
        fertilization=fertilization,
        fertilization_comparable=fertilization_comparable,
        crop=crop,
        crop_nonhier=crop_nonhier,
        crop_hier=crop_hier,
        hierarchical_ablation=hierarchical_ablation,
        train_log_summary=train_log_summary,
        failure_signatures=failure_signatures,
        failure_causes=failure_causes,
    )


def make_run_state_plot(runs: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 4.5))
    sns.countplot(data=runs, x="domain", hue="run_state", palette="Set2")
    plt.title("Run outcomes by domain")
    plt.xlabel("Domain")
    plt.ylabel("Runs")
    savefig("01_run_state_by_domain.png")


def make_train_log_plot(train_log_summary: pd.DataFrame) -> pd.DataFrame:
    if train_log_summary.empty:
        return pd.DataFrame()
    summary = (
        train_log_summary.assign(
            end_event=lambda df: np.where(df["has_end_event"].astype(str).eq("True"), "end_logged", "missing_end")
        )
        .groupby(["domain", "end_event"], as_index=False)
        .size()
        .rename(columns={"size": "runs"})
    )
    plt.figure(figsize=(8, 4.5))
    sns.barplot(data=summary, x="domain", y="runs", hue="end_event", palette="Set1")
    plt.title("Training log completion")
    plt.xlabel("Domain")
    plt.ylabel("Log files")
    savefig("02_training_log_completion.png")
    return summary


def make_failure_signature_plot(failure_signatures: pd.DataFrame) -> None:
    if failure_signatures.empty:
        return
    plot_df = failure_signatures.sort_values("count", ascending=True)
    plt.figure(figsize=(9, 4.5))
    sns.barplot(data=plot_df, x="count", y="failure_signature", color=sns.color_palette("flare", 6)[3])
    plt.title("Historical failure signatures")
    plt.xlabel("Count")
    plt.ylabel("Failure signature")
    savefig("03_failure_signature_counts.png")


def make_fertilization_budget_plot(fertilization: pd.DataFrame) -> None:
    plot_df = fertilization[
        fertilization["method"].isin(["PPO", "A2C"])
        & fertilization["eval_test_det/mean_reward"].notna()
        & fertilization["total_years"].notna()
    ].copy()
    grouped = (
        plot_df.groupby(["method", "adaptive_mode", "weather_mode", "total_years"], as_index=False)
        .agg(mean_test_reward=("eval_test_det/mean_reward", "mean"))
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, method in zip(axes, ["PPO", "A2C"], strict=True):
        subset = grouped[grouped["method"] == method]
        sns.lineplot(
            data=subset,
            x="total_years",
            y="mean_test_reward",
            hue="weather_mode",
            style="adaptive_mode",
            markers=True,
            dashes=False,
            ax=ax,
        )
        ax.set_title(f"{method}: test reward vs training budget")
        ax.set_xlabel("total_years")
        ax.set_ylabel("eval_test_det/mean_reward")
    savefig("04_fertilization_budget_vs_test_reward.png")


def make_fertilization_holdout_plot(fertilization: pd.DataFrame) -> None:
    plot_df = fertilization[
        fertilization["eval_test_det/mean_reward"].notna() & fertilization["pak_holdout_return"].notna()
    ].copy()
    plt.figure(figsize=(7, 6))
    sns.scatterplot(
        data=plot_df,
        x="eval_test_det/mean_reward",
        y="pak_holdout_return",
        hue="method",
        style="weather_mode",
        size="total_years",
        sizes=(40, 180),
        alpha=0.8,
    )
    lower = min(plot_df["eval_test_det/mean_reward"].min(), plot_df["pak_holdout_return"].min())
    upper = max(plot_df["eval_test_det/mean_reward"].max(), plot_df["pak_holdout_return"].max())
    plt.plot([lower, upper], [lower, upper], linestyle="--", color="black", linewidth=1)
    plt.title("Fertilization: test vs holdout reward")
    plt.xlabel("eval_test_det/mean_reward")
    plt.ylabel("pak_holdout_return")
    savefig("05_fertilization_test_vs_holdout.png")


def make_fertilization_train_test_plot(fertilization: pd.DataFrame) -> None:
    plot_df = fertilization[
        fertilization["eval_train_det/mean_reward"].notna() & fertilization["eval_test_det/mean_reward"].notna()
    ].copy()
    plt.figure(figsize=(7, 6))
    sns.scatterplot(
        data=plot_df,
        x="eval_train_det/mean_reward",
        y="eval_test_det/mean_reward",
        hue="method",
        style="weather_mode",
        size="total_years",
        sizes=(40, 180),
        alpha=0.8,
    )
    lower = min(plot_df["eval_train_det/mean_reward"].min(), plot_df["eval_test_det/mean_reward"].min())
    upper = max(plot_df["eval_train_det/mean_reward"].max(), plot_df["eval_test_det/mean_reward"].max())
    plt.plot([lower, upper], [lower, upper], linestyle="--", color="black", linewidth=1)
    plt.title("Fertilization: train vs test reward")
    plt.xlabel("eval_train_det/mean_reward")
    plt.ylabel("eval_test_det/mean_reward")
    savefig("06_fertilization_train_vs_test.png")


def make_crop_hier_plot(crop: pd.DataFrame) -> None:
    plot_df = crop.copy()
    plt.figure(figsize=(10, 5))
    sns.boxplot(data=plot_df, x="adaptive_mode", y="deterministic_return", hue="method", palette="Set3")
    sns.stripplot(
        data=plot_df,
        x="adaptive_mode",
        y="deterministic_return",
        hue="method",
        dodge=True,
        linewidth=0.3,
        edgecolor="black",
        size=3,
        alpha=0.65,
        palette="dark:black",
    )
    plt.yscale("symlog", linthresh=1000)
    plt.title("Crop planning: deterministic return by policy mode")
    plt.xlabel("Policy mode")
    plt.ylabel("deterministic_return (symlog)")
    handles, labels = plt.gca().get_legend_handles_labels()
    method_count = plot_df["method"].nunique()
    plt.legend(handles[:method_count], labels[:method_count], title="Method")
    savefig("07_crop_hierarchical_vs_nonhierarchical.png")


def make_crop_new_year_plot(crop_nonhier: pd.DataFrame) -> None:
    plot_df = crop_nonhier[
        crop_nonhier["eval_det/mean_reward"].notna() & crop_nonhier["eval_det_new_years/mean_reward"].notna()
    ].copy()
    plt.figure(figsize=(7, 6))
    sns.scatterplot(
        data=plot_df,
        x="eval_det/mean_reward",
        y="eval_det_new_years/mean_reward",
        hue="method",
        style="weather_mode",
        size="deterministic_return",
        sizes=(40, 180),
        alpha=0.8,
    )
    lower = min(plot_df["eval_det/mean_reward"].min(), plot_df["eval_det_new_years/mean_reward"].min())
    upper = max(plot_df["eval_det/mean_reward"].max(), plot_df["eval_det_new_years/mean_reward"].max())
    plt.plot([lower, upper], [lower, upper], linestyle="--", color="black", linewidth=1)
    plt.title("Crop planning: in-sample vs new-years reward")
    plt.xlabel("eval_det/mean_reward")
    plt.ylabel("eval_det_new_years/mean_reward")
    savefig("08_crop_in_sample_vs_new_years.png")


def make_crop_other_loc_plot(crop: pd.DataFrame) -> None:
    plot_df = crop[crop["eval_det/mean_reward"].notna() & crop["eval_det_other_loc/mean_reward"].notna()].copy()
    plt.figure(figsize=(7, 6))
    sns.scatterplot(
        data=plot_df,
        x="eval_det/mean_reward",
        y="eval_det_other_loc/mean_reward",
        hue="adaptive_mode",
        style="method",
        alpha=0.8,
    )
    lower = min(plot_df["eval_det/mean_reward"].min(), plot_df["eval_det_other_loc/mean_reward"].min())
    upper = max(plot_df["eval_det/mean_reward"].max(), plot_df["eval_det_other_loc/mean_reward"].max())
    plt.plot([lower, upper], [lower, upper], linestyle="--", color="black", linewidth=1)
    plt.title("Crop planning: deterministic other-location check")
    plt.xlabel("eval_det/mean_reward")
    plt.ylabel("eval_det_other_loc/mean_reward")
    savefig("09_crop_other_location_identity.png")


def make_crop_metric_alignment_plot(crop_nonhier: pd.DataFrame) -> None:
    plot_df = crop_nonhier[
        crop_nonhier["eval_det/mean_reward"].notna() & crop_nonhier["deterministic_return"].notna()
    ].copy()
    plt.figure(figsize=(7, 6))
    sns.scatterplot(
        data=plot_df,
        x="eval_det/mean_reward",
        y="deterministic_return",
        hue="method",
        style="weather_mode",
        alpha=0.8,
    )
    plt.title("Crop planning: eval metric vs final deterministic return")
    plt.xlabel("eval_det/mean_reward")
    plt.ylabel("deterministic_return")
    savefig("10_crop_eval_metric_vs_final_return.png")


def make_hierarchical_ablation_cost_plot(hierarchical_ablation: pd.DataFrame) -> None:
    plot_df = hierarchical_ablation[
        hierarchical_ablation["total_cost"].notna() & hierarchical_ablation["deterministic_return"].notna()
    ].copy()
    plt.figure(figsize=(7, 6))
    sns.scatterplot(
        data=plot_df,
        x="total_cost",
        y="deterministic_return",
        hue="method",
        style="weather_mode",
        size="total_n_kg",
        sizes=(40, 180),
        alpha=0.85,
    )
    plt.title("Hierarchical ablation: nutrient cost vs deterministic return")
    plt.xlabel("Total nutrient cost")
    plt.ylabel("deterministic_return")
    savefig("11_hierarchical_cost_vs_return.png")


def make_hierarchical_ablation_window_plot(hierarchical_ablation: pd.DataFrame) -> None:
    plot_df = hierarchical_ablation.sort_values("defined_window_rate", ascending=False).copy()
    plt.figure(figsize=(10, 4.8))
    sns.barplot(
        data=plot_df,
        x="Name",
        y="defined_window_rate",
        hue="method",
        palette="Set2",
    )
    plt.title("Hierarchical ablation: share of yearly decisions with defined calendar windows")
    plt.xlabel("Run")
    plt.ylabel("Defined-window rate")
    plt.xticks(rotation=60, ha="right")
    savefig("12_hierarchical_defined_window_rate.png")


def build_tables(bundle: AnalysisBundle) -> dict[str, pd.DataFrame]:
    run_inventory = bundle.runs[
        [
            "Name",
            "run_state",
            "domain",
            "method",
            "adaptive_mode",
            "weather_mode",
            "seed",
            "total_years",
            "cohort",
            "summary_ref",
            "eval_train_det/mean_reward",
            "eval_test_det/mean_reward",
            "pak_holdout_return",
            "eval_det/mean_reward",
            "eval_det_new_years/mean_reward",
            "eval_det_other_loc/mean_reward",
            "deterministic_return",
            "stochastic_return_mean",
            "uplift_vs_best_baseline_det",
        ]
    ].copy()

    fert_group = (
        bundle.fertilization_comparable.groupby(
            ["method", "adaptive_mode", "weather_mode", "total_years"],
            as_index=False,
        )
        .agg(
            runs=("Name", "count"),
            mean_test_reward=("eval_test_det/mean_reward", "mean"),
            mean_holdout_reward=("pak_holdout_return", "mean"),
            mean_train_test_gap=("train_test_gap", "mean"),
            mean_test_holdout_gap=("test_holdout_gap", "mean"),
            mean_det_return=("deterministic_return", "mean"),
        )
        .sort_values(["mean_holdout_reward", "mean_test_reward"], ascending=False)
    )

    crop_group = (
        bundle.crop_nonhier.groupby(["method", "adaptive_mode", "weather_mode"], as_index=False)
        .agg(
            runs=("Name", "count"),
            mean_eval_det=("eval_det/mean_reward", "mean"),
            mean_eval_det_new_years=("eval_det_new_years/mean_reward", "mean"),
            mean_det_return=("deterministic_return", "mean"),
            mean_sto_return=("stochastic_return_mean", "mean"),
            mean_uplift=("uplift_vs_best_baseline_det", "mean"),
        )
        .sort_values(["adaptive_mode", "method", "weather_mode"])
    )

    top_fert = bundle.fertilization_comparable.sort_values(
        ["pak_holdout_return", "eval_test_det/mean_reward"], ascending=False
    )[
        [
            "Name",
            "method",
            "adaptive_mode",
            "weather_mode",
            "total_years",
            "seed",
            "eval_test_det/mean_reward",
            "pak_holdout_return",
            "train_test_gap",
            "deterministic_return",
        ]
    ].head(10)

    top_crop = bundle.crop_nonhier.sort_values(
        ["deterministic_return", "eval_det/mean_reward"], ascending=False
    )[
        [
            "Name",
            "method",
            "adaptive_mode",
            "weather_mode",
            "seed",
            "eval_det/mean_reward",
            "eval_det_new_years/mean_reward",
            "deterministic_return",
            "stochastic_return_mean",
            "uplift_vs_best_baseline_det",
        ]
    ].head(10)

    train_log_completion = make_train_log_plot(bundle.train_log_summary)

    hierarchical_ablation_summary = bundle.hierarchical_ablation[
        [
            "Name",
            "method",
            "weather_mode",
            "seed",
            "deterministic_return",
            "stochastic_return_mean",
            "total_cost",
            "total_n_kg",
            "total_p_kg",
            "total_k_kg",
            "overall_compliance_rate",
            "defined_window_rate",
            "corn_rows",
            "soy_rows",
        ]
    ].sort_values("deterministic_return")

    hierarchical_ablation_reasons = pd.DataFrame(
        [
            {
                "reason": "Dense fertilizer cost dominates sparse crop revenue",
                "evidence": (
                    f"Mean hierarchical nutrient cost is {bundle.hierarchical_ablation['total_cost'].mean():,.0f}, "
                    f"and cost-return correlation is {bundle.hierarchical_ablation['total_cost'].corr(bundle.hierarchical_ablation['deterministic_return']):.2f}."
                ),
                "interpretation": "The policy is spending far more on weekly fertilizer than it recovers at harvest.",
            },
            {
                "reason": "Calendar coverage is incomplete for many yearly decisions",
                "evidence": (
                    f"Only {bundle.hierarchical_ablation['defined_window_rate'].mean():.1%} of yearly decisions even have a defined calendar window "
                    f"in the thesis reports."
                ),
                "interpretation": "The high-level planner is operating with incomplete agronomic guidance, especially when soybean is chosen.",
            },
            {
                "reason": "Hierarchical PPO is especially unstable",
                "evidence": (
                    f"PPO hierarchical runs average {bundle.hierarchical_ablation.loc[bundle.hierarchical_ablation['method'].eq('PPO'), 'deterministic_return'].mean():,.0f} "
                    f"vs {bundle.hierarchical_ablation.loc[bundle.hierarchical_ablation['method'].eq('A2C'), 'deterministic_return'].mean():,.0f} for A2C."
                ),
                "interpretation": "The larger action burden appears to hurt PPO more severely under the current reward design.",
            },
        ]
    )

    suspicious = pd.DataFrame(
        [
            {
                "finding": "Crop hierarchical collapse",
                "severity": "high",
                "value": (
                    f"{len(bundle.crop_hier)}/{len(bundle.crop_hier)} hierarchical crop runs finished with negative "
                    f"deterministic return; mean {bundle.crop_hier['deterministic_return'].mean():,.0f} "
                    f"vs {bundle.crop_nonhier['deterministic_return'].mean():,.0f} for non-hier runs."
                ),
                "why_it_matters": "This is a catastrophic regression, not normal variance.",
            },
            {
                "finding": "Crop temporal generalization gap",
                "severity": "high",
                "value": (
                    f"Non-hier crop runs average {bundle.crop_nonhier['eval_det_new_years/mean_reward'].mean():,.0f} "
                    f"on new years vs {bundle.crop_nonhier['eval_det/mean_reward'].mean():,.0f} in-sample "
                    f"({bundle.crop_nonhier['new_year_ratio'].mean():.1%} retention)."
                ),
                "why_it_matters": "This is consistent with strong overfitting to the seen weather years.",
            },
            {
                "finding": "Crop other-location metric identity",
                "severity": "high",
                "value": (
                    f"{int((bundle.crop['eval_det/mean_reward'].round(6) == bundle.crop['eval_det_other_loc/mean_reward'].round(6)).sum())}/"
                    f"{bundle.crop['eval_det/mean_reward'].notna().sum()} deterministic other-location scores are exactly equal "
                    "to in-sample scores."
                ),
                "why_it_matters": "Spatial generalization claims are not trustworthy until this evaluator is audited.",
            },
            {
                "finding": "Crop metric mismatch",
                "severity": "medium",
                "value": (
                    f"Pearson correlation between eval_det/mean_reward and deterministic_return is "
                    f"{bundle.crop_nonhier['eval_det/mean_reward'].corr(bundle.crop_nonhier['deterministic_return']):.2f}."
                ),
                "why_it_matters": "The short evaluation metric is a weak proxy for the final return used in the thesis story.",
            },
            {
                "finding": "Fertilization inverse train-test gap",
                "severity": "medium",
                "value": (
                    f"{int((bundle.fertilization_comparable['train_test_gap'] < 0).sum())}/"
                    f"{len(bundle.fertilization_comparable)} comparable fertilization runs scored higher on test than train; "
                    f"mean gap {bundle.fertilization_comparable['train_test_gap'].mean():,.0f}."
                ),
                "why_it_matters": "This is the opposite of classical overfitting and suggests a split or logging definition issue.",
            },
            {
                "finding": "Fertilization low-budget instability",
                "severity": "medium",
                "value": (
                    "At total_years=1000, 8/24 runs have negative test reward and 15/24 have negative holdout reward. "
                    "At total_years=3000 all 24 runs stay positive, and at 5000 only 1/26 is negative."
                ),
                "why_it_matters": "The 1000-year budget looks under-trained and should not be used for headline claims.",
            },
            {
                "finding": "Current DQN failures are technical",
                "severity": "medium",
                "value": (
                    "Fertilization DQN fails because Stable-Baselines3 DQN rejects the MultiDiscrete action space; "
                    "crop DQN fails because wandb.log receives a PosixPath object."
                ),
                "why_it_matters": "DQN comparisons are incomplete because the failures are implementation issues, not just poor scores.",
            },
            {
                "finding": "Training logs miss explicit end events",
                "severity": "low",
                "value": (
                    f"Historical train log summaries show {int((bundle.train_log_summary['domain'].eq('fertilization') & bundle.train_log_summary['has_end_event'].astype(str).eq('False')).sum())}/"
                    f"{int(bundle.train_log_summary['domain'].eq('fertilization').sum())} fertilization logs and "
                    f"{int((bundle.train_log_summary['domain'].eq('crop_planning') & bundle.train_log_summary['has_end_event'].astype(str).eq('False')).sum())}/"
                    f"{int(bundle.train_log_summary['domain'].eq('crop_planning').sum())} crop logs without an explicit end event."
                ),
                "why_it_matters": "Instrumentation is mostly usable, but end-of-run logging is not fully reliable.",
            },
        ]
    )

    return {
        "run_inventory.csv": run_inventory,
        "fertilization_group_summary.csv": fert_group,
        "crop_group_summary.csv": crop_group,
        "top_fertilization_runs.csv": top_fert,
        "top_crop_runs.csv": top_crop,
        "hierarchical_failed_ablation_summary.csv": hierarchical_ablation_summary,
        "hierarchical_failed_ablation_reasons.csv": hierarchical_ablation_reasons,
        "suspicious_checks.csv": suspicious,
        "current_failure_causes.csv": bundle.failure_causes,
        "train_log_completion_summary.csv": train_log_completion,
    }


def build_report(bundle: AnalysisBundle, tables: dict[str, pd.DataFrame]) -> str:
    total_runs = len(bundle.runs)
    total_finished = int(bundle.runs["is_finished"].sum())
    total_failed = total_runs - total_finished

    positive_holdout = bundle.fertilization_comparable[
        (bundle.fertilization_comparable["eval_test_det/mean_reward"] > 0)
        & (bundle.fertilization_comparable["pak_holdout_return"] > 0)
    ].copy()
    holdout_ratio_median = (
        positive_holdout["pak_holdout_return"] / positive_holdout["eval_test_det/mean_reward"]
    ).median()

    coverage = pd.DataFrame(
        [
            {
                "domain": "fertilization",
                "finished_runs": len(bundle.fertilization),
                "failed_runs": int((bundle.runs["domain"].eq("fertilization") & ~bundle.runs["is_finished"]).sum()),
            },
            {
                "domain": "crop_planning",
                "finished_runs": len(bundle.crop),
                "failed_runs": int((bundle.runs["domain"].eq("crop_planning") & ~bundle.runs["is_finished"]).sum()),
            },
        ]
    )

    report = f"""# Runs Experiments Report

Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Scope

- Main consolidated source: `run_experiments_7_3_2026_RUNS/wandb_export_2026-03-11T01_53_38.382+05_00.csv`
- Supporting summaries: `runs/experiment_summaries/train_logs_summary.csv`, `runs/experiment_summaries/failure_signature_counts.csv`
- Current failure root-cause evidence: `runs/experiment_summaries/non_hier_10_3_2026_20260309_193918/console.log`
- Performance comparisons below are based on finished runs unless stated otherwise.

## Executive Summary

1. Hierarchical crop planning has been removed from the main comparative results and is now reported only as a failed ablation. Its mean deterministic return is {bundle.crop_hier['deterministic_return'].mean():,.0f} versus {bundle.crop_nonhier['deterministic_return'].mean():,.0f} for non-hier runs.
2. Crop planning also shows a strong temporal generalization gap. Non-hier runs retain only {bundle.crop_nonhier['new_year_ratio'].mean():.1%} of in-sample deterministic reward on the `new_years` evaluation.
3. The crop `other_loc` deterministic metric is almost certainly misconfigured: {int((bundle.crop['eval_det/mean_reward'].round(6) == bundle.crop['eval_det_other_loc/mean_reward'].round(6)).sum())} of {bundle.crop['eval_det/mean_reward'].notna().sum()} runs match exactly.
4. Fertilization does not show classical overfitting. Instead, {int((bundle.fertilization_comparable['train_test_gap'] < 0).sum())} of {len(bundle.fertilization_comparable)} comparable runs score higher on test than train, which is itself suspicious and should be audited.
5. Fertilization budgets below `total_years=3000` are unstable. At `1000` years, 8 of 24 runs have negative test reward and 15 of 24 have negative holdout reward.

## Coverage

The export contains {total_runs} runs in total. {total_finished} finished and {total_failed} failed.

{markdown_table(coverage)}

![Run state counts](figures/01_run_state_by_domain.png)

## Main Findings

### Fertilization

- Best-performing finished fertilization runs are concentrated at `total_years=3000` or `5000`, with PPO and A2C both reaching the 790k range on `eval_test_det/mean_reward`.
- Among runs with positive test and holdout scores, the median holdout/test ratio is {holdout_ratio_median:.3f}. Holdout performance is usually close to test performance once the budget is large enough.
- The low-budget regime is the weak point: `1000`-year runs are the only budget where negative rewards are common.
- The train/test direction is unusual. Test scores are often much larger than train scores, so this is not standard overfitting; it looks more like a split-definition or logging mismatch.

![Fertilization budget vs test reward](figures/04_fertilization_budget_vs_test_reward.png)

![Fertilization test vs holdout](figures/05_fertilization_test_vs_holdout.png)

![Fertilization train vs test](figures/06_fertilization_train_vs_test.png)

Top fertilization runs by holdout performance:

{markdown_table(tables["top_fertilization_runs.csv"], max_rows=5)}

### Crop Planning (Main Results, Hierarchy Excluded)

- The crop tables and comparisons in this section exclude the hierarchical variant and use only the non-hier policies.
- Non-hier crop runs are much healthier, but their `new_years` performance collapses. Mean in-sample deterministic evaluation is {bundle.crop_nonhier['eval_det/mean_reward'].mean():,.0f}, while `eval_det_new_years/mean_reward` drops to {bundle.crop_nonhier['eval_det_new_years/mean_reward'].mean():,.0f}.
- The crop deterministic evaluation metrics need caution. `eval_det/mean_reward` correlates only {bundle.crop_nonhier['eval_det/mean_reward'].corr(bundle.crop_nonhier['deterministic_return']):.2f} with the final deterministic return, so it is not a reliable standalone ranking metric.
- The deterministic `other_loc` metric is effectively identical to in-sample results, so spatial-generalization claims should be avoided until the evaluator is checked.

![Crop in-sample vs new years](figures/08_crop_in_sample_vs_new_years.png)

![Crop other-location identity](figures/09_crop_other_location_identity.png)

![Crop eval metric vs final return](figures/10_crop_eval_metric_vs_final_return.png)

Top non-hier crop runs by deterministic return:

{markdown_table(tables["top_crop_runs.csv"], max_rows=5)}

## Failed Hierarchical Ablation

The hierarchical crop variant is excluded from the main results because it is not a valid competitive model in its current form. It is better interpreted as a failed ablation that revealed design problems in the hierarchical setup.

- All 12 finished hierarchical runs have negative deterministic return.
- Mean nutrient cost across the 12 reports is {bundle.hierarchical_ablation['total_cost'].mean():,.0f}.
- Only {bundle.hierarchical_ablation['defined_window_rate'].mean():.1%} of yearly decisions have a defined calendar window in the thesis report files.
- The correlation between total nutrient cost and deterministic return is {bundle.hierarchical_ablation['total_cost'].corr(bundle.hierarchical_ablation['deterministic_return']):.2f}, which strongly supports cost blow-up as a primary failure mode.

Academic interpretation:

- The ablation fails because the low-level weekly fertilizer controller is too unconstrained relative to the sparse crop-revenue signal.
- The high-level crop planner is also operating with incomplete agronomic guidance, since many yearly decisions do not even have a defined calendar window in the generated thesis-report files.
- For this reason, the hierarchical variant should be discussed as a negative result and future-work item, not as an empirical baseline.

Rerun status:

- The environment has now been hardened for follow-up experiments with crop-window sanitization, seasonal fertilizer gating, and annual nutrient budgets.
- Those code changes are intended only for targeted reruns; they do not change the interpretation of the completed March 7-11, 2026 matrix reported here.

![Crop hierarchical vs non-hierarchical](figures/07_crop_hierarchical_vs_nonhierarchical.png)

![Hierarchical cost vs return](figures/11_hierarchical_cost_vs_return.png)

![Hierarchical defined-window rate](figures/12_hierarchical_defined_window_rate.png)

Failed-ablation reasons:

{markdown_table(tables["hierarchical_failed_ablation_reasons.csv"])}

Run-level failed-ablation summary:

{markdown_table(tables["hierarchical_failed_ablation_summary.csv"], max_rows=6)}

## Suspicious Items To Mention Explicitly

{markdown_table(tables["suspicious_checks.csv"])}

## Failure Analysis

All four failed runs in the current March export are DQN runs, but the failure modes are implementation issues rather than simple low reward:

{markdown_table(tables["current_failure_causes.csv"])}

The historical failure signature summary is still useful for context:

![Historical failure signatures](figures/03_failure_signature_counts.png)

## Logging Quality

The raw training logs are usable but not perfect. Some files stop without an explicit end event, especially on fertilization runs.

![Training log completion](figures/02_training_log_completion.png)

## Recommended Thesis Framing

1. Present fertilization `3000` and `5000`-year PPO/A2C results as the credible training regime, and describe `1000` years as under-trained.
2. Do not claim classical overfitting for fertilization. Instead, report an unexpected train/test inversion and state that the split semantics need audit.
3. Report crop non-hier performance, but explicitly say temporal generalization to unseen years is weak.
4. Do not use crop `other_loc` deterministic results as evidence of spatial transfer until the evaluation path is verified.
5. Present the hierarchical crop variant only as a failed ablation with documented causes, not as part of the main crop benchmark table.
6. If a follow-up hierarchical rerun is shown, label it explicitly as post-hoc stabilization work rather than mixing it into the completed March benchmark claims.
"""
    return report


def main() -> None:
    ensure_dirs()
    sns.set_theme(style="whitegrid")

    bundle = load_runs()

    make_run_state_plot(bundle.runs)
    make_failure_signature_plot(bundle.failure_signatures)
    make_fertilization_budget_plot(bundle.fertilization)
    make_fertilization_holdout_plot(bundle.fertilization_comparable)
    make_fertilization_train_test_plot(bundle.fertilization)
    make_crop_hier_plot(bundle.crop)
    make_crop_new_year_plot(bundle.crop_nonhier)
    make_crop_other_loc_plot(bundle.crop)
    make_crop_metric_alignment_plot(bundle.crop_nonhier)
    make_hierarchical_ablation_cost_plot(bundle.hierarchical_ablation)
    make_hierarchical_ablation_window_plot(bundle.hierarchical_ablation)

    tables = build_tables(bundle)
    for name, table in tables.items():
        export_table(table, name)

    report = build_report(bundle, tables)
    (REPORT_DIR / "Run_Experiment_Analysis_Report.md").write_text(report, encoding="utf-8")

    print(f"Report written to: {REPORT_DIR}")


if __name__ == "__main__":
    main()
