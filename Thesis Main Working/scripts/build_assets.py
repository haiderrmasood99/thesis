from __future__ import annotations

import json
from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd


THESIS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
FIG_ROOT = THESIS_ROOT / "figures" / "generated"
TAB_ROOT = THESIS_ROOT / "tables" / "generated"


def ensure_dirs() -> None:
    for subdir in [
        FIG_ROOT / "context",
        FIG_ROOT / "protocol",
        FIG_ROOT / "results_historical",
        TAB_ROOT,
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


def load_latest_matrix() -> pd.DataFrame:
    path = REPO_ROOT / "runs" / "experiment_summaries" / "run_experiments_7_3_2026_summary.csv"
    return pd.read_csv(path)


def load_historical_fertilization() -> pd.DataFrame:
    path = REPO_ROOT / "Experimentation and Results" / "artifacts" / "fertilization_grouped_latest_success.csv"
    return pd.read_csv(path)


def load_historical_crop() -> pd.DataFrame:
    path = REPO_ROOT / "Experimentation and Results" / "artifacts" / "crop_grouped_latest_success.csv"
    return pd.read_csv(path)


def load_failure_counts() -> pd.DataFrame:
    path = REPO_ROOT / "Experimentation and Results" / "artifacts" / "failure_signature_counts.csv"
    return pd.read_csv(path)


def load_historical_runtime() -> pd.DataFrame:
    path = REPO_ROOT / "Experimentation and Results" / "artifacts" / "wandb_runs_aggregated_enriched.csv"
    return pd.read_csv(path)


def savefig(fig: plt.Figure, relative_path: str) -> None:
    out_path = THESIS_ROOT / relative_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def wrap(text: str, width: int = 18) -> str:
    return fill(text, width=width)


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


def write_tex_table(filename: str, body: str) -> None:
    (TAB_ROOT / filename).write_text(body.strip() + "\n", encoding="utf-8")


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
        lns, lbs = axis.get_legend_handles_labels()
        lines.extend(lns)
        labels.extend(lbs)
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
        lns, lbs = axis.get_legend_handles_labels()
        lines.extend(lns)
        labels.extend(lbs)
    ax1.legend(lines, labels, frameon=False, loc="upper right")
    ax1.set_title("Monthly climatology implied by the Pakistan weather file")
    ax1.grid(alpha=0.15)
    savefig(fig, "figures/generated/context/pakistan_monthly_climatology.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 3.5))
    ax.set_xlim(1, 365)
    ax.set_ylim(0, 3)
    ax.set_yticks([1, 2])
    ax.set_yticklabels(["WinterWheat", "Corn family"])
    ax.set_xticks([1, 60, 121, 182, 244, 305, 365])
    ax.set_xlabel("Day of year")
    ax.set_title("Pakistan crop-calendar windows currently enforced in the thesis repo")
    ax.barh(1, 334 - 305, left=305, height=0.35, color="#f59e0b", alpha=0.85)
    ax.barh(2, 196 - 166, left=166, height=0.35, color="#16a34a", alpha=0.85)
    ax.text(319.5, 1, "Nov 1-30", ha="center", va="center", fontsize=10)
    ax.text(181, 2, "Mid Jun-Mid Jul", ha="center", va="center", fontsize=10)
    ax.grid(axis="x", alpha=0.25)
    savefig(fig, "figures/generated/context/pakistan_crop_calendar_windows.pdf")


def generate_protocol_figures(matrix_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    counts = (
        matrix_df.groupby(["domain", "method"])
        .size()
        .reset_index(name="count")
        .sort_values(["domain", "method"])
    )
    domains = counts["domain"].unique().tolist()
    methods = counts["method"].unique().tolist()
    x = np.arange(len(domains))
    width = 0.18
    colors = {"PPO": "#0f766e", "A2C": "#1d4ed8", "DQN": "#dc2626", "BASELINE": "#6b7280"}
    for idx, method in enumerate(methods):
        vals = []
        for domain in domains:
            row = counts[(counts["domain"] == domain) & (counts["method"] == method)]
            vals.append(int(row["count"].iloc[0]) if not row.empty else 0)
        offset = idx * width - width * (len(methods) - 1) / 2
        ax.bar(x + offset, vals, width=width, label=method, color=colors.get(method, "#111827"))
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace("_", " ").title() for d in domains])
    ax.set_ylabel("Jobs")
    ax.set_title("Latest NPK thesis matrix composition by domain and method")
    ax.legend(frameon=False, ncol=len(methods))
    ax.grid(axis="y", alpha=0.25)
    savefig(fig, "figures/generated/protocol/experiment_matrix_counts.pdf")

    budget_counts = matrix_df["budget"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    ax.barh(range(len(budget_counts)), budget_counts.values, color="#7c3aed")
    ax.set_yticks(range(len(budget_counts)))
    ax.set_yticklabels([fill(str(label), 22) for label in budget_counts.index])
    ax.set_xlabel("Jobs")
    ax.set_title("Budget distribution of the latest NPK experiment matrix")
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
    draw_box(ax, 0.54, 0.67, 0.18, 0.16, "Weekly NPK log", "#fef3c7")
    draw_box(ax, 0.79, 0.67, 0.16, 0.16, "Yearly crop decisions", "#fee2e2")
    draw_box(ax, 0.54, 0.35, 0.18, 0.16, "Season-window compliance", "#ede9fe")
    draw_box(ax, 0.79, 0.35, 0.16, 0.16, "Reporting summary JSON", "#fce7f3")
    draw_box(ax, 0.29, 0.35, 0.18, 0.16, "run_experiments summary CSV", "#e0f2fe")
    draw_box(ax, 0.05, 0.35, 0.18, 0.16, "LaTeX tables and figures", "#dcfce7")
    draw_arrow(ax, 0.23, 0.75, 0.29, 0.75)
    draw_arrow(ax, 0.47, 0.75, 0.54, 0.75)
    draw_arrow(ax, 0.47, 0.75, 0.79, 0.75)
    draw_arrow(ax, 0.47, 0.67, 0.61, 0.51)
    draw_arrow(ax, 0.47, 0.67, 0.86, 0.43)
    draw_arrow(ax, 0.29, 0.43, 0.23, 0.43)
    ax.axis("off")
    ax.set_title("Reporting and thesis-asset generation workflow")
    savefig(fig, "figures/generated/protocol/reporting_pipeline_diagram.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    draw_box(ax, 0.05, 0.70, 0.18, 0.15, "Official data sources", "#dbeafe")
    draw_box(ax, 0.29, 0.70, 0.18, 0.15, "Repo preprocessing utilities", "#d1fae5")
    draw_box(ax, 0.53, 0.70, 0.18, 0.15, "Versioned local assets", "#fef3c7")
    draw_box(ax, 0.77, 0.70, 0.18, 0.15, "Environment defaults", "#fee2e2")
    draw_box(ax, 0.29, 0.34, 0.18, 0.15, "Reward and pricing layer", "#ede9fe")
    draw_box(ax, 0.53, 0.34, 0.18, 0.15, "Runner summaries", "#fce7f3")
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
    ax.set_title("Data provenance flow from official sources to thesis evidence")
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
        "Reporting layer and standardized summaries",
        "Final run-readiness defaults",
    ]
    y_positions = np.linspace(0.82, 0.12, len(phases))
    colors = ["#d1d5db", "#bae6fd", "#bbf7d0", "#fecaca", "#ddd6fe", "#fef3c7"]
    for idx, (label, y) in enumerate(zip(phases, y_positions)):
        draw_box(ax, 0.17, y, 0.66, 0.10, label, colors[idx], fontsize=10)
        if idx < len(phases) - 1:
            draw_arrow(ax, 0.50, y, 0.50, y_positions[idx + 1] + 0.10)
    ax.axis("off")
    ax.set_title("Capability evolution from the original base repo to the thesis stack")
    savefig(fig, "figures/generated/protocol/base_to_current_evolution.pdf")

    fig, ax = plt.subplots(figsize=(10.5, 5.0))
    draw_box(ax, 0.06, 0.58, 0.24, 0.20, "Near term:\nfinish broad NPK matrix\nand regenerate Chapter 6", "#d1fae5")
    draw_box(ax, 0.38, 0.58, 0.24, 0.20, "Medium term:\nadd irrigation control\nand richer shock studies", "#dbeafe")
    draw_box(ax, 0.70, 0.58, 0.24, 0.20, "Long term:\nnew rotations,\nfield-adjacent validation", "#fef3c7")
    draw_arrow(ax, 0.30, 0.68, 0.38, 0.68)
    draw_arrow(ax, 0.62, 0.68, 0.70, 0.68)
    draw_box(ax, 0.38, 0.18, 0.24, 0.18, "Persistent requirement:\nkeep claims bounded by repo evidence", "#fee2e2")
    draw_arrow(ax, 0.50, 0.58, 0.50, 0.36)
    ax.axis("off")
    ax.set_title("Roadmap implied by the current thesis limitations")
    savefig(fig, "figures/generated/protocol/future_work_roadmap.pdf")

    status_counts = matrix_df["status"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.bar(status_counts.index.astype(str), status_counts.values, color="#1d4ed8")
    ax.set_ylabel("Jobs")
    ax.set_title("Current latest-NPK matrix status at thesis-build time")
    ax.grid(axis="y", alpha=0.25)
    savefig(fig, "figures/generated/protocol/latest_matrix_status.pdf")


def generate_historical_figures(
    fert_df: pd.DataFrame,
    crop_df: pd.DataFrame,
    failure_df: pd.DataFrame,
    runtime_df: pd.DataFrame,
) -> None:
    fert_plot = fert_df.copy()
    fert_plot["config"] = (
        fert_plot["method"]
        + " | "
        + fert_plot["nonadaptive"].astype(str)
        + " | "
        + fert_plot["fixed_weather"].astype(str)
        + " | "
        + fert_plot["total_years"].astype(str)
    )
    fert_plot = fert_plot.sort_values("mean_score", ascending=False)
    fig, ax = plt.subplots(figsize=(11.5, 6.0))
    ax.barh(fert_plot["config"], fert_plot["mean_score"], color="#0f766e")
    ax.invert_yaxis()
    ax.set_xlabel("Mean deterministic score")
    ax.set_title("Historical fertilization benchmark context from audited February 2026 runs")
    ax.grid(axis="x", alpha=0.25)
    savefig(fig, "figures/generated/results_historical/historical_fertilization_scores.pdf")

    crop_plot = crop_df.copy()
    crop_plot["config"] = (
        crop_plot["method"]
        + " | "
        + crop_plot["nonadaptive"].astype(str)
        + " | "
        + crop_plot["fixed_weather"].astype(str)
    )
    crop_plot = crop_plot.sort_values("mean_score", ascending=False)
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.barh(crop_plot["config"], crop_plot["mean_score"], color="#7c3aed")
    ax.invert_yaxis()
    ax.set_xlabel("Mean deterministic score")
    ax.set_title("Historical crop-planning benchmark context from audited February 2026 runs")
    ax.grid(axis="x", alpha=0.25)
    savefig(fig, "figures/generated/results_historical/historical_crop_scores.pdf")

    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.barh(failure_df["failure_signature"], failure_df["count"], color="#dc2626")
    ax.invert_yaxis()
    ax.set_xlabel("Count")
    ax.set_title("Observed failure signatures in the audited February 2026 experiments")
    ax.grid(axis="x", alpha=0.25)
    savefig(fig, "figures/generated/results_historical/historical_failure_signatures.pdf")

    runtime_ok = runtime_df[(runtime_df["status"] == "ok") & runtime_df["runtime_sec"].notna()].copy()
    runtime_ok["runtime_hr"] = runtime_ok["runtime_sec"] / 3600.0
    grouped = runtime_ok.groupby("domain")["runtime_hr"].agg(["mean", "median", "max"]).reset_index()
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    x = np.arange(len(grouped))
    ax.bar(x - 0.22, grouped["mean"], width=0.22, label="Mean", color="#0ea5e9")
    ax.bar(x, grouped["median"], width=0.22, label="Median", color="#14b8a6")
    ax.bar(x + 0.22, grouped["max"], width=0.22, label="Max", color="#f97316")
    ax.set_xticks(x)
    ax.set_xticklabels(grouped["domain"].str.replace("_", " ").str.title())
    ax.set_ylabel("Hours")
    ax.set_title("Historical runtime profile used to estimate the fresh campaign budget")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    savefig(fig, "figures/generated/results_historical/historical_runtime_profile.pdf")


def generate_tables(
    matrix_df: pd.DataFrame,
    fert_df: pd.DataFrame,
    crop_df: pd.DataFrame,
    failure_df: pd.DataFrame,
    runtime_df: pd.DataFrame,
) -> None:
    synopsis_closure = r"""
\begin{table}[H]
\centering
\caption{Synopsis closure matrix used to keep thesis claims aligned with the implemented repo state.}
\label{tab:synopsis-closure}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.23\textwidth} >{\RaggedRight\arraybackslash}p{0.13\textwidth} >{\RaggedRight\arraybackslash}X >{\RaggedRight\arraybackslash}p{0.18\textwidth}}
\toprule
Synopsis item & Status & Evidence in the current repo & Thesis treatment \\
\midrule
Pakistan-adapted weather and soil inputs & Implemented & Pakistan weather and soil files are wired into train and evaluation entrypoints. & Present as a completed contribution. \\
Cost-aware reward shaping & Implemented & Reward stack and Pakistan price profiles are implemented and tested. & Present as a completed contribution. \\
Multi-nutrient fertilizer modeling & Implemented & NPK action mode, price series, and reporting are implemented. & Present as a completed contribution. \\
Hierarchical RL across planning and fertilization & Implemented & Dedicated hierarchical environment and reporting callback exist. & Present as a completed contribution with explicit scope bounds. \\
Irrigation as a learned action & Not implemented & No active training flow exposes irrigation as a learned control variable. & Present as future work only. \\
Rice-specific cultivar localization & Not implemented & Current crop-planning stack uses the working maize-soy configuration. & Present as future work only. \\
Rice-wheat experimental rotation & Not implemented & Crop-calendar support exists, but the main experiment setup remains maize-soy. & Present as a deferred extension, not a result claim. \\
Farmer-facing advisory rule export & Partial & CSV-style reporting exists, but no polished advisory layer is implemented. & Present as partial engineering output. \\
Formal price- and climate-shock campaign & Partial & The matrix runner is ready, but the broad fresh NPK campaign is still pending at build time. & Present as a planned experiment campaign. \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("synopsis_closure_matrix.tex", synopsis_closure)

    env_comp = r"""
\begin{table}[H]
\centering
\caption{Positioning of the thesis stack against closely related agricultural RL environments.}
\label{tab:environment-comparison}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.18\textwidth} >{\RaggedRight\arraybackslash}p{0.18\textwidth} >{\RaggedRight\arraybackslash}p{0.18\textwidth} X}
\toprule
Environment & Main scope & Strength for this thesis & Limitation for this thesis \\
\midrule
CropGym \citep{kallenberg2023cropgym} & Single-season nitrogen management on crop-growth simulations & Useful nitrogen-management benchmark with transparent reward trade-offs & Limited long-horizon rotation modeling and narrower carry-over effects \\
gym-DSSAT \citep{gautron2022gymdssat} & Daily control in DSSAT-based environments & High-fidelity crop-model integration and daily action interface & More limited rotation emphasis and a heavier integration footprint \\
CyclesGym \citep{turchetta2022cyclesgym} & Multi-year crop-management RL on the CYCLES simulator & Strong match to long-horizon crop rotation, soil C/N dynamics, and constraint-aware management & Requires more engineering to localize data and reporting for Pakistan-specific thesis work \\
This thesis stack & Pakistan-adapted CyclesGym with NPK and hierarchical RL extensions & Adds Pakistan price localization, crop-calendar alignment, hierarchical integration, and thesis reporting outputs & Latest full broad NPK campaign still needs completion before final empirical claims are frozen \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("environment_comparison.tex", env_comp)

    module_map = r"""
\begin{table}[H]
\centering
\caption{File-level responsibilities of the core thesis components.}
\label{tab:module-map}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.19\textwidth} >{\RaggedRight\arraybackslash}p{0.24\textwidth} X >{\RaggedRight\arraybackslash}p{0.18\textwidth}}
\toprule
Component & Main file & Responsibility & Why it matters to the thesis \\
\midrule
Weekly fertilization environment & \texttt{cyclesgym/envs/corn.py} & Maps weekly agent actions into fertilizer operations and simulator reruns. & Main benchmark for Pakistan-aligned fertilization experiments. \\
Flat crop-planning environment & \texttt{cyclesgym/envs/crop\_planning.py} & Encodes annual crop and planting choices with soil-nitrogen observations. & Strategic planning layer for the maize-soy thesis setup. \\
Hierarchical environment & \texttt{cyclesgym/envs/hierarchical.py} & Couples yearly crop planning with weekly NPK fertilization and rich info dictionaries. & Core thesis-specific system extension. \\
Pricing localization & \texttt{cyclesgym/utils/pricing\_utils.py} & Loads Pakistan yearly crop and nutrient price series with legacy fallbacks. & Converts narrative cost-awareness into executable reward logic. \\
Reporting callback & \texttt{cyclesgym/utils/thesis\_reporting.py} & Writes weekly nutrient logs, yearly crop decisions, compliance files, and summary JSON. & Makes Chapter~6 traceable to generated artifacts. \\
Experiment orchestrator & \texttt{run\_experiments\_7\_3\_2026.py} & Builds the 113-job matrix and standardizes per-run summary outputs. & Defines the authoritative latest-NPK campaign. \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("module_responsibility_map.tex", module_map)

    env_design = r"""
\begin{table}[H]
\centering
\caption{Active environment designs used in the thesis workflow.}
\label{tab:environment-design}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.18\textwidth} >{\RaggedRight\arraybackslash}p{0.12\textwidth} >{\RaggedRight\arraybackslash}p{0.14\textwidth} >{\RaggedRight\arraybackslash}p{0.16\textwidth} X}
\toprule
Environment & Decision interval & Observation design & Action design & Thesis use \\
\midrule
\texttt{Corn} & 7 days & 27 features from weather, crop state, and cumulative nitrogen-to-date & Discrete N or 3-channel NPK fertilizer action & Main fertilization benchmark under Pakistan price and weather defaults. \\
\texttt{CropPlanningFixedPlanting} & 1 year & 11 soil-nitrogen features & Crop choice plus planting-week index & Main flat crop-planning baseline used by the working maize-soy setup. \\
\texttt{HierarchicalCropPlanningFertilization} & 7-day loop with first-step yearly planning & 14 features from soil nitrogen plus cumulative N and year index & 7-channel action: crop, window start, window end, max SMC, N, P, K & Thesis-specific combined planner plus fertilization environment with report-rich outputs. \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("environment_design_summary.tex", env_design)

    algorithm_roles = r"""
\begin{table}[H]
\centering
\caption{Algorithm roles in the latest thesis experiment matrix.}
\label{tab:algorithm-roles}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.12\textwidth} >{\RaggedRight\arraybackslash}p{0.18\textwidth} X >{\RaggedRight\arraybackslash}p{0.16\textwidth}}
\toprule
Method & Primary use in this thesis & Rationale & Limitation \\
\midrule
PPO & Main method across fertilization, crop planning, and hierarchical runs & Historically strongest method in repo audits and robust default for discrete policy optimization & On-policy training is comparatively expensive. \\
A2C & Secondary actor-critic baseline & Simpler policy-gradient baseline that shares much of the PPO stack & Usually less stable and lower performing than PPO in this repo. \\
DQN & Narrow ablation only & Tests whether a value-based learner remains competitive after action-space wrapping & Requires flattening MultiDiscrete actions and is more brittle in planning tasks. \\
Baseline policies & Reference comparison & Prevents RL scores from being interpreted without a non-learning point of comparison & Not intended to be a strong production policy family. \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("algorithm_roles.tex", algorithm_roles)

    implementation_phases = r"""
