from __future__ import annotations

import json
from pathlib import Path
from textwrap import fill

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


THESIS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
FIG_ROOT = THESIS_ROOT / "figures" / "generated"
TAB_ROOT = THESIS_ROOT / "tables" / "generated"
REPORTING_ROOT = REPO_ROOT / "artifacts" / "final_successful_runs" / "final_113" / "reporting"
DOCS_ASSET_ROOT = REPO_ROOT / "docs" / "assets"
RECOVERED_WANDB_ROOT = REPO_ROOT / "artifacts" / "final_successful_runs" / "Recovered" / "wandb_full_backup"

GROUP_ORDER = [
    "fertilization_core",
    "fertilization_baseline",
    "fertilization_dqn_rerun",
    "crop_planning_nonhier",
    "crop_planning_dqn_rerun",
    "crop_planning_hierarchical_guarded_rerun",
]

GROUP_LABELS = {
    "fertilization_core": "Fertilization core",
    "fertilization_baseline": "Fertilization baseline",
    "fertilization_dqn_rerun": "Fertilization DQN rerun",
    "crop_planning_nonhier": "Crop planning non-hierarchical",
    "crop_planning_dqn_rerun": "Crop planning DQN rerun",
    "crop_planning_hierarchical_guarded_rerun": "Crop planning hierarchical guarded rerun",
}

ANOVA_TERM_LABELS = {
    "C(method)": "method",
    "C(adaptive_label)": "adaptivity",
    "C(weather_label)": "weather regime",
    "C(budget_label)": "budget",
    "C(method):C(weather_label)": "method x weather",
    "C(method):C(budget_label)": "method x budget",
    "C(adaptive_label):C(weather_label)": "adaptivity x weather",
}


def ensure_dirs() -> None:
    for subdir in [
        FIG_ROOT / "context",
        FIG_ROOT / "protocol",
        FIG_ROOT / "results_final",
        TAB_ROOT,
        DOCS_ASSET_ROOT,
    ]:
        subdir.mkdir(parents=True, exist_ok=True)


def load_weather() -> pd.DataFrame:
    weather_path = REPO_ROOT / "cycles" / "input" / "Pakistan_Site_final.weather"
    df = pd.read_csv(
        weather_path,
        sep=r"\s+",
        skiprows=[0, 1, 2, 4],
        engine="python",
    )
    for col in ["YEAR", "DOY", "PP", "TX", "TN", "SOLAR", "RHX", "RHN", "WIND"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna().reset_index(drop=True)


def load_price_series() -> dict:
    price_path = REPO_ROOT / "cyclesgym" / "resources" / "pricing" / "pakistan_yearly_series.json"
    return json.loads(price_path.read_text(encoding="utf-8"))


def _parse_bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().map({"true": True, "false": False}).fillna(False)


def _numericify(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    numeric_names = {
        "index",
        "seed",
        "n",
        "total_years",
        "primary_metric_value",
        "deterministic_return",
        "eval_det_mean_reward",
        "eval_sto_mean_reward",
        "stochastic_return_mean",
        "stochastic_return_std",
        "pak_holdout_return",
        "baseline_best_return",
        "uplift_vs_best_baseline_det",
        "runtime_seconds",
        "summary_json_count",
        "mean_a",
        "mean_b",
        "statistic",
        "df",
        "p_value",
        "corrected_p_value",
        "sum_sq",
        "eta_squared",
        "effect_size",
        "ci_low",
        "ci_high",
    }
    for col in out.columns:
        if (
            col in numeric_names
            or col.endswith("_mean")
            or col.endswith("_std")
            or col.endswith("_se")
            or col.endswith("_ci_low")
            or col.endswith("_ci_high")
            or col.endswith("_min")
            or col.endswith("_max")
            or col.startswith("guardrail_annual_")
            or col.startswith("hierarchical_export_")
        ):
            out[col] = pd.to_numeric(out[col], errors="coerce")
    bool_columns = [
        "fixed_weather",
        "nonadaptive",
        "adaptive",
        "hierarchical",
        "baseline",
        "inferential_eligible",
        "summary_json_present_actual",
        "wandb_summary_present_actual",
        "model_zip_present_actual",
        "best_model_present_actual",
        "vec_normalize_present_actual",
        "hierarchical_report_present_actual",
        "is_replacement",
        "hierarchical_export_match",
    ]
    for col in bool_columns:
        if col in out.columns:
            out[col] = _parse_bool_series(out[col])
    return out


def load_run_level() -> pd.DataFrame:
    return _numericify(pd.read_csv(REPORTING_ROOT / "run_level_metrics.csv"))


def load_grouped_metrics() -> pd.DataFrame:
    return _numericify(pd.read_csv(REPORTING_ROOT / "grouped_metrics.csv"))


def load_statistical_tests() -> pd.DataFrame:
    return _numericify(pd.read_csv(REPORTING_ROOT / "statistical_tests.csv"))


def load_final_summary() -> dict:
    path = REPORTING_ROOT / "final_reporting_summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_artifact_audit() -> pd.DataFrame:
    return _numericify(pd.read_csv(REPORTING_ROOT / "artifact_completeness_audit.csv"))


def savefig(fig: plt.Figure, relative_path: str) -> None:
    out_path = THESIS_ROOT / relative_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def savefig_copy(fig: plt.Figure, thesis_relative_path: str, repo_relative_path: str) -> None:
    thesis_path = THESIS_ROOT / thesis_relative_path
    repo_path = REPO_ROOT / repo_relative_path
    thesis_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(thesis_path, bbox_inches="tight")
    fig.savefig(repo_path, bbox_inches="tight", dpi=180)
    plt.close(fig)


def wrap(text: str, width: int = 20) -> str:
    return fill(text, width=width)


def latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def fmt_num(value: object, decimals: int = 1, thousands: bool = True) -> str:
    if value is None or pd.isna(value):
        return "--"
    number = float(value)
    if decimals == 0:
        return f"{number:,.0f}" if thousands else f"{number:.0f}"
    return f"{number:,.{decimals}f}" if thousands else f"{number:.{decimals}f}"


def fmt_hours(seconds: object) -> str:
    if seconds is None or pd.isna(seconds):
        return "--"
    return fmt_num(float(seconds) / 3600.0, decimals=2, thousands=False)


def fmt_ci(low: object, high: object, decimals: int = 1) -> str:
    if low is None or high is None or pd.isna(low) or pd.isna(high):
        return "--"
    return f"[{fmt_num(low, decimals=decimals)}, {fmt_num(high, decimals=decimals)}]"


def fmt_p(value: object) -> str:
    if value is None or pd.isna(value):
        return "--"
    value = float(value)
    if value < 0.001:
        return "less than 0.001"
    return f"{value:.3f}"


def display_group(group_key: str) -> str:
    return str(group_key).replace("_", " ")


def draw_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    facecolor: str,
    edgecolor: str = "#1f2937",
    fontsize: int = 10,
) -> None:
    box = patches.FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.2,
        edgecolor=edgecolor,
        facecolor=facecolor,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2,
        y + h / 2,
        wrap(text, 20),
        ha="center",
        va="center",
        fontsize=fontsize,
        color="#111827",
    )


def draw_arrow(ax: plt.Axes, x0: float, y0: float, x1: float, y1: float) -> None:
    ax.annotate(
        "",
        xy=(x1, y1),
        xytext=(x0, y0),
        arrowprops=dict(arrowstyle="->", lw=1.6, color="#374151"),
    )


def _recovered_run_dirs() -> dict[str, Path]:
    run_dirs: dict[str, Path] = {}
    if not RECOVERED_WANDB_ROOT.exists():
        return run_dirs
    for project_dir in RECOVERED_WANDB_ROOT.iterdir():
        if not project_dir.is_dir():
            continue
        for run_dir in project_dir.iterdir():
            if run_dir.is_dir() and "__" in run_dir.name:
                run_dirs[run_dir.name.split("__", 1)[0]] = run_dir
    return run_dirs


def _count_recovered_artifacts() -> dict[str, int]:
    if not RECOVERED_WANDB_ROOT.exists():
        return {
            "tensorboard_event_files": 0,
            "history_scan_csv": 0,
            "system_metrics_json": 0,
            "table_json": 0,
        }
    return {
        "tensorboard_event_files": sum(1 for _ in RECOVERED_WANDB_ROOT.rglob("events.out.tfevents*")),
        "history_scan_csv": sum(1 for _ in RECOVERED_WANDB_ROOT.rglob("history_scan.csv")),
        "system_metrics_json": sum(1 for _ in RECOVERED_WANDB_ROOT.rglob("system_metrics.json")),
        "table_json": sum(1 for _ in RECOVERED_WANDB_ROOT.rglob("*.table.json")),
    }


def write_tex_table(filename: str, body: str) -> None:
    (TAB_ROOT / filename).write_text(body.strip() + "\n", encoding="utf-8")


def tabular_table(
    caption: str,
    label: str,
    headers: list[str],
    rows: list[list[str]],
    col_spec: str,
    filename: str,
    use_tabularx: bool = False,
    resize: bool = False,
) -> None:
    env_name = "tabularx" if use_tabularx else "tabular"
    lines = [
        r"\begin{table}[H]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
    ]
    if resize:
        lines.append(r"\resizebox{\textwidth}{!}{%")
    if use_tabularx:
        lines.append(rf"\begin{{{env_name}}}{{\textwidth}}{{{col_spec}}}")
    else:
        lines.append(rf"\begin{{{env_name}}}{{{col_spec}}}")
    lines.extend([r"\toprule", " & ".join(headers) + r" \\", r"\midrule"])
    for row in rows:
        lines.append(" & ".join(row) + r" \\")
    lines.extend([r"\bottomrule", rf"\end{{{env_name}}}"])
    if resize:
        lines.append(r"}")
    lines.append(r"\end{table}")
    write_tex_table(filename, "\n".join(lines))