\begin{table}[H]
\centering
\caption{Implementation phases already completed in the current repo before the fresh broad experiment campaign.}
\label{tab:implementation-phases}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.08\textwidth} >{\RaggedRight\arraybackslash}p{0.26\textwidth} X >{\RaggedRight\arraybackslash}p{0.16\textwidth}}
\toprule
Step & Theme & Outcome & Verification note \\
\midrule
1 & Pakistan crop-calendar alignment & Added conservative local sowing windows for maize and wheat families. & Targeted tests and backward-compatible defaults \\
2 & Price localization and NPK scaffolding & Added Pakistan price profiles plus NPK-ready reward and action logic. & 21 targeted tests passed \\
3 & Hierarchical integration & Added yearly crop-planning plus weekly fertilization environment. & Full integration path stabilized across platforms \\
4 & Reporting and data hardening & Added structured reporting CSVs, yearly series generation, and standardized summary JSON outputs. & Full test suite passed at this stage \\
5 & Final NPK run readiness & Updated default training settings to Pakistan-aligned NPK mode and validated runner wiring. & 59 tests passed and dry-run matrix validated \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("implementation_phases.tex", implementation_phases)

    matrix_counts = (
        matrix_df.groupby(["domain", "method", "hierarchical"])
        .size()
        .reset_index(name="jobs")
        .sort_values(["domain", "method", "hierarchical"])
    )
    body = [
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Full broad latest-NPK matrix encoded in \texttt{run\_experiments\_7\_3\_2026.py}.}",
        r"\label{tab:experiment-matrix}",
        r"\begin{tabular}{lllr}",
        r"\toprule",
        r"Domain & Method & Hierarchical & Jobs \\",
        r"\midrule",
    ]
    for _, row in matrix_counts.iterrows():
        body.append(
            f"{row['domain'].replace('_', ' ')} & {row['method']} & {row['hierarchical']} & {int(row['jobs'])} \\\\"
        )
    body.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write_tex_table("experiment_matrix.tex", "\n".join(body))

    artifact_inventory = r"""
\begin{table}[H]
\centering
\caption{Core artifacts that make the thesis stack reproducible.}
\label{tab:artifact-inventory}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.24\textwidth} >{\RaggedRight\arraybackslash}p{0.20\textwidth} X}
\toprule
Artifact & Path family & Role in the thesis \\
\midrule
Pakistan weather file & \texttt{cycles/input/Pakistan\_Site\_final.weather} & Historical daily weather source used in training and evaluation. \\
Pakistan soil file & \texttt{cycles/input/Pakistan\_Soil\_final.soil} & Local soil profile used by the active environments. \\
Pakistan yearly price series & \texttt{cyclesgym/resources/pricing/pakistan\_yearly\_series.json} & Official-source-derived crop and nutrient price series. \\
Runner summary CSV & \texttt{runs/experiment\_summaries/run\_experiments\_7\_3\_2026\_summary.csv} & Authoritative latest-NPK experiment matrix definition. \\
Historical audit artifacts & \texttt{Experimentation and Results/artifacts/} & Historical benchmark context and failure audit. \\
Change logs & \texttt{Changes/THESIS\_IMPLEMENTATION\_*.md} & Engineering traceability for thesis claims about implemented extensions. \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("artifact_inventory.tex", artifact_inventory)

    data_provenance = r"""
\begin{table}[H]
\centering
\caption{Data provenance summary for the localized thesis stack.}
\label{tab:data-provenance}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.18\textwidth} >{\RaggedRight\arraybackslash}p{0.22\textwidth} X >{\RaggedRight\arraybackslash}p{0.16\textwidth}}
\toprule
Asset family & Repo artifact & Upstream source family & Thesis role \\
\midrule
Weather history & \texttt{Pakistan\_Site\_final.weather} & Pakistan-local weather processing pipeline informed by NASA POWER style provenance & Drives train and evaluation episodes. \\
Soil profile & \texttt{Pakistan\_Soil\_final.soil} & Localized soil setup with SoilGrids-style documentation lineage & Anchors the simulated site conditions. \\
Crop prices & \texttt{pakistan\_yearly\_series.json} crop section & FAOSTAT producer prices and local conversions & Turns yield into localized revenue. \\
Nutrient prices & \texttt{pakistan\_yearly\_series.json} nutrient section & NFDC fertilizer price tables and nutrient-content conversion logic & Turns N, P, and K actions into explicit cost signals. \\
Crop calendars & \texttt{pakistan\_crop\_calendar.py} & PBS kharif/rabi calendars and KP maize guidance & Constrains planting windows to Pakistan-relevant seasonal ranges. \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("data_source_provenance.tex", data_provenance)

    summary_schema = r"""
\begin{table}[H]
\centering
\caption{Machine-readable outputs that connect experiments to thesis tables and figures.}
\label{tab:summary-schema}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.20\textwidth} >{\RaggedRight\arraybackslash}p{0.18\textwidth} X}
\toprule
Artifact & Producer & Main fields used by the thesis \\
\midrule
Per-run summary JSON & training entrypoints and unified runner & deterministic return, stochastic return mean/std, baseline uplift, holdout return, status, runtime metadata \\
Unified summary CSV & \texttt{run\_experiments\_7\_3\_2026.py} & matrix coverage, method labels, domain, weather regime, seed, budget, status \\
Weekly NPK log & \texttt{HierarchicalThesisReportCallback} & timestep, date, nutrient masses, nutrient costs, crop label, planner-applied flag \\
Yearly crop decisions & \texttt{HierarchicalThesisReportCallback} & crop name, operation year, planting DOYs, compliance flags \\
Season-window compliance CSV & \texttt{HierarchicalThesisReportCallback} & yearly compliance counts and aggregate compliance rate \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("summary_output_schema.tex", summary_schema)

    verification_checks = r"""