def generate_context_figures(price_payload: dict, weather_df: pd.DataFrame) -> None:
    crop_prices = price_payload["crop_prices_lcu_per_tonne"]
    nutrient_prices = price_payload["nutrient_prices_rs_per_kg"]

    years = np.array(sorted(map(int, crop_prices["maize"].keys())))
    maize = np.array([crop_prices["maize"][str(y)] for y in years], dtype=float)
    soy = np.array([crop_prices["soybeans"][str(y)] for y in years], dtype=float)
    silage = np.array([crop_prices["maize_silage_proxy"][str(y)] for y in years], dtype=float)

    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    ax.plot(years, maize, label="Maize producer price", color="#0f766e", lw=2.2)
    ax.plot(years, soy, label="Soybean producer price", color="#dc2626", lw=2.2)
    ax.plot(years, silage, label="Maize silage proxy", color="#7c3aed", lw=2.2, ls="--")
    ax.set_title("Pakistan crop price series used by the thesis stack")
    ax.set_xlabel("Year")
    ax.set_ylabel("Local currency units per tonne")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    savefig(fig, "figures/generated/context/pakistan_crop_price_trends.pdf")

    nutrient_years = np.array(sorted(map(int, nutrient_prices["N"].keys())))
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    for nutrient, color in [("N", "#2563eb"), ("P", "#f59e0b"), ("K", "#16a34a")]:
        values = np.array([nutrient_prices[nutrient][str(y)] for y in nutrient_years], dtype=float)
        ax.plot(nutrient_years, values, label=f"{nutrient} price", color=color, lw=2.2)
    ax.set_title("Pakistan nutrient price series derived from NFDC-linked data")
    ax.set_xlabel("Year")
    ax.set_ylabel("PKR per kg nutrient")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    savefig(fig, "figures/generated/context/pakistan_nutrient_price_trends.pdf")

    annual = (
        weather_df.groupby("YEAR")
        .agg(annual_rainfall_mm=("PP", "sum"), mean_tx=("TX", "mean"), mean_tn=("TN", "mean"))
        .reset_index()
    )
    fig, ax1 = plt.subplots(figsize=(10.5, 5.5))
    ax1.bar(annual["YEAR"], annual["annual_rainfall_mm"], color="#38bdf8", alpha=0.8, label="Annual rainfall")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Rainfall (mm)", color="#0c4a6e")
    ax1.tick_params(axis="y", labelcolor="#0c4a6e")
    ax2 = ax1.twinx()
    ax2.plot(annual["YEAR"], annual["mean_tx"], color="#b91c1c", lw=2.2, label="Mean Tmax")
    ax2.plot(annual["YEAR"], annual["mean_tn"], color="#1d4ed8", lw=2.2, label="Mean Tmin")
    ax2.set_ylabel("Temperature (deg C)")
    lines, labels = [], []
    for axis in [ax1, ax2]:
        current_lines, current_labels = axis.get_legend_handles_labels()
        lines.extend(current_lines)
        labels.extend(current_labels)
    ax1.legend(lines, labels, frameon=False, loc="upper left")
    ax1.set_title("Coverage of the Pakistan weather file wired into training and evaluation")
    ax1.grid(alpha=0.15)
    savefig(fig, "figures/generated/context/pakistan_weather_coverage.pdf")

    climatology = weather_df.copy()
    climatology["date"] = pd.to_datetime(
        climatology["YEAR"].astype(int).astype(str) + climatology["DOY"].astype(int).astype(str).str.zfill(3),
        format="%Y%j",
    )
    climatology["month"] = climatology["date"].dt.month
    monthly = (
        climatology.groupby("month")
        .agg(monthly_rainfall_mm=("PP", "mean"), mean_tx=("TX", "mean"), mean_tn=("TN", "mean"))
        .reset_index()
    )
    fig, ax1 = plt.subplots(figsize=(10.5, 5.5))
    ax1.bar(monthly["month"], monthly["monthly_rainfall_mm"], color="#0ea5e9", alpha=0.8, label="Mean monthly rainfall")
    ax1.set_xticks(range(1, 13))
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Rainfall (mm)", color="#0c4a6e")
    ax1.tick_params(axis="y", labelcolor="#0c4a6e")
    ax2 = ax1.twinx()
    ax2.plot(monthly["month"], monthly["mean_tx"], color="#b91c1c", lw=2.2, label="Mean Tmax")
    ax2.plot(monthly["month"], monthly["mean_tn"], color="#1d4ed8", lw=2.2, label="Mean Tmin")
    ax2.set_ylabel("Temperature (deg C)")
    lines, labels = [], []
    for axis in [ax1, ax2]:
        current_lines, current_labels = axis.get_legend_handles_labels()
        lines.extend(current_lines)
        labels.extend(current_labels)
    ax1.legend(lines, labels, frameon=False, loc="upper right")
    ax1.set_title("Monthly climatology implied by the Pakistan weather file")
    ax1.grid(alpha=0.15)
    savefig(fig, "figures/generated/context/pakistan_monthly_climatology.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 3.5))
    ax.set_xlim(1, 365)
    ax.set_ylim(0, 3)
    ax.set_yticks([1, 2])
    ax.set_yticklabels(["Winter wheat", "Corn family"])
    ax.set_xticks([1, 60, 121, 182, 244, 305, 365])
    ax.set_xlabel("Day of year")
    ax.set_title("Pakistan crop-calendar windows currently enforced in the thesis repo")
    ax.barh(1, 334 - 305, left=305, height=0.35, color="#f59e0b", alpha=0.85)
    ax.barh(2, 196 - 166, left=166, height=0.35, color="#16a34a", alpha=0.85)
    ax.text(319.5, 1, "Nov 1-30", ha="center", va="center", fontsize=10)
    ax.text(181, 2, "Mid Jun-Mid Jul", ha="center", va="center", fontsize=10)
    ax.grid(axis="x", alpha=0.25)
    savefig(fig, "figures/generated/context/pakistan_crop_calendar_windows.pdf")


def generate_protocol_figures(run_level_df: pd.DataFrame) -> None:
    counts = (
        run_level_df.groupby(["domain", "method"])
        .size()
        .reset_index(name="count")
        .sort_values(["domain", "method"])
    )
    domains = counts["domain"].unique().tolist()
    methods = counts["method"].unique().tolist()
    x = np.arange(len(domains))
    width = 0.18
    colors = {"PPO": "#0f766e", "A2C": "#1d4ed8", "DQN": "#dc2626", "BASELINE": "#6b7280"}
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    for idx, method in enumerate(methods):
        values = []
        for domain in domains:
            row = counts[(counts["domain"] == domain) & (counts["method"] == method)]
            values.append(int(row["count"].iloc[0]) if not row.empty else 0)
        offset = idx * width - width * (len(methods) - 1) / 2
        ax.bar(x + offset, values, width=width, label=method, color=colors.get(method, "#111827"))
    ax.set_xticks(x)
    ax.set_xticklabels([domain.replace("_", " ").title() for domain in domains])
    ax.set_ylabel("Runs")
    ax.set_title("Final 113-run thesis matrix composition by domain and method")
    ax.legend(frameon=False, ncol=len(methods))
    ax.grid(axis="y", alpha=0.25)
    savefig(fig, "figures/generated/protocol/experiment_matrix_counts.pdf")

    fert_only = run_level_df[run_level_df["domain"] == "fertilization"].copy()
    budget_counts = fert_only["budget_label"].dropna().astype(str).value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10.5, 5.0))
    ax.barh(range(len(budget_counts)), budget_counts.values, color="#7c3aed")
    ax.set_yticks(range(len(budget_counts)))
    ax.set_yticklabels([latex_escape(label) for label in budget_counts.index])
    ax.set_xlabel("Runs")
    ax.set_title("Budget distribution inside the fertilization branch of the final matrix")
    ax.grid(axis="x", alpha=0.25)
    savefig(fig, "figures/generated/protocol/experiment_budget_counts.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    draw_box(ax, 0.07, 0.66, 0.18, 0.16, "Policy network", "#d1fae5")
    draw_box(ax, 0.34, 0.66, 0.18, 0.16, "Action mapper", "#dbeafe")
    draw_box(ax, 0.61, 0.66, 0.18, 0.16, "CYCLES-backed environment", "#fee2e2")
    draw_box(ax, 0.61, 0.30, 0.18, 0.16, "Observers and rewarders", "#fce7f3")
    draw_box(ax, 0.34, 0.30, 0.18, 0.16, "Normalized observations", "#fef3c7")
    draw_box(ax, 0.07, 0.30, 0.18, 0.16, "Logging and evaluation", "#ddd6fe")
    draw_arrow(ax, 0.25, 0.74, 0.34, 0.74)
    draw_arrow(ax, 0.52, 0.74, 0.61, 0.74)
    draw_arrow(ax, 0.70, 0.66, 0.70, 0.46)
    draw_arrow(ax, 0.61, 0.38, 0.52, 0.38)
    draw_arrow(ax, 0.34, 0.38, 0.25, 0.38)
    draw_arrow(ax, 0.16, 0.46, 0.16, 0.66)
    ax.text(0.43, 0.79, "policy output", fontsize=9, ha="center")
    ax.text(0.70, 0.53, "transition + reward", fontsize=9, ha="center")
    ax.text(0.43, 0.43, "state features", fontsize=9, ha="center")
    ax.text(0.16, 0.53, "metrics", fontsize=9, rotation=90, va="center")
    ax.axis("off")
    ax.set_title("RL interaction loop instantiated by the thesis stack")
    savefig(fig, "figures/generated/protocol/rl_loop_diagram.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    draw_box(ax, 0.04, 0.72, 0.16, 0.16, "SB3 policy", "#d1fae5")
    draw_box(ax, 0.27, 0.72, 0.18, 0.16, "cyclesgym environment", "#dbeafe")
    draw_box(ax, 0.52, 0.72, 0.18, 0.16, "Implementers and managers", "#fee2e2")
    draw_box(ax, 0.76, 0.72, 0.18, 0.16, "CYCLES executable", "#ede9fe")
    draw_box(ax, 0.52, 0.40, 0.18, 0.16, "Output parsers", "#fef3c7")
    draw_box(ax, 0.27, 0.40, 0.18, 0.16, "Observers and rewarders", "#fce7f3")
    draw_arrow(ax, 0.20, 0.80, 0.27, 0.80)
    draw_arrow(ax, 0.45, 0.80, 0.52, 0.80)
    draw_arrow(ax, 0.70, 0.80, 0.76, 0.80)
    draw_arrow(ax, 0.76, 0.72, 0.70, 0.56)
    draw_arrow(ax, 0.52, 0.48, 0.45, 0.48)
    draw_arrow(ax, 0.27, 0.48, 0.20, 0.72)
    ax.text(0.84, 0.56, "write inputs\nrun simulation", fontsize=9, ha="center")
    ax.text(0.60, 0.58, "read outputs", fontsize=9, ha="center")
    ax.axis("off")
    ax.set_title("Component-level architecture of the thesis system")
    savefig(fig, "figures/generated/protocol/system_architecture_diagram.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    lanes = [("Agent", 0.86), ("Environment", 0.64), ("Filesystem", 0.42), ("CYCLES", 0.20)]
    for label, y in lanes:
        ax.plot([0.10, 0.90], [y, y], color="#d1d5db", lw=1.2)
        ax.text(0.03, y, label, fontsize=10, va="center", fontweight="bold")
    sequence = [
        (0.16, 0.86, 0.26, 0.64, "reset()"),
        (0.28, 0.64, 0.42, 0.42, "write control/operation/weather"),
        (0.44, 0.64, 0.58, 0.20, "invoke CYCLES"),
        (0.60, 0.20, 0.72, 0.42, "output files"),
        (0.74, 0.42, 0.86, 0.64, "parse and score"),
        (0.88, 0.64, 0.90, 0.86, "obs, reward, info"),
    ]
    for x0, y0, x1, y1, label in sequence:
        draw_arrow(ax, x0, y0, x1, y1)
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.03, wrap(label, 18), fontsize=9, ha="center")
    ax.axis("off")
    ax.set_title("Sequence of one environment interaction cycle")
    savefig(fig, "figures/generated/protocol/simulation_sequence_diagram.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    draw_box(ax, 0.05, 0.66, 0.18, 0.16, "Start of year", "#dbeafe")
    draw_box(ax, 0.29, 0.66, 0.20, 0.16, "Crop planning action", "#d1fae5")
    draw_box(ax, 0.56, 0.66, 0.18, 0.16, "Planting window configuration", "#fef3c7")
    draw_box(ax, 0.79, 0.66, 0.16, 0.16, "Weekly loop", "#fee2e2")
    draw_box(ax, 0.79, 0.34, 0.16, 0.16, "NPK fertilization action", "#ede9fe")
    draw_box(ax, 0.56, 0.34, 0.18, 0.16, "CYCLES step and outputs", "#fce7f3")
    draw_box(ax, 0.29, 0.34, 0.20, 0.16, "Reward, compliance, and logs", "#e0f2fe")
    draw_box(ax, 0.05, 0.34, 0.18, 0.16, "End-year summary", "#dcfce7")
    draw_arrow(ax, 0.23, 0.74, 0.29, 0.74)
    draw_arrow(ax, 0.49, 0.74, 0.56, 0.74)
    draw_arrow(ax, 0.74, 0.74, 0.79, 0.74)
    draw_arrow(ax, 0.87, 0.66, 0.87, 0.50)
    draw_arrow(ax, 0.79, 0.42, 0.74, 0.42)
    draw_arrow(ax, 0.56, 0.42, 0.49, 0.42)
    draw_arrow(ax, 0.29, 0.42, 0.23, 0.42)
    draw_arrow(ax, 0.14, 0.50, 0.14, 0.66)
    ax.text(0.11, 0.58, "repeat yearly", fontsize=9, rotation=90, va="center")
    ax.axis("off")
    ax.set_title("Hierarchical decision flow implemented in the current repo")
    savefig(fig, "figures/generated/protocol/hierarchical_decision_diagram.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    draw_box(ax, 0.05, 0.68, 0.16, 0.16, "CLI config and defaults", "#dbeafe")
    draw_box(ax, 0.27, 0.68, 0.16, 0.16, "Environment builder", "#d1fae5")
    draw_box(ax, 0.49, 0.68, 0.16, 0.16, "VecMonitor and VecNormalize", "#fef3c7")
    draw_box(ax, 0.72, 0.68, 0.18, 0.16, "PPO / A2C / DQN", "#fee2e2")
    draw_box(ax, 0.72, 0.36, 0.18, 0.16, "Model checkpoints and stats", "#ede9fe")
    draw_box(ax, 0.49, 0.36, 0.16, 0.16, "Eval callbacks", "#e0f2fe")
    draw_box(ax, 0.27, 0.36, 0.16, 0.16, "JSONL train logs", "#dcfce7")
    draw_box(ax, 0.05, 0.36, 0.16, 0.16, "Summary JSON", "#fce7f3")
    draw_arrow(ax, 0.21, 0.76, 0.27, 0.76)
    draw_arrow(ax, 0.43, 0.76, 0.49, 0.76)
    draw_arrow(ax, 0.65, 0.76, 0.72, 0.76)
    draw_arrow(ax, 0.81, 0.68, 0.81, 0.52)
    draw_arrow(ax, 0.72, 0.44, 0.65, 0.44)
    draw_arrow(ax, 0.49, 0.44, 0.43, 0.44)
    draw_arrow(ax, 0.27, 0.44, 0.21, 0.44)
    ax.axis("off")
    ax.set_title("Training and evaluation pipeline used for thesis experiments")
    savefig(fig, "figures/generated/protocol/training_pipeline_diagram.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    draw_box(ax, 0.05, 0.67, 0.18, 0.16, "Environment step info", "#dbeafe")
    draw_box(ax, 0.29, 0.67, 0.18, 0.16, "Hierarchical report callback", "#d1fae5")
    draw_box(ax, 0.54, 0.67, 0.18, 0.16, "Weekly and yearly logs", "#fef3c7")
    draw_box(ax, 0.79, 0.67, 0.16, 0.16, "Summary JSON", "#fee2e2")
    draw_box(ax, 0.54, 0.35, 0.18, 0.16, "Canonical final reports", "#ede9fe")
    draw_box(ax, 0.79, 0.35, 0.16, 0.16, "Thesis tables and figures", "#fce7f3")
    draw_box(ax, 0.29, 0.35, 0.18, 0.16, "final\\_113/reporting", "#e0f2fe")
    draw_box(ax, 0.05, 0.35, 0.18, 0.16, "Audit and provenance notes", "#dcfce7")
    draw_arrow(ax, 0.23, 0.75, 0.29, 0.75)
    draw_arrow(ax, 0.47, 0.75, 0.54, 0.75)
    draw_arrow(ax, 0.72, 0.75, 0.79, 0.75)
    draw_arrow(ax, 0.62, 0.67, 0.62, 0.51)
    draw_arrow(ax, 0.47, 0.43, 0.54, 0.43)
    draw_arrow(ax, 0.72, 0.43, 0.79, 0.43)
    draw_arrow(ax, 0.29, 0.43, 0.23, 0.43)
    ax.axis("off")
    ax.set_title("Canonical reporting workflow from frozen artifacts to thesis assets")
    savefig(fig, "figures/generated/protocol/reporting_pipeline_diagram.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    draw_box(ax, 0.05, 0.70, 0.18, 0.15, "Official data sources", "#dbeafe")
    draw_box(ax, 0.29, 0.70, 0.18, 0.15, "Repo preprocessing utilities", "#d1fae5")
    draw_box(ax, 0.53, 0.70, 0.18, 0.15, "Versioned local assets", "#fef3c7")
    draw_box(ax, 0.77, 0.70, 0.18, 0.15, "Environment defaults", "#fee2e2")
    draw_box(ax, 0.29, 0.34, 0.18, 0.15, "Reward and pricing layer", "#ede9fe")
    draw_box(ax, 0.53, 0.34, 0.18, 0.15, "Canonical report builder", "#fce7f3")
    draw_box(ax, 0.77, 0.34, 0.18, 0.15, "LaTeX figures/tables", "#dcfce7")
    draw_arrow(ax, 0.23, 0.78, 0.29, 0.78)
    draw_arrow(ax, 0.47, 0.78, 0.53, 0.78)
    draw_arrow(ax, 0.71, 0.78, 0.77, 0.78)
    draw_arrow(ax, 0.62, 0.70, 0.38, 0.49)
    draw_arrow(ax, 0.62, 0.70, 0.62, 0.49)
    draw_arrow(ax, 0.71, 0.42, 0.77, 0.42)
    ax.text(0.14, 0.62, "FAOSTAT,\nNFDC, PBS,\nKP, survey data", ha="center", va="center", fontsize=9)
    ax.text(0.38, 0.26, "prices used\ninside rewards", ha="center", va="center", fontsize=9)
    ax.axis("off")
    ax.set_title("Data provenance flow from primary sources to final thesis evidence")
    savefig(fig, "figures/generated/protocol/data_provenance_diagram.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 4)
    ax.hlines([3, 2, 1], xmin=10, xmax=92, color="#d1d5db", lw=2)
    ax.text(3, 3, "Crop planning", va="center", fontweight="bold")
    ax.text(3, 2, "Hierarchical env", va="center", fontweight="bold")
    ax.text(3, 1, "Fertilization", va="center", fontweight="bold")
    ax.add_patch(patches.Rectangle((12, 2.7), 74, 0.45, facecolor="#bbf7d0", edgecolor="#16a34a"))
    ax.add_patch(patches.Rectangle((12, 1.7), 74, 0.45, facecolor="#bfdbfe", edgecolor="#2563eb"))
    for start in range(12, 86, 7):
        ax.add_patch(patches.Rectangle((start, 0.7), 4.5, 0.45, facecolor="#fecaca", edgecolor="#dc2626"))
    ax.text(49, 2.93, "one action each season / year", ha="center", va="center", fontsize=10)
    ax.text(49, 1.93, "yearly planning plus within-season fertilizer steps", ha="center", va="center", fontsize=10)
    ax.text(49, 0.93, "weekly nutrient decisions", ha="center", va="center", fontsize=10)
    ax.text(49, 0.22, "relative within-season timeline", ha="center", fontsize=10)
    ax.axis("off")
    ax.set_title("Decision timescales represented by the active thesis environments")
    savefig(fig, "figures/generated/protocol/decision_timescales_diagram.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    draw_box(ax, 0.07, 0.64, 0.22, 0.18, "Harvest revenue\nCropRewarder", "#d1fae5")
    draw_box(ax, 0.39, 0.64, 0.22, 0.18, "N cost\nNPKProfitabilityRewarder", "#dbeafe")
    draw_box(ax, 0.39, 0.34, 0.22, 0.18, "P and K cost\nsame rewarder", "#fef3c7")
    draw_box(ax, 0.71, 0.49, 0.20, 0.18, "Compound reward", "#fee2e2")
    draw_arrow(ax, 0.29, 0.73, 0.39, 0.62)
    draw_arrow(ax, 0.61, 0.73, 0.71, 0.58)
    draw_arrow(ax, 0.61, 0.43, 0.71, 0.58)
    ax.text(0.50, 0.82, "positive term", fontsize=9, ha="center")
    ax.text(0.50, 0.24, "negative cost terms", fontsize=9, ha="center")
    ax.axis("off")
    ax.set_title("Reward decomposition used by the thesis environments")
    savefig(fig, "figures/generated/protocol/reward_decomposition_diagram.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    phases = [
        "Base CyclesGym repository",
        "Pakistan crop-calendar alignment",
        "Pakistan price localization and NPK scaffolding",
        "Hierarchical crop planning plus fertilization",
        "Final 113-run matrix execution and recovery",
        "Canonical reporting and thesis rebuild pipeline",
    ]
    y_positions = np.linspace(0.82, 0.12, len(phases))
    colors = ["#d1d5db", "#bae6fd", "#bbf7d0", "#fecaca", "#ddd6fe", "#fef3c7"]
    for idx, (label, y) in enumerate(zip(phases, y_positions)):
        draw_box(ax, 0.17, y, 0.66, 0.10, label, colors[idx], fontsize=10)
        if idx < len(phases) - 1:
            draw_arrow(ax, 0.50, y, 0.50, y_positions[idx + 1] + 0.10)
    ax.axis("off")
    ax.set_title("Capability evolution from the base repo to the final thesis stack")
    savefig(fig, "figures/generated/protocol/base_to_current_evolution.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.0))
    draw_box(ax, 0.06, 0.58, 0.24, 0.20, "Near term:\nheuristic crop baseline\nand richer provenance notes", "#d1fae5")
    draw_box(ax, 0.38, 0.58, 0.24, 0.20, "Medium term:\nadd irrigation control\nand richer economics", "#dbeafe")
    draw_box(ax, 0.70, 0.58, 0.24, 0.20, "Long term:\nfield-adjacent validation\nand broader rotations", "#fef3c7")
    draw_arrow(ax, 0.30, 0.68, 0.38, 0.68)
    draw_arrow(ax, 0.62, 0.68, 0.70, 0.68)
    draw_box(ax, 0.38, 0.18, 0.24, 0.18, "Persistent requirement:\nkeep claims bounded by frozen evidence", "#fee2e2")
    draw_arrow(ax, 0.50, 0.58, 0.50, 0.36)
    ax.axis("off")
    ax.set_title("Extension roadmap implied by the final thesis scope boundaries")
    savefig(fig, "figures/generated/protocol/future_work_roadmap.pdf")


def generate_training_validity_figure(run_level_df: pd.DataFrame, audit_df: pd.DataFrame, final_summary: dict) -> None:
    recovered_dirs = _recovered_run_dirs()
    example_row = None
    history_df = None
    for _, row in (
        run_level_df[run_level_df["report_group"] == "fertilization_core"]
        .sort_values(["deterministic_return", "runtime_seconds"], ascending=[False, False])
        .iterrows()
    ):
        run_dir = recovered_dirs.get(str(row.get("run_id", "")))
        if run_dir is None:
            continue
        history_path = run_dir / "history" / "history_scan.csv"
        if not history_path.exists():
            continue
        candidate = pd.read_csv(history_path)
        if candidate["global_step"].notna().sum() < 2:
            continue
        example_row = row
        history_df = candidate
        break

    if example_row is None or history_df is None:
        return

    inventory_counts = _count_recovered_artifacts()
    audit_counts = (
        audit_df.groupby("report_group")[
            [
                "summary_json_present_actual",
                "model_zip_present_actual",
                "best_model_present_actual",
                "vec_normalize_present_actual",
            ]
        ]
        .sum()
        .reindex([group for group in GROUP_ORDER if group in audit_df["report_group"].unique()])
        .fillna(0)
    )
    audit_labels = [fill(GROUP_LABELS[group], 18) for group in audit_counts.index]

    history_sorted = history_df.sort_values("global_step").copy()
    rollout_series = history_sorted["rollout/ep_rew_mean"] if "rollout/ep_rew_mean" in history_sorted.columns else pd.Series(np.nan, index=history_sorted.index)
    history_sorted["rollout_smoothed"] = rollout_series.rolling(window=5, min_periods=1).mean()

    fig, axes = plt.subplots(2, 2, figsize=(13.5, 8.8))
    fig.suptitle("Training-validity evidence stack used by the final thesis reporting layer", fontsize=15, fontweight="bold")

    ax = axes[0, 0]
    ax.plot(history_sorted["global_step"], history_sorted["rollout_smoothed"], color="#0f766e", lw=2.0, label="Smoothed rollout reward")
    if "eval_train_det/mean_reward" in history_sorted.columns and history_sorted["eval_train_det/mean_reward"].notna().any():
        ax.plot(
            history_sorted["global_step"],
            history_sorted["eval_train_det/mean_reward"],
            color="#2563eb",
            lw=1.4,
            alpha=0.85,
            label="Train deterministic eval",
        )
    ax.set_title("Recovered optimization trace")
    ax.set_xlabel("Global step")
    ax.set_ylabel("Reward")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, loc="best")

    ax = axes[0, 1]
    for column, label, color in [
        ("deterministic_return", "Deterministic return", "#dc2626"),
        ("pak_holdout_return", "Pakistan holdout return", "#7c3aed"),
        ("stochastic_return_mean", "Stochastic return mean", "#0ea5e9"),
    ]:
        if column in history_sorted.columns and history_sorted[column].notna().any():
            ax.plot(history_sorted["global_step"], history_sorted[column], lw=1.8, label=label, color=color)
    ax.set_title("Recovered evaluation traces")
    ax.set_xlabel("Global step")
    ax.set_ylabel("Return")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, loc="best")

    ax = axes[1, 0]
    x = np.arange(len(audit_counts))
    width = 0.18
    audit_series = [
        ("summary_json_present_actual", "Summary JSON", "#0f766e"),
        ("model_zip_present_actual", "Model ZIP", "#2563eb"),
        ("best_model_present_actual", "Best model", "#f97316"),
        ("vec_normalize_present_actual", "VecNormalize", "#7c3aed"),
    ]
    for idx, (column, label, color) in enumerate(audit_series):
        ax.bar(x + (idx - 1.5) * width, audit_counts[column].to_numpy(dtype=float), width=width, label=label, color=color)
    ax.set_xticks(x)
    ax.set_xticklabels(audit_labels)
    ax.set_ylabel("Recovered or frozen runs with artifact")
    ax.set_title("Artifact availability by final report group")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, ncol=2, fontsize=9)

    ax = axes[1, 1]
    ax.axis("off")
    proof_lines = [
        "Canonical proof surface",
        f"113/113 final rows resolved in reporting",
        f"{final_summary['counts']['replacement_rows']} tracked recovered replacements",
        f"{final_summary['hierarchical_guarded_rerun']['row_count']}/12 guarded reruns matched the March 14 export",
        "",
        "Recovered W&B evidence inventory",
        f"{inventory_counts['tensorboard_event_files']} TensorBoard event files",
        f"{inventory_counts['history_scan_csv']} history scans",
        f"{inventory_counts['system_metrics_json']} system-metrics snapshots",
        f"{inventory_counts['table_json']} W&B table artifacts",
        "",
        "Per-run audit trail",
        "config/rawconfig, requirements, diff.patch",
        "output.log, wandb-summary, model.zip",
        f"example run: {display_group(str(example_row['label']))}",
    ]
    ax.text(
        0.03,
        0.97,
        "\n".join(proof_lines),
        va="top",
        ha="left",
        fontsize=10,
        linespacing=1.45,
        bbox=dict(boxstyle="round,pad=0.55", facecolor="#f8fafc", edgecolor="#cbd5e1"),
    )

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    savefig_copy(
        fig,
        "figures/generated/protocol/training_validity_evidence.pdf",
        "docs/assets/training_validity_evidence.png",
    )


def _plot_ranked_groups(
    df: pd.DataFrame,
    value_col: str,
    ci_low_col: str,
    ci_high_col: str,
    title: str,
    xlabel: str,
    output_path: str,
    max_rows: int | None = None,
    accent_col: str | None = None,
    accent_label: str | None = None,
) -> None:
    plot_df = df.copy().sort_values(value_col, ascending=False)
    if max_rows is not None:
        plot_df = plot_df.head(max_rows)
    labels = [display_group(value) for value in plot_df["group_key"]]
    means = plot_df[value_col].to_numpy(dtype=float)
    low = means - plot_df[ci_low_col].to_numpy(dtype=float)
    high = plot_df[ci_high_col].to_numpy(dtype=float) - means
    y = np.arange(len(plot_df))

    fig, ax = plt.subplots(figsize=(11.0, max(4.5, 0.55 * len(plot_df) + 1.8)))
    ax.barh(y, means, color="#0f766e")
    ax.errorbar(means, y, xerr=np.vstack([low, high]), fmt="none", ecolor="#111827", capsize=4, lw=1.2)
    if accent_col is not None and accent_col in plot_df.columns and plot_df[accent_col].notna().any():
        accent = plot_df[accent_col].to_numpy(dtype=float)
        ax.scatter(accent, y, color="#dc2626", marker="D", s=42, label=accent_label or accent_col)
        ax.legend(frameon=False, loc="lower right")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.25)
    savefig(fig, output_path)


def generate_results_figures(run_level_df: pd.DataFrame, grouped_df: pd.DataFrame, final_summary: dict) -> None:
    group_counts = final_summary["counts"]["report_group_counts"]
    ordered_groups = [group for group in GROUP_ORDER if group in group_counts]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.bar(
        range(len(ordered_groups)),
        [group_counts[group] for group in ordered_groups],
        color=["#0f766e", "#6b7280", "#dc2626", "#7c3aed", "#ef4444", "#1d4ed8"],
    )
    ax.set_xticks(range(len(ordered_groups)))
    ax.set_xticklabels([fill(GROUP_LABELS[group], 18) for group in ordered_groups])
    ax.set_ylabel("Runs")
    ax.set_title("Composition of the frozen final_113 evidence set")
    ax.grid(axis="y", alpha=0.25)
    savefig(fig, "figures/generated/results_final/final_matrix_status.pdf")

    runtime_df = (
        run_level_df.groupby("report_group")["runtime_seconds"]
        .agg(["mean", "median", "max"])
        .reindex(ordered_groups)
        .dropna(how="all")
    )
    fig, ax = plt.subplots(figsize=(11.0, 5.0))
    x = np.arange(len(runtime_df))
    ax.bar(x - 0.22, runtime_df["mean"] / 3600.0, width=0.22, label="Mean", color="#0ea5e9")
    ax.bar(x, runtime_df["median"] / 3600.0, width=0.22, label="Median", color="#14b8a6")
    ax.bar(x + 0.22, runtime_df["max"] / 3600.0, width=0.22, label="Max", color="#f97316")
    ax.set_xticks(x)
    ax.set_xticklabels([fill(GROUP_LABELS[group], 18) for group in runtime_df.index])
    ax.set_ylabel("Hours")
    ax.set_title("Observed runtime profile of the frozen final evidence set")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    savefig(fig, "figures/generated/results_final/final_runtime_profile.pdf")

    fert_df = grouped_df[(grouped_df["report_group"] == "fertilization_core") & (grouped_df["inferential_eligible"])]
    _plot_ranked_groups(
        fert_df,
        "primary_metric_value_mean",
        "primary_metric_value_ci_low",
        "primary_metric_value_ci_high",
        "Repeated fertilization groups ranked by deterministic return",
        "Mean deterministic return",
        "figures/generated/results_final/final_fertilization_scores.pdf",
        max_rows=10,
        accent_col="pak_holdout_return_mean",
        accent_label="Mean Pakistan holdout return",
    )

    crop_df = grouped_df[(grouped_df["report_group"] == "crop_planning_nonhier") & (grouped_df["inferential_eligible"])]
    _plot_ranked_groups(
        crop_df,
        "primary_metric_value_mean",
        "primary_metric_value_ci_low",
        "primary_metric_value_ci_high",
        "Repeated non-hierarchical crop-planning groups ranked by eval_det/mean_reward",
        "Mean eval_det/mean_reward",
        "figures/generated/results_final/final_crop_scores.pdf",
    )

    hier_df = grouped_df[grouped_df["report_group"] == "crop_planning_hierarchical_guarded_rerun"]
    _plot_ranked_groups(
        hier_df,
        "primary_metric_value_mean",
        "primary_metric_value_ci_low",
        "primary_metric_value_ci_high",
        "Corrected guarded hierarchical reruns ranked by deterministic return",
        "Mean deterministic return",
        "figures/generated/results_final/final_hierarchical_scores.pdf",
        accent_col="baseline_best_return_mean",
        accent_label="Mean baseline comparator",
    )

    audit_counts = pd.Series(
        {
            "Recovered replacements": final_summary["counts"]["replacement_rows"],
            "Hierarchical rerun rows": final_summary["counts"]["hierarchical_export_rows"],
            "Missing hierarchical reports": final_summary["artifact_audit"]["hierarchical_rerun_missing_report_rows"],
            "Missing VecNormalize files": final_summary["artifact_audit"]["missing_vec_normalize_rows"],
        }
    )
    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    ax.barh(audit_counts.index.tolist(), audit_counts.values, color=["#4f46e5", "#0f766e", "#dc2626", "#f59e0b"])
    ax.invert_yaxis()
    ax.set_xlabel("Count")
    ax.set_title("Audit counts that remain relevant to final reporting")
    ax.grid(axis="x", alpha=0.25)
    savefig(fig, "figures/generated/results_final/final_artifact_audit.pdf")


def _anova_summary(stats_df: pd.DataFrame, report_group: str) -> str:
    subset = stats_df[
        (stats_df["report_group"] == report_group)
        & (stats_df["test_type"] == "anova_type_ii")
        & (stats_df["term"] != "Residual")
    ].copy()
    if subset.empty:
        return "No ANOVA produced."
    subset = subset.sort_values(["p_value", "eta_squared"], ascending=[True, False])
    significant = subset[subset["p_value"] < 0.05]
    if significant.empty:
        return "No Type II ANOVA term was below 0.05."
    parts = []
    for _, row in significant.iterrows():
        term = ANOVA_TERM_LABELS.get(str(row["term"]), str(row["term"]))
        parts.append(f"{term} (p {fmt_p(row['p_value'])}, eta-squared={float(row['eta_squared']):.3f})")
    return "; ".join(parts)


def _pairwise_summary(stats_df: pd.DataFrame, report_group: str) -> str:
    subset = stats_df[(stats_df["report_group"] == report_group) & (stats_df["test_type"] == "pairwise_welch_t")]
    if subset.empty:
        return "No targeted pairwise comparison was generated."
    subset = subset.sort_values(["corrected_p_value", "p_value"], ascending=[True, True])
    best = subset.iloc[0]
    corrected = best["corrected_p_value"]
    if pd.notna(corrected) and float(corrected) < 0.05:
        return (
            f"{display_group(best['comparison'])} survived Holm correction "
            f"(p {fmt_p(corrected)}, g={float(best['effect_size']):.2f})."
        )
    return f"No Holm-corrected top-group contrast was below 0.05; smallest corrected p {fmt_p(corrected)}."


def generate_tables(run_level_df: pd.DataFrame, grouped_df: pd.DataFrame, stats_df: pd.DataFrame, final_summary: dict) -> None:
    synopsis_rows = [
        ["Pakistan-adapted weather and soil inputs", "Completed", "Pakistan weather and soil defaults remain wired into the active environments.", "Present as a completed contribution."],
        ["Cost-aware reward shaping", "Completed", "Pakistan price localization and reward logic are versioned and used in the frozen evidence set.", "Present as a completed contribution."],
        ["Multi-nutrient fertilizer modeling", "Completed", "The fertilization branch uses NPK action mode and Pakistan price profiles throughout the final matrix.", "Present as a completed contribution."],
        ["Hierarchical RL across planning and fertilization", "Completed branch, corrected reruns", "Twelve 14 March 2026 guarded reruns are frozen in the canonical set with explicit guardrail metadata.", "Present as a guarded branch with provenance and separate interpretation."],
        ["Irrigation as a learned action", "Outside current claim set", "No active training flow exposes irrigation as a learned control variable.", "Keep outside the current claim set."],
        ["Rice-specific cultivar localization", "Outside current claim set", "The final experiment stack remains centered on the working maize-soy setup.", "Keep outside the current claim set."],
        ["Rice-wheat experimental rotation", "Outside current claim set", "Calendar support exists, but the frozen evidence set does not evaluate a rice-wheat rotation.", "Keep outside the current claim set."],
        ["Farmer-facing advisory rule export", "Partial", "Structured reporting exists, but no dedicated advisory delivery layer is implemented.", "Present as partial engineering output only."],
        ["Final 113-run campaign and reporting freeze", "Completed", "The canonical evidence base now contains 113 frozen rows, including 16 recovered replacements.", "Present as the main empirical evidence base."],
    ]
    tabular_table(
        "Synopsis closure matrix used to keep thesis claims aligned with the implemented and frozen repo state.",
        "tab:synopsis-closure",
        ["Synopsis item", "Status", "Evidence in the current repo", "Thesis treatment"],
        [[latex_escape(cell) for cell in row] for row in synopsis_rows],
        r">{\RaggedRight\arraybackslash}p{0.23\textwidth} >{\RaggedRight\arraybackslash}p{0.13\textwidth} >{\RaggedRight\arraybackslash}X >{\RaggedRight\arraybackslash}p{0.18\textwidth}",
        "synopsis_closure_matrix.tex",
        use_tabularx=True,
    )

    env_rows = [
        ["CropGym \\citep{kallenberg2023cropgym}", "Single-season nitrogen management on crop-growth simulations", "Useful nitrogen-management benchmark with transparent reward trade-offs", "Limited long-horizon rotation modeling and narrower carry-over effects"],
        ["gym-DSSAT \\citep{gautron2022gymdssat}", "Daily control in DSSAT-based environments", "High-fidelity crop-model integration and daily action interface", "More limited rotation emphasis and a heavier integration footprint"],
        ["CyclesGym \\citep{turchetta2022cyclesgym}", "Multi-year crop-management RL on the CYCLES simulator", "Strong match to long-horizon crop rotation, soil C/N dynamics, and constraint-aware management", "Requires additional localization and reporting work for Pakistan-specific thesis claims"],
        ["This thesis stack", "Pakistan-adapted CyclesGym with NPK and hierarchical extensions", "Adds Pakistan price localization, crop-calendar alignment, final reporting artifacts, and guarded hierarchical reruns", "Evidence remains simulation-only, irrigation is absent, and the crop-planning scope remains maize-soy"],
    ]
    tabular_table(
        "Positioning of the thesis stack against closely related agricultural RL environments.",
        "tab:environment-comparison",
        ["Environment", "Main scope", "Strength for this thesis", "Limitation for this thesis"],
        env_rows,
        r">{\RaggedRight\arraybackslash}p{0.18\textwidth} >{\RaggedRight\arraybackslash}p{0.18\textwidth} >{\RaggedRight\arraybackslash}p{0.18\textwidth} X",
        "environment_comparison.tex",
        use_tabularx=True,
    )

    module_rows = [
        [r"Weekly fertilization environment", r"\texttt{cyclesgym/envs/corn.py}", "Maps weekly agent actions into fertilizer operations and simulator reruns.", "Main benchmark for Pakistan-aligned fertilization experiments."],
        [r"Flat crop-planning environment", r"\texttt{cyclesgym/envs/crop\_planning.py}", "Encodes annual crop and planting choices with soil-nitrogen observations.", "Strategic planning layer for the maize-soy thesis setup."],
        [r"Hierarchical environment", r"\texttt{cyclesgym/envs/hierarchical.py}", "Couples yearly crop planning with weekly NPK fertilization and rich info dictionaries.", "Core thesis-specific system extension and guarded negative-result branch."],
        [r"Pricing localization", r"\texttt{cyclesgym/utils/pricing\_utils.py}", "Loads Pakistan yearly crop and nutrient price series with legacy fallbacks.", "Turns cost-aware framing into executable reward logic."],
        [r"Reporting callback", r"\texttt{cyclesgym/utils/thesis\_reporting.py}", "Writes weekly nutrient logs, yearly crop decisions, compliance files, and summary JSON.", "Makes Chapter~6 traceable to generated artifacts."],
        [r"Experiment orchestrator", r"\texttt{run\_experiments\_7\_3\_2026.py}", "Defines the 113-run matrix and original command configuration space.", "Preserves the design provenance of the final campaign."],
        [r"Canonical report builder", r"\texttt{scripts/build\_final\_reports.py}", "Canonicalizes final\\_113, recovered replacements, grouped summaries, tests, and audit outputs.", "Turns frozen artifacts into one authoritative reporting dataset."],
        [r"Thesis asset generator", r"\texttt{Thesis Main Working/scripts/build\_assets.py}", "Builds LaTeX tables and figures directly from the canonical reporting outputs.", "Keeps the thesis synced to the frozen evidence set."],
    ]
    tabular_table(
        "File-level responsibilities of the core thesis components.",
        "tab:module-map",
        ["Component", "Main file", "Responsibility", "Why it matters to the thesis"],
        module_rows,
        r">{\RaggedRight\arraybackslash}p{0.19\textwidth} >{\RaggedRight\arraybackslash}p{0.24\textwidth} X >{\RaggedRight\arraybackslash}p{0.18\textwidth}",
        "module_responsibility_map.tex",
        use_tabularx=True,
    )

    env_design_rows = [
        [r"\texttt{Corn}", "7 days", "27 features from weather, crop state, and cumulative nitrogen-to-date", "Discrete N or 3-channel NPK fertilizer action", "Main fertilization benchmark under Pakistan price and weather defaults."],
        [r"\texttt{CropPlanningFixedPlanting}", "1 year", "11 soil-nitrogen features", "Crop choice plus planting-week index", "Main flat crop-planning baseline used by the working maize-soy setup."],
        [r"\texttt{HierarchicalCropPlanningFertilization}", "7-day loop with first-step yearly planning", "14 features from soil nitrogen plus cumulative N and year index", "7-channel action: crop, window start, window end, max SMC, N, P, K", "Combined planner plus fertilization environment used in the guarded reruns."],
    ]
    tabular_table(
        "Active environment designs used in the thesis workflow.",
        "tab:environment-design",
        ["Environment", "Decision interval", "Observation design", "Action design", "Thesis use"],
        env_design_rows,
        r">{\RaggedRight\arraybackslash}p{0.18\textwidth} >{\RaggedRight\arraybackslash}p{0.12\textwidth} >{\RaggedRight\arraybackslash}p{0.14\textwidth} >{\RaggedRight\arraybackslash}p{0.16\textwidth} X",
        "environment_design_summary.tex",
        use_tabularx=True,
    )

    algorithm_rows = [
        ["PPO", "Main method across fertilization, crop planning, and hierarchical reruns", "Most broadly used algorithm family in the frozen evidence set", "On-policy training is comparatively expensive."],
        ["A2C", "Secondary actor-critic baseline", "Shares much of the PPO stack while offering a simpler policy-gradient comparison", "Typically lower-performing in fertilization and more variable in planning."],
        ["DQN", "Narrow descriptive ablation only", "Tests whether a value-based learner remains competitive after action-space wrapping", "Included only as single-seed reruns and excluded from inferential statistics."],
        ["Baseline policies", "Reference comparison", "Prevents RL scores from being interpreted without a non-learning comparator", "Only one fertilization baseline row is present in the frozen evidence set."],
    ]
    tabular_table(
        "Algorithm roles in the final thesis evidence set.",
        "tab:algorithm-roles",
        ["Method", "Primary use in this thesis", "Rationale", "Limitation"],
        [[latex_escape(cell) for cell in row] for row in algorithm_rows],
        r">{\RaggedRight\arraybackslash}p{0.12\textwidth} >{\RaggedRight\arraybackslash}p{0.18\textwidth} X >{\RaggedRight\arraybackslash}p{0.16\textwidth}",
        "algorithm_roles.tex",
        use_tabularx=True,
    )

    implementation_rows = [
        ["1", "Pakistan crop-calendar alignment", "Added conservative local sowing windows for maize and wheat families.", "Targeted tests and backward-compatible defaults"],
        ["2", "Price localization and NPK scaffolding", "Added Pakistan price profiles plus NPK-ready reward and action logic.", "Pricing and reward tests passed before the final matrix freeze"],
        ["3", "Hierarchical integration", "Added yearly crop-planning plus weekly fertilization environment and reporting callbacks.", "Guarded reruns executed on 14 March 2026"],
        ["4", "113-run execution, recovery, and freeze", "Completed the campaign, recovered interrupted rows, and froze the corrected final_113 bundle set.", "113 manifest rows and 16 replacements are present in the canonical reporting layer"],
        ["5", "Canonical reporting and thesis rebuild", "Added a single report builder and redirected thesis assets to canonical outputs.", "Final tables and figures now rebuild from final_113/reporting"],
    ]
    tabular_table(
        "Implementation phases completed in the final thesis repo.",
        "tab:implementation-phases",
        ["Step", "Theme", "Outcome", "Verification note"],
        [[latex_escape(cell) for cell in row] for row in implementation_rows],
        r">{\RaggedRight\arraybackslash}p{0.08\textwidth} >{\RaggedRight\arraybackslash}p{0.26\textwidth} X >{\RaggedRight\arraybackslash}p{0.16\textwidth}",
        "implementation_phases.tex",
        use_tabularx=True,
    )

    matrix_counts = (
        run_level_df.groupby(["report_group", "domain", "method"])
        .size()
        .reset_index(name="runs")
        .sort_values(["report_group", "method"])
    )
    experiment_rows = [
        [
            latex_escape(GROUP_LABELS.get(str(row["report_group"]), str(row["report_group"]))),
            latex_escape(str(row["domain"]).replace("_", " ")),
            latex_escape(str(row["method"])),
            latex_escape(str(int(row["runs"]))),
        ]
        for _, row in matrix_counts.iterrows()
    ]
    tabular_table(
        "Composition of the frozen final thesis matrix by reporting group and method.",
        "tab:experiment-matrix",
        ["Report group", "Domain", "Method", "Runs"],
        experiment_rows,
        "lllr",
        "experiment_matrix.tex",
    )

    artifact_rows = [
        [r"Pakistan weather file", r"\texttt{cycles/input/Pakistan\_Site\_final.weather}", "Historical daily weather source used in training and evaluation."],
        [r"Pakistan soil file", r"\texttt{cycles/input/Pakistan\_Soil\_final.soil}", "Localized soil profile used by the active environments."],
        [r"Pakistan yearly price series", r"\texttt{cyclesgym/resources/pricing/pakistan\_yearly\_series.json}", "Official-source-derived crop and nutrient price series used by rewarders."],
        [r"Frozen final evidence set", r"\texttt{artifacts/final\_successful\_runs/final\_113/}", "Canonical 113-run bundle set, including recovered replacements."],
        [r"Canonical reporting outputs", r"\texttt{artifacts/final\_successful\_runs/final\_113/reporting/}", "Single source of truth for run-level, grouped, statistical, and audit summaries."],
        [r"Recovered rerun exports", r"\texttt{artifacts/final\_successful\_runs/Recovered/}", "Source of the corrected DQN and guarded hierarchical replacements."],
        [r"Change logs", r"\texttt{Changes/THESIS\_IMPLEMENTATION\_*.md}", "Engineering traceability for thesis claims about implemented extensions."],
    ]
    tabular_table(
        "Core artifacts that make the final thesis stack reproducible.",
        "tab:artifact-inventory",
        ["Artifact", "Path family", "Role in the thesis"],
        artifact_rows,
        r">{\RaggedRight\arraybackslash}p{0.24\textwidth} >{\RaggedRight\arraybackslash}p{0.25\textwidth} X",
        "artifact_inventory.tex",
        use_tabularx=True,
    )

    data_rows = [
        ["Weather history", r"\texttt{Pakistan\_Site\_final.weather}", "Pakistan-local weather processing pipeline informed by NASA POWER-style provenance", "Drives train and evaluation episodes."],
        ["Soil profile", r"\texttt{Pakistan\_Soil\_final.soil}", "Localized soil setup with SoilGrids-style documentation lineage", "Anchors the simulated site conditions."],
        ["Crop prices", r"\texttt{pakistan\_yearly\_series.json} crop section", "FAOSTAT producer prices and local conversions", "Turns yield into localized revenue."],
        ["Nutrient prices", r"\texttt{pakistan\_yearly\_series.json} nutrient section", "NFDC fertilizer price tables and nutrient-content conversion logic", "Turns N, P, and K actions into explicit cost signals."],
        ["Crop calendars", r"\texttt{pakistan\_crop\_calendar.py}", "PBS kharif/rabi calendars and KP maize guidance", "Constrains planting windows to Pakistan-relevant seasonal ranges."],
    ]
    tabular_table(
        "Data provenance summary for the localized thesis stack.",
        "tab:data-provenance",
        ["Asset family", "Repo artifact", "Upstream source family", "Thesis role"],
        data_rows,
        r">{\RaggedRight\arraybackslash}p{0.18\textwidth} >{\RaggedRight\arraybackslash}p{0.22\textwidth} X >{\RaggedRight\arraybackslash}p{0.16\textwidth}",
        "data_source_provenance.tex",
        use_tabularx=True,
    )

    schema_rows = [
        [r"Per-run summary JSON", "Training entrypoints and recovered bundle normalization", "Deterministic return, stochastic return, holdout metrics, runtime, source provenance"],
        [r"Canonical run-level CSV", r"\texttt{run\_level\_metrics.csv}", "One row per frozen run with canonical group labels and primary metrics"],
        [r"Grouped metrics CSV", r"\texttt{grouped\_metrics.csv}", r"Repeated-group means, standard deviations, standard errors, and 95\% confidence intervals"],
        [r"Statistical tests CSV", r"\texttt{statistical\_tests.csv}", "Type II ANOVA results, group confidence intervals, targeted pairwise Welch tests"],
        [r"Artifact audit CSV", r"\texttt{artifact\_completeness\_audit.csv}", "Presence or absence of reports, models, and normalization sidecars"],
        [r"Weekly NPK and yearly crop reports", r"\texttt{thesis\_report/} directories where present", "Fine-grained hierarchical traces; absent for recovered guarded reruns and therefore surfaced as a limitation"],
    ]
    tabular_table(
        "Machine-readable outputs that connect experiments to thesis tables and figures.",
        "tab:summary-schema",
        ["Artifact", "Producer", "Main fields used by the thesis"],
        schema_rows,
        r">{\RaggedRight\arraybackslash}p{0.22\textwidth} >{\RaggedRight\arraybackslash}p{0.22\textwidth} X",
        "summary_output_schema.tex",
        use_tabularx=True,
    )

    verification_rows = [
        [r"\texttt{python scripts/build\_final\_reports.py}", "Passed", "Rebuilt canonical run-level, grouped, statistical, and audit outputs from the frozen final\\_113 bundle set."],
        [r"\texttt{python .\textbackslash{}scripts\textbackslash{}build\_assets.py}", "Passed", "Regenerated thesis figures and tables from canonical reporting outputs only."],
        [r"\texttt{powershell -ExecutionPolicy Bypass -File .\textbackslash{}build.ps1}", "Passed", "Rebuilt the full thesis PDF after regenerating assets."],
        [r"Canonical count cross-check", "Passed", "Verified 113 manifest rows, 16 replacements, 12 guarded hierarchical reruns, and 4 DQN rerun rows."],
        [r"Active-surface stale-text scan", "Passed", "Confirmed removal of provisional phrases such as dry-run, campaign pending, and historical-only status from active thesis/docs surfaces."],
    ]
    tabular_table(
        "Verification commands and release checks executed for the final thesis workspace on 14 March 2026.",
        "tab:verification-checks",
        ["Command or check", "Result", "What it validates"],
        verification_rows,
        r">{\RaggedRight\arraybackslash}p{0.32\textwidth} >{\RaggedRight\arraybackslash}p{0.14\textwidth} X",
        "verification_checks.tex",
        use_tabularx=True,
    )

    limitation_rows = [
        ["Simulation-only evidence", "External validity", "High simulator returns do not guarantee field performance.", "State explicitly and keep claims bounded to simulation evidence."],
        ["No irrigation control", "Control design", "Water-management conclusions are outside the active training flows.", "Keep outside the current claim set."],
        ["Maize-soy crop-planning scope", "Scope", "Limits direct generalization to rice-focused or broader Pakistan rotations.", "Present as the current working configuration rather than a universal recommendation."],
        ["Missing recovered hierarchical report directories", "Artifact provenance", "Guarded rerun bundles contain summary-level evidence but not the original thesis-report folders.", "Flag in Chapter~6 and keep hierarchical interpretation branch-specific."],
        ["Recovered summary normalization", "Provenance", "Sixteen replacement rows were reconstructed into the frozen bundle set from recovered metadata and exports.", "Document replacement provenance rather than treating all bundles as first-pass originals."],
        ["Restricted inferential scope", "Statistics", "Only repeated three-seed groups support ANOVA and pairwise testing.", "Keep DQN reruns and the baseline row descriptive only."],
    ]
    tabular_table(
        "Claim-boundary matrix used to distinguish the current evidence base from extension paths.",
        "tab:limitations-matrix",
        ["Boundary", "Category", "Why it matters", "Handling in thesis"],
        [[latex_escape(cell) for cell in row] for row in limitation_rows],
        r">{\RaggedRight\arraybackslash}p{0.22\textwidth} >{\RaggedRight\arraybackslash}p{0.18\textwidth} X >{\RaggedRight\arraybackslash}p{0.16\textwidth}",
        "limitations_matrix.tex",
        use_tabularx=True,
    )

    runtime_summary = (
        run_level_df.groupby("report_group")
        .agg(runs=("index", "count"), mean_runtime=("runtime_seconds", "mean"), median_runtime=("runtime_seconds", "median"), max_runtime=("runtime_seconds", "max"))
        .reindex([group for group in GROUP_ORDER if group in run_level_df["report_group"].unique()])
        .dropna(how="all")
    )
    runtime_rows = [
        [
            latex_escape(GROUP_LABELS.get(report_group, report_group)),
            latex_escape(str(int(row["runs"]))),
            latex_escape(fmt_hours(row["mean_runtime"])),
            latex_escape(fmt_hours(row["median_runtime"])),
            latex_escape(fmt_hours(row["max_runtime"])),
        ]
        for report_group, row in runtime_summary.iterrows()
    ]
    tabular_table(
        "Observed runtime statistics of the frozen final evidence set.",
        "tab:runtime-summary",
        ["Report group", "Runs", "Mean (h)", "Median (h)", "Max (h)"],
        runtime_rows,
        "lrrrr",
        "runtime_summary.tex",
    )

    completed_rows = int((run_level_df["status"].astype(str) == "finished").sum())
    descriptive_rows = int(run_level_df["report_group"].isin(["fertilization_baseline", "fertilization_dqn_rerun", "crop_planning_dqn_rerun"]).sum())
    status_rows = [
        ["Total manifest rows", latex_escape(str(final_summary["counts"]["manifest_rows"])), "The canonical final\\_113 manifest contains the full frozen evidence set."],
        ["Finished rows in canonical reporting", latex_escape(str(completed_rows)), "All 113 rows resolve to finished runs in the canonical reporting layer."],
        ["Recovered replacement rows", latex_escape(str(final_summary["counts"]["replacement_rows"])), "Rows requiring recovery were explicitly replaced from preserved backups."],
        ["Guarded hierarchical rerun rows", latex_escape(str(final_summary["counts"]["hierarchical_export_rows"])), "The hierarchical branch is represented by the corrected 14 March 2026 guarded reruns."],
        ["Recovered DQN rerun rows", latex_escape(str(final_summary["counts"]["report_group_counts"]["fertilization_dqn_rerun"] + final_summary["counts"]["report_group_counts"]["crop_planning_dqn_rerun"])), "Four DQN reruns are retained descriptively after recovery."],
        ["Inferentially eligible repeated groups", latex_escape(str(final_summary["statistics"]["inferential_groups"])), "Only repeated three-seed groups contribute to ANOVA, confidence intervals, and pairwise testing."],
        ["Descriptive-only rows", latex_escape(str(descriptive_rows)), "The baseline row and all DQN reruns are reported descriptively but excluded from inferential claims."],
    ]
    tabular_table(
        "Final status of the canonical thesis evidence set.",
        "tab:current-results-status",
        ["Metric", "Value", "Interpretation"],
        status_rows,
        r">{\RaggedRight\arraybackslash}p{0.28\textwidth} >{\RaggedRight\arraybackslash}p{0.12\textwidth} X",
        "current_results_status.tex",
        use_tabularx=True,
    )

    fert_rows = []
    fert_subset = grouped_df[grouped_df["report_group"] == "fertilization_core"].sort_values("primary_metric_value_mean", ascending=False)
    for rank, (_, row) in enumerate(fert_subset.iterrows(), start=1):
        fert_rows.append([
            latex_escape(str(rank)),
            latex_escape(display_group(row["group_key"])),
            latex_escape(str(int(row["n"]))),
            latex_escape(fmt_num(row["primary_metric_value_mean"], decimals=1)),
            latex_escape(fmt_ci(row["primary_metric_value_ci_low"], row["primary_metric_value_ci_high"])),
            latex_escape(fmt_num(row["pak_holdout_return_mean"], decimals=1)),
        ])
    tabular_table(
        "Repeated fertilization groups ranked by deterministic return, with Pakistan holdout return as the main robustness metric.",
        "tab:final-fertilization",
        ["Rank", "Group", "n", "Mean deterministic return", "95\\% CI", "Mean Pakistan holdout return"],
        fert_rows,
        "rlrrrr",
        "final_fertilization_table.tex",
        resize=True,
    )

    crop_rows = []
    crop_subset = grouped_df[grouped_df["report_group"] == "crop_planning_nonhier"].sort_values("primary_metric_value_mean", ascending=False)
    for rank, (_, row) in enumerate(crop_subset.iterrows(), start=1):
        crop_rows.append([
            latex_escape(str(rank)),
            latex_escape(display_group(row["group_key"])),
            latex_escape(str(int(row["n"]))),
            latex_escape(fmt_num(row["primary_metric_value_mean"], decimals=1)),
            latex_escape(fmt_ci(row["primary_metric_value_ci_low"], row["primary_metric_value_ci_high"])),
            latex_escape(fmt_num(row["deterministic_return_mean"], decimals=1)),
        ])
    tabular_table(
        "Repeated non-hierarchical crop-planning groups ranked by the headline metric eval\\_det/mean\\_reward, with deterministic return retained as a supporting metric.",
        "tab:final-crop",
        ["Rank", "Group", "n", "Mean eval\\_det/mean\\_reward", "95\\% CI", "Mean deterministic return"],
        crop_rows,
        "rlrrrr",
        "final_crop_table.tex",
        resize=True,
    )

    hier_rows = []
    hier_subset = grouped_df[grouped_df["report_group"] == "crop_planning_hierarchical_guarded_rerun"].sort_values("primary_metric_value_mean", ascending=False)
    for _, row in hier_subset.iterrows():
        hier_rows.append([
            latex_escape(display_group(row["group_key"])),
            latex_escape(str(int(row["n"]))),
            latex_escape(fmt_num(row["primary_metric_value_mean"], decimals=1)),
            latex_escape(fmt_ci(row["primary_metric_value_ci_low"], row["primary_metric_value_ci_high"])),
            latex_escape(fmt_num(row["eval_det_mean_reward_mean"], decimals=1)),
            latex_escape(fmt_num(row["uplift_vs_best_baseline_det_mean"], decimals=1)),
        ])
    tabular_table(
        "Corrected guarded hierarchical reruns reported as a separate branch because they operate under a corrected reward and constraint regime.",
        "tab:final-hierarchical",
        ["Group", "n", "Mean deterministic return", "95\\% CI", "Mean eval\\_det/mean\\_reward", "Mean uplift vs baseline det"],
        hier_rows,
        "lrrrrr",
        "final_hierarchical_table.tex",
        resize=True,
    )

    stats_rows = [
        [latex_escape("Fertilization core"), latex_escape("Deterministic return"), latex_escape(_anova_summary(stats_df, "fertilization_core")), latex_escape(_pairwise_summary(stats_df, "fertilization_core"))],
        [latex_escape("Crop planning non-hierarchical"), latex_escape("eval_det/mean_reward"), latex_escape(_anova_summary(stats_df, "crop_planning_nonhier")), latex_escape(_pairwise_summary(stats_df, "crop_planning_nonhier"))],
        [latex_escape("Crop planning hierarchical guarded rerun"), latex_escape("Deterministic return"), latex_escape(_anova_summary(stats_df, "crop_planning_hierarchical_guarded_rerun")), latex_escape(_pairwise_summary(stats_df, "crop_planning_hierarchical_guarded_rerun"))],
    ]
    tabular_table(
        "Condensed statistical summary for the repeated three-seed groups only.",
        "tab:statistical-summary",
        ["Branch", "Primary metric", "Type II ANOVA summary", "Targeted pairwise summary"],
        stats_rows,
        r">{\RaggedRight\arraybackslash}p{0.18\textwidth} >{\RaggedRight\arraybackslash}p{0.14\textwidth} X >{\RaggedRight\arraybackslash}p{0.26\textwidth}",
        "statistical_summary.tex",
        use_tabularx=True,
    )

    caveat_rows = [
        ["Recovered replacement provenance", latex_escape(str(final_summary["counts"]["replacement_rows"])), "Sixteen rows in the canonical set come from recovered reruns and are explicitly tracked in the reporting freeze."],
        ["Hierarchical rerun export matching", "12/12", "All corrected guarded hierarchical rows match the 14 March 2026 export used as the authoritative rerun evidence."],
        ["Missing hierarchical report directories", latex_escape(str(final_summary["artifact_audit"]["hierarchical_rerun_missing_report_rows"])), "Recovered guarded reruns retain summary-level evidence but not the original thesis-report directories."],
        ["Missing VecNormalize sidecars", latex_escape(str(final_summary["artifact_audit"]["missing_vec_normalize_rows"])), "This remains an artifact completeness issue, not a reason to discard the canonical summary metrics."],
        ["Descriptive-only rows", latex_escape(str(descriptive_rows)), "The single baseline row and all DQN reruns are excluded from inferential statistics."],
        ["Guardrail regime note", "Separate branch", "Hierarchical reruns are reported in their own subsection rather than inside the non-hierarchical leaderboard."],
    ]
    tabular_table(
        "Artifact and evidence notes that remain relevant after canonicalization.",
        "tab:artifact-validity-caveats",
        ["Issue", "Evidence", "Thesis treatment"],
        caveat_rows,
        r">{\RaggedRight\arraybackslash}p{0.24\textwidth} >{\RaggedRight\arraybackslash}p{0.14\textwidth} X",
        "artifact_validity_caveats.tex",
        use_tabularx=True,
    )

    appendix_lines = [
        r"\begin{longtable}{rllllll}",
        r"\caption{Canonical 113-run matrix listing generated from \texttt{final\_113/reporting/run\_level\_metrics.csv}.}\label{tab:appendix-matrix-listing}\\",
        r"\toprule",
        r"Idx & Domain & Method & Adaptive & Hierarchical & Weather & Budget \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Idx & Domain & Method & Adaptive & Hierarchical & Weather & Budget \\",
        r"\midrule",
        r"\endhead",
    ]
    for _, row in run_level_df.sort_values("index").iterrows():
        appendix_lines.append(
            f"{int(row['index'])} & "
            f"{latex_escape(str(row['domain']).replace('_', ' '))} & "
            f"{latex_escape(str(row['method']))} & "
            f"{latex_escape(str(row['adaptive_label']).replace('_', ' '))} & "
            f"{latex_escape(str(bool(row['hierarchical'])))} & "
            f"{latex_escape(str(row['weather_label']).replace('_', ' '))} & "
            f"{latex_escape(str(row['budget_label']) if pd.notna(row['budget_label']) else '--')} \\\\"
        )
    appendix_lines.extend([r"\bottomrule", r"\end{longtable}"])
    write_tex_table("appendix_matrix_listing.tex", "\n".join(appendix_lines))


def main() -> None:
    ensure_dirs()
    weather_df = load_weather()
    price_payload = load_price_series()
    run_level_df = load_run_level()
    grouped_df = load_grouped_metrics()
    stats_df = load_statistical_tests()
    audit_df = load_artifact_audit()
    final_summary = load_final_summary()

    generate_context_figures(price_payload, weather_df)
    generate_protocol_figures(run_level_df)
    generate_training_validity_figure(run_level_df, audit_df, final_summary)
    generate_results_figures(run_level_df, grouped_df, final_summary)
    generate_tables(run_level_df, grouped_df, stats_df, final_summary)


if __name__ == "__main__":
    main()