\begin{table}[H]
\centering
\caption{Verification commands executed during the thesis workspace implementation on 8 March 2026.}
\label{tab:verification-checks}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.30\textwidth} >{\RaggedRight\arraybackslash}p{0.18\textwidth} X}
\toprule
Command & Result & What it validates \\
\midrule
\texttt{python -m unittest cyclesgym.tests.test\_thesis\_reporting -v} & Passed & Structured reporting files are written with the expected weekly, yearly, and compliance outputs. \\
\texttt{python -m unittest cyclesgym.tests.test\_pricing\_utils -v} & Passed & Pakistan price profiles load correctly and preserve year-varying crop and NPK series. \\
\texttt{python -m unittest cyclesgym.tests.test\_crop\_planning -v} & Passed & Crop-planning transitions remain stable after the thesis-localization changes. \\
\texttt{python -m unittest cyclesgym.tests.test\_hierarchical\_env -v} & Passed & The hierarchical environment applies yearly planning only when intended and preserves step semantics. \\
\texttt{powershell -ExecutionPolicy Bypass -File .\textbackslash{}Thesis Main Working\textbackslash{}build.ps1} & Passed & Figures, tables, bibliography, and the full thesis PDF rebuild from versioned assets. \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("verification_checks.tex", verification_checks)

    limitations_matrix = r"""
\begin{table}[H]
\centering
\caption{Limitations matrix used to distinguish current evidence boundaries from future work.}
\label{tab:limitations-matrix}
\begin{tabularx}{\textwidth}{>{\RaggedRight\arraybackslash}p{0.22\textwidth} >{\RaggedRight\arraybackslash}p{0.18\textwidth} X >{\RaggedRight\arraybackslash}p{0.14\textwidth}}
\toprule
Limitation & Category & Why it matters & Handling in thesis \\
\midrule
Fresh 113-job campaign not yet completed & Evidence & Final algorithm comparisons cannot yet be frozen & Keep Chapter~6 provisional and clearly staged. \\
Working crop setup remains maize-soy & Scope & Limits generalization to broader Pakistan rotations & Present as current experimental configuration, not universal recommendation. \\
Irrigation not exposed as learned action & Control design & Proposal-scale water-management claims are unsupported & Treat as future work only. \\
No field validation & External validity & Simulator success does not guarantee farm deployment success & State explicitly in limitations and roadmap. \\
Simplified economics beyond prices & Modeling realism & Profit-related reward omits wider farm logistics and market frictions & Limit claims to cost-aware simulation, not full farm economics. \\
\bottomrule
\end{tabularx}
\end{table}
"""
    write_tex_table("limitations_matrix.tex", limitations_matrix)

    runtime_ok = runtime_df[(runtime_df["status"] == "ok") & runtime_df["runtime_sec"].notna()].copy()
    runtime_ok["runtime_hr"] = runtime_ok["runtime_sec"] / 3600.0
    runtime_stats = runtime_ok.groupby("domain")["runtime_hr"].agg(["mean", "median", "max"]).reset_index()
    body = [
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Historical runtime statistics used to estimate the wall-clock budget of the fresh broad campaign.}",
        r"\label{tab:runtime-summary}",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Domain & Mean (h) & Median (h) & Max (h) \\",
        r"\midrule",
    ]
    for _, row in runtime_stats.iterrows():
        body.append(
            f"{row['domain'].replace('_', ' ').title()} & {row['mean']:.2f} & {row['median']:.2f} & {row['max']:.2f} \\\\"
        )
    body.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    write_tex_table("runtime_summary.tex", "\n".join(body))

    status_counts = matrix_df["status"].value_counts()
    current_status = rf"""
\begin{{table}}[H]
\centering
\caption{{Current status of the latest broad NPK matrix at the time of thesis build.}}
\label{{tab:current-results-status}}
\begin{{tabularx}}{{\textwidth}}{{>{{\RaggedRight\arraybackslash}}p{{0.25\textwidth}} >{{\RaggedRight\arraybackslash}}p{{0.12\textwidth}} X}}
\toprule
Metric & Value & Interpretation \\
\midrule
Total jobs encoded & {len(matrix_df)} & The runner defines the full broad experiment campaign requested for the thesis. \\
Current dry-run jobs & {int(status_counts.get('DRY_RUN', 0))} & The matrix has been materialized and audited, but not yet executed end-to-end at build time. \\
Completed latest-NPK jobs & 0 & No fresh broad-matrix result should be claimed as final evidence before execution. \\
Historical completed jobs & 44 & Older February 2026 runs remain useful only as historical benchmark context. \\
\bottomrule
\end{{tabularx}}
\end{{table}}
"""
    write_tex_table("current_results_status.tex", current_status)

    def simple_table_from_df(df: pd.DataFrame, caption: str, label: str, filename: str) -> None:
        cols = df.columns.tolist()
        col_spec = "l" * len(cols)
        lines = [
            r"\begin{table}[H]",
            r"\centering",
            rf"\caption{{{caption}}}",
            rf"\label{{{label}}}",
            r"\resizebox{\textwidth}{!}{%",
            rf"\begin{{tabular}}{{{col_spec}}}",
            r"\toprule",
            " & ".join(str(c).replace("_", r"\_") for c in cols) + r" \\",
            r"\midrule",
        ]
        for _, row in df.iterrows():
            vals = [latex_escape(v) for v in row.tolist()]
            lines.append(" & ".join(vals) + r" \\")
        lines.extend([r"\bottomrule", r"\end{tabular}", r"}", r"\end{table}"])
        write_tex_table(filename, "\n".join(lines))

    simple_table_from_df(
        fert_df.round(4),
        "Historical fertilization benchmarks from audited February 2026 runs.",
        "tab:historical-fert",
        "historical_fertilization_table.tex",
    )
    simple_table_from_df(
        crop_df.round(4),
        "Historical crop-planning benchmarks from audited February 2026 runs.",
        "tab:historical-crop",
        "historical_crop_table.tex",
    )
    simple_table_from_df(
        failure_df,
        "Historical failure signatures observed in the audited February 2026 runs.",
        "tab:historical-failure",
        "historical_failure_table.tex",
    )

    appendix_lines = [
        r"\begin{longtable}{rllllll}",
        r"\caption{Full broad latest-NPK matrix listing generated from the unified runner summary CSV.}\label{tab:appendix-matrix-listing}\\",
        r"\toprule",
        r"Idx & Domain & Method & Adaptive & Hierarchical & Weather & Budget \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Idx & Domain & Method & Adaptive & Hierarchical & Weather & Budget \\",
        r"\midrule",
        r"\endhead",
    ]
    for idx, row in matrix_df.iterrows():
        budget = latex_escape(row["budget"])
        appendix_lines.append(
            f"{idx + 1} & {latex_escape(row['domain'].replace('_', ' '))} & {latex_escape(row['method'])} & {latex_escape(row['adaptive'])} & {latex_escape(row['hierarchical'])} & {latex_escape(row['fixed_weather'])} & {budget} \\\\"
        )
    appendix_lines.extend([r"\bottomrule", r"\end{longtable}"])
    write_tex_table("appendix_matrix_listing.tex", "\n".join(appendix_lines))


def main() -> None:
    ensure_dirs()
    weather_df = load_weather()
    price_payload = load_price_series()
    matrix_df = load_latest_matrix()
    fert_df = load_historical_fertilization()
    crop_df = load_historical_crop()
    failure_df = load_failure_counts()
    runtime_df = load_historical_runtime()

    generate_context_figures(price_payload, weather_df)
    generate_protocol_figures(matrix_df)
    generate_historical_figures(fert_df, crop_df, failure_df, runtime_df)
    generate_tables(matrix_df, fert_df, crop_df, failure_df, runtime_df)


if __name__ == "__main__":
    main()

