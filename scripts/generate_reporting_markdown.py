#!/usr/bin/env python3
"""Generate folder-level README files and a final experiments reporting markdown."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from thesis_reporting_pack_lib import FINAL_SUCCESSFUL_RUNS_PATH


ROOT = FINAL_SUCCESSFUL_RUNS_PATH / "thesis_reporting_pack"
FINAL_REPORT = ROOT / "FINAL_EXPERIMENTS_REPORTING.md"
ARTIFACT_SUFFIXES = {".png", ".csv", ".json"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel_from_root(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def titleize(text: str) -> str:
    return text.replace("_", " ").replace("-", " ").strip().title()


def artifact_key(stem: str) -> str:
    parts = stem.split("__")
    return "__".join(parts[1:]) if len(parts) > 1 else stem


def companion_json(path: Path) -> Path:
    return path.with_suffix(".json")


def json_series_names(payload: dict[str, Any]) -> list[str]:
    return [str(item.get("name", "")) for item in payload.get("series", []) if item.get("name")]


def explain_figure(stem: str, payload: dict[str, Any]) -> tuple[str, str, str]:
    key = artifact_key(stem)
    series_names = ", ".join(json_series_names(payload)) or "the plotted series"
    if "training_reward_vs_global_step" in key:
        return (
            "The x-axis is global training step and the y-axis is mean rollout reward.",
            "This graph shows how average training return changed as optimization progressed.",
            "An upward slope indicates learning progress, a plateau indicates convergence, and sharp oscillations or collapses indicate instability or policy regression.",
        )
    if "episode_length_vs_global_step" in key:
        return (
            "The x-axis is global training step and the y-axis is mean episode length.",
            "This graph shows whether the agent is surviving longer or finishing episodes sooner during training.",
            "A rising curve usually means longer survival or longer task engagement, while sudden drops often indicate unstable behavior or early termination.",
        )
    if "primary_metric_vs_global_step" in key:
        return (
            f"The x-axis is global training step and the y-axis is the main evaluation metric logged for this run: {series_names}.",
            "This graph shows the most thesis-relevant performance signal over training rather than only raw rollout reward.",
            "A steadily increasing curve indicates that the trained policy is improving on the target evaluation criterion; a flat curve indicates saturation; noisy reversals indicate unstable generalization.",
        )
    if "diagnostics_panel" in key:
        return (
            f"The panel contains optimizer and learning diagnostics such as {series_names}.",
            "This graph shows whether PPO, A2C, or DQN updates remained numerically well-behaved during training.",
            "Smooth bounded traces usually indicate stable optimization, while spikes, drifting losses, or highly erratic traces indicate unstable updates or poor critic fitting.",
        )
    if "checkpoint_eval_curves" in key:
        return (
            f"The x-axis is checkpoint timestep and the y-axis is checkpoint mean reward for {series_names}.",
            "This graph shows how intermediate checkpoints performed on the saved evaluation sets.",
            "If later checkpoints dominate earlier ones, performance improved through training; if train curves rise while test curves stagnate, that suggests overfitting or weak transfer.",
        )
    if "weekly_npk_behavior" in key:
        return (
            "The x-axis is environment timestep and the y-axis is weekly applied or blocked N/P/K mass in kilograms.",
            "This graph shows how the hierarchical crop-planning policy requested, applied, or had fertilizer blocked over time.",
            "Spikes indicate concentrated fertilizer events, persistent blocked mass indicates repeated constraint violations in proposed actions, and low blocked mass with controlled applications indicates policy alignment with guardrails.",
        )
    if "crop_decision_timeline" in key:
        return (
            "The x-axis is operation year and the y-axis is the effective crop chosen for that year.",
            "This graph shows the sequence of crop choices produced after sanitization and guardrail application.",
            "Stable repeated patterns indicate a consistent policy preference, while abrupt switching or heavy sanitization would indicate unstable or poorly aligned planning behavior.",
        )
    if "compliance_summary" in key:
        return (
            "The x-axis is operation year and the y-axis is compliance rate for seasonal decision windows.",
            "This graph shows how often the crop-planning policy stayed inside the allowed decision windows each year.",
            "A flat line near 1.0 indicates robust constraint adherence, while dips reveal years where the policy or sanitizer had to correct invalid decisions.",
        )
    if "blocked_cost_summary" in key:
        return (
            "The bars summarize total cost, blocked fertilizer mass, compliance, and total blocked-penalty contribution.",
            "This graph shows the aggregate trade-off between economic cost, blocked nutrient attempts, and shaping penalties for one run.",
            "Higher blocked or penalty bars indicate that the policy is pushing harder against constraints; lower blocked mass with similar return indicates cleaner control.",
        )
    if "primary_render" in key:
        return (
            f"This render combines deterministic behavior traces and scalar summaries such as {series_names}.",
            "It is a compact policy-behavior panel intended for visual inspection rather than raw numeric comparison.",
            "Use the shape of the lines and the balance of the summary bars to see whether the policy behaves smoothly, whether actions cluster into a stable strategy, and whether the final metrics align with that behavior.",
        )
    if "leaderboard_primary_metric" in key:
        return (
            "The x-axis lists grouped experimental configurations and the y-axis is grouped mean primary performance.",
            "This graph ranks the best-performing grouped settings in the canonical 113-run pack.",
            "Taller bars indicate stronger average performance for that configuration; large gaps between bars indicate practically meaningful separation between design choices.",
        )
    if "grouped_comparison" in key:
        return (
            "The x-axis lists top runs and the y-axis is the primary metric value for each run.",
            "This graph compares the strongest individual learned runs directly.",
            "Taller bars indicate stronger final performance, while clustering of heights indicates that multiple settings perform similarly well.",
        )
    if "runtime_comparison" in key:
        return (
            "The x-axis lists groups or ablation points and the y-axis is mean wall-clock runtime in seconds.",
            "This graph shows computational cost rather than policy quality.",
            "Taller bars indicate more expensive runs; if two settings achieve similar reward but one has a much shorter runtime, that setting is operationally more efficient.",
        )
    if "uplift_vs_baseline" in key:
        return (
            "The x-axis lists experiment groups and the y-axis is mean uplift relative to the best available baseline.",
            "This graph shows whether learned policies are actually outperforming the baseline strategies.",
            "Bars above zero indicate improvement over baseline; bars below zero indicate that the learned policy failed to clear the baseline.",
        )
    if "artifact_completeness" in key:
        return (
            "The x-axis lists artifact classes and the y-axis counts how many runs have that artifact present.",
            "This graph shows evidence completeness rather than learning performance.",
            "Shorter bars identify missing evidence sources that can limit later re-analysis, rerendering, or reproduction work.",
        )
    if "point1_entropy_primary_metric" in key:
        return (
            "The x-axis is entropy coefficient and the y-axis is mean deterministic return, split by weather regime.",
            "This graph shows how increasing entropy regularization changed performance in the point1 fertilization ablation.",
            "An upward move from 0.0 to 0.01 means the extra exploration helped that weather regime; a downward move means it hurt final policy quality or slowed convergence.",
        )
    if "point1_entropy_paired_deltas" in key:
        return (
            "The bars show paired deterministic-return deltas for ent_coef=0.01 relative to ent_coef=0.0 within matched seed and weather settings.",
            "This graph isolates the causal direction of the entropy change by controlling for seed and weather.",
            "Bars above zero indicate improvement from more entropy; bars below zero indicate degradation.",
        )
    if "point2_primary_comparison" in key:
        return (
            "The x-axis is blocked nutrient penalty per kilogram and the y-axis is deterministic return, with separate lines for PPO and A2C.",
            "This graph shows how stronger blocked-fertilizer shaping changed hierarchical crop-planning performance.",
            "An upward slope means the shaping penalty helped that method; a downward slope means the penalty overconstrained the policy or distorted the reward too much.",
        )
    if "point2_thesis_compliance" in key:
        return (
            "The x-axis is blocked nutrient penalty per kilogram and the y-axis is overall compliance rate, split by method and weather.",
            "This graph shows whether the shaping penalty materially changed reported constraint adherence.",
            "A flat line near 1.0 means compliance was already saturated, so any return change came from reward shaping rather than improved rule-following.",
        )
    if "point3_cost_weight_primary_metric" in key:
        return (
            "The x-axis is nutrient cost weight and the y-axis is mean deterministic return, split by weather regime.",
            "This graph shows how aggressively penalizing fertilizer cost changed fertilization performance in point3.",
            "The peak of the curve indicates the best return-cost trade-off; lower values on either side indicate under- or over-penalizing nutrient cost.",
        )
    if "point3_cost_weight_paired_deltas" in key:
        return (
            "The bars show paired deterministic-return deltas for each cost weight relative to the baseline cost_weight=1.0.",
            "This graph isolates how changing nutrient cost weighting shifts return under matched seed and weather conditions.",
            "Positive bars indicate that the alternative weight outperformed the baseline; negative bars indicate that the baseline weight remained better.",
        )
    return (
        f"The plotted values come from {series_names}.",
        "This graph is one of the generated reporting figures for the thesis pack.",
        "Interpret the shape by checking whether the plotted series rises, falls, plateaus, or diverges across conditions, because those geometric changes correspond to improvement, degradation, convergence, or separation between settings.",
    )

def explain_table(stem: str, payload: dict[str, Any]) -> tuple[str, str]:
    key = artifact_key(stem)
    columns = ", ".join(payload.get("columns", [])[:10])
    if "run_catalog" in key:
        return (
            "This table is the canonical run index. It maps each run to its dataset, bundle, source history, method, seed, weather regime, and ablation parameters.",
            "Use it when you need to know which config produced a figure, which run id to trace back to W&B history, or which artifact set belongs to a reported conclusion.",
        )
    if "history_source_index" in key:
        return (
            "This table maps run_id values to the recovered W&B export folders used as the canonical history source.",
            "It is the provenance bridge between frozen bundles and the recovered step-level logs.",
        )
    if "artifact_availability" in key or "artifact_completeness" in key:
        return (
            "This table records which runs have models, normalization state, reports, evaluation archives, and other evidence artifacts available.",
            "It is the main completeness audit for later inference, rerendering, or statistical review work.",
        )
    if "representative_index" in key:
        return (
            "This table lists the representative renders copied into the curated representative-set folders and the reason each run was selected.",
            "Use it to justify why a render was labeled best, median, worst, or best/worst within a single-seed family.",
        )
    if "run_level_metrics" in key or "run_metrics" in key:
        return (
            "This table contains one row per run with the main scalar metrics, identifiers, and artifact presence flags.",
            "It is the main flat table for filtering runs, ranking them, and matching final performance back to configuration choices.",
        )
    if "grouped_metrics" in key:
        return (
            "This table aggregates repeated runs into grouped means, standard deviations, and confidence intervals.",
            "It is the correct source for configuration-level conclusions because it respects seed-level repetition instead of overinterpreting single runs.",
        )
    if "statistical_tests" in key or "paired_stats" in key:
        return (
            "This table contains inferential or paired-comparison statistics such as mean deltas, t-statistics, p-values, and group-wise significance summaries.",
            "Use it to separate descriptive trends from effects that are at least directionally supported by repeated-seed evidence.",
        )
    if "paired_deltas" in key:
        return (
            "This table contains matched within-seed deltas between two ablation settings, so each row isolates the effect of a single design change.",
            "Positive deltas indicate improvement over the control condition; negative deltas indicate degradation.",
        )
    if "weekly_npk_log" in key:
        return (
            "This table is the full step-level nutrient trace for a point2 hierarchical run, including requested fertilizer, applied fertilizer, blocked fertilizer, costs, rewards, and compliance flags.",
            "It is the source for the weekly N/P/K behavior plot and for diagnosing where shaping, blocking, or budget clipping changed behavior.",
        )
    if "yearly_crop_decisions" in key:
        return (
            "This table records the effective crop selected each operation year, alongside sanitization and window information.",
            "It supports the crop timeline plots and shows whether the policy settled into a stable yearly planning pattern.",
        )
    if "season_window_compliance" in key:
        return (
            "This table summarizes compliance by operation year.",
            "It is the compact numeric basis for the compliance plots and for proving whether guardrail adherence actually changed across ablation settings.",
        )
    if "history_selected" in key:
        return (
            f"This cache table contains the selected reporting history columns for one run. The first columns include: {columns}.",
            "It is the normalized per-run time series source used to generate the per-run training and evaluation figures.",
        )
    if "checkpoint_eval_curves" in key:
        return (
            "This table flattens evaluations.npz archives into checkpoint-level mean reward, variance, and episode length rows.",
            "It is the clean numerical source behind the checkpoint evaluation progression figures.",
        )
    if "runtime_summary" in key:
        return (
            "This table aggregates wall-clock runtime by group or ablation point.",
            "It supports computational-efficiency comparisons between settings that may have similar final return.",
        )
    if "uplift_vs_baseline" in key:
        return (
            "This table summarizes how much learned policies improved over the strongest baseline available to that task family.",
            "Use it to judge whether a policy is merely competent or actually better than the baseline policy class.",
        )
    return (
        f"This table stores reporting values and statistics. The leading columns are: {columns}.",
        "Read the rows as the numeric backbone behind the linked figures in the same directory.",
    )


def explain_json_only(stem: str, payload: dict[str, Any]) -> tuple[str, str]:
    if "build_summary" in stem:
        return (
            "This JSON is the top-level build manifest for the thesis reporting pack.",
            "It reports the final counts, generated artifacts, and validation status for the whole pack.",
        )
    if "build_verification" in stem:
        return (
            "This JSON records structural QA checks such as CSV/PNG companion JSON coverage and run-level metric JSON presence.",
            "Use it to confirm that the pack is internally consistent before citing figures or tables.",
        )
    if "smoke_tests" in stem:
        return (
            "This JSON records targeted smoke tests on representative runs and validates the point2 runs without vec_normalize as valid reporting targets.",
            "It is the quickest sanity check when you want to confirm the build is usable without reading every directory.",
        )
    if "final_reporting_summary" in stem:
        return (
            "This JSON is the summary conclusion block for the frozen 113-run report.",
            "It contains best groups, best single runs, artifact notes, and limitations used in the overall thesis interpretation.",
        )
    if "reporting_summary" in stem:
        return (
            "This JSON is the per-run point2 thesis summary, including compliance, blocked nutrient mass, and total cost.",
            "It is the compact explanation of what happened inside one hierarchical shaping run.",
        )
    if "run_metrics" in stem:
        return (
            "This JSON is the per-run scalar summary emitted for the reporting pack.",
            "It is the fastest single-file summary for one run when you do not need the full time series.",
        )
    if "missing_or_skipped" in stem:
        return (
            "This JSON records anything the reporting build intentionally skipped because the source artifact did not exist.",
            "Treat it as a gap log, not as a failure log: most entries reflect genuinely missing source data rather than a broken build.",
        )
    if "render_rebuild_summary" in stem:
        return (
            "This JSON records the standalone render-only rebuild execution.",
            "Use it to confirm that the render pipeline can be rerun independently of the full reporting build.",
        )
    return (
        "This JSON stores reporting metadata or numeric summaries for this directory.",
        "Use it as the machine-readable counterpart to the PNG or CSV artifacts in the same folder.",
    )


def inventory_line(directory: Path, pngs: list[Path], csvs: list[Path], json_only: list[Path]) -> list[str]:
    return [
        f"- Relative path: `{rel_from_root(directory)}`",
        f"- PNG figures/renders: `{len(pngs)}`",
        f"- CSV tables: `{len(csvs)}`",
        f"- JSON-only summary files: `{len(json_only)}`",
    ]


def group_label(directory: Path, file_path: Path) -> str:
    if "per_run" in directory.parts and "__" in file_path.stem:
        return file_path.stem.split("__", 1)[0]
    return file_path.stem


def write_directory_readme(directory: Path) -> None:
    files = [path for path in directory.iterdir() if path.is_file() and path.name != "README.md" and path.suffix.lower() in ARTIFACT_SUFFIXES]
    pngs = sorted(path for path in files if path.suffix.lower() == ".png")
    csvs = sorted(path for path in files if path.suffix.lower() == ".csv")
    json_candidates = sorted(path for path in files if path.suffix.lower() == ".json")
    companion_stems = {path.stem for path in pngs + csvs}
    json_only = [path for path in json_candidates if path.stem not in companion_stems]
    if not pngs and not csvs and not json_only:
        return

    lines: list[str] = []
    lines.append(f"# {titleize(directory.name)}")
    lines.append("")
    lines.append("This README explains the reporting artifacts stored directly in this folder.")
    lines.append("")
    lines.extend(inventory_line(directory, pngs, csvs, json_only))
    lines.append("")

    if pngs:
        lines.append("## Figures and Renders")
        lines.append("")
        png_groups: dict[str, list[Path]] = {}
        for path in pngs:
            png_groups.setdefault(group_label(directory, path), []).append(path)
        for group, paths in png_groups.items():
            if len(png_groups) > 1:
                lines.append(f"### {group}")
                lines.append("")
            for path in paths:
                payload = read_json(companion_json(path)) if companion_json(path).exists() else {}
                values_text, show_text, infer_text = explain_figure(path.stem, payload)
                lines.append(f"#### `{path.name}`")
                lines.append("")
                lines.append(f"- File: [{path.name}]({path.name})")
                lines.append(f"- Values: {values_text}")
                lines.append(f"- What the graph shows: {show_text}")
                lines.append(f"- What can be inferred from the shape: {infer_text}")
                lines.append("")

    if csvs:
        lines.append("## Tables and Numeric Reports")
        lines.append("")
        csv_groups: dict[str, list[Path]] = {}
        for path in csvs:
            csv_groups.setdefault(group_label(directory, path), []).append(path)
        for group, paths in csv_groups.items():
            if len(csv_groups) > 1:
                lines.append(f"### {group}")
                lines.append("")
            for path in paths:
                payload = read_json(companion_json(path)) if companion_json(path).exists() else {}
                desc_1, desc_2 = explain_table(path.stem, payload)
                lines.append(f"#### `{path.name}`")
                lines.append("")
                lines.append(f"- File: [{path.name}]({path.name})")
                lines.append(f"- Explanation: {desc_1}")
                lines.append(f"- How to read it: {desc_2}")
                lines.append("")

    if json_only:
        lines.append("## JSON Summaries")
        lines.append("")
        json_groups: dict[str, list[Path]] = {}
        for path in json_only:
            json_groups.setdefault(group_label(directory, path), []).append(path)
        for group, paths in json_groups.items():
            if len(json_groups) > 1:
                lines.append(f"### {group}")
                lines.append("")
            for path in paths:
                payload = read_json(path)
                desc_1, desc_2 = explain_json_only(path.stem, payload)
                lines.append(f"#### `{path.name}`")
                lines.append("")
                lines.append(f"- File: [{path.name}]({path.name})")
                lines.append(f"- Explanation: {desc_1}")
                lines.append(f"- How to use it: {desc_2}")
                lines.append("")

    (directory / "README.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

def write_root_readme() -> None:
    lines = [
        "# Thesis Reporting Pack",
        "",
        "This directory is the immutable reporting layer built on top of the frozen final_113 and final_42_ablation bundle sets.",
        "",
        "- Main report: [FINAL_EXPERIMENTS_REPORTING.md](FINAL_EXPERIMENTS_REPORTING.md)",
        "- Top-level catalogs: [catalogs](catalogs)",
        "- 113-run reporting pack: [final_113](final_113)",
        "- 42-run ablation reporting pack: [final_42_ablation](final_42_ablation)",
        "- Representative renders: [representative_sets](representative_sets)",
        "- QA outputs: [qa](qa)",
        "",
        "Each subdirectory that contains figures, tables, renders, or reporting summaries also contains a README.md that explains what the artifacts mean.",
        "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_final_experiments_report() -> None:
    build_summary = read_json(ROOT / "qa" / "build_summary.json")
    final113_summary = read_json(FINAL_SUCCESSFUL_RUNS_PATH / "final_113" / "reporting" / "final_reporting_summary.json")
    p1 = pd.read_csv(ROOT / "final_42_ablation" / "tables" / "grouped" / "final_42_ablation__point1_grouped_metrics.csv")
    p1_stats = pd.read_csv(ROOT / "final_42_ablation" / "tables" / "grouped" / "final_42_ablation__point1_paired_stats.csv")
    p2 = pd.read_csv(ROOT / "final_42_ablation" / "tables" / "grouped" / "final_42_ablation__point2_grouped_metrics.csv")
    p3 = pd.read_csv(ROOT / "final_42_ablation" / "tables" / "grouped" / "final_42_ablation__point3_grouped_metrics.csv")

    p1_fixed = p1[p1["weather_label"] == "fixed_weather"].sort_values("ent_coef")
    p1_random = p1[p1["weather_label"] == "random_weather"].sort_values("ent_coef")
    p1_random_stat = p1_stats[(p1_stats["metric"] == "deterministic_return") & (p1_stats["weather_label"] == "random_weather")].iloc[0]
    p3_fixed = p3[p3["weather_label"] == "fixed_weather"].sort_values("nutrient_cost_weight")
    p3_random = p3[p3["weather_label"] == "random_weather"].sort_values("nutrient_cost_weight")
    p3_fixed_best = p3_fixed.loc[p3_fixed["primary_metric_value__mean"].idxmax()]
    p3_random_best = p3_random.loc[p3_random["primary_metric_value__mean"].idxmax()]
    p2_a2c_fixed_best = p2[(p2["method"] == "A2C") & (p2["weather_label"] == "fixed_weather")].sort_values("deterministic_return", ascending=False).iloc[0]
    p2_a2c_random_best = p2[(p2["method"] == "A2C") & (p2["weather_label"] == "random_weather")].sort_values("deterministic_return", ascending=False).iloc[0]
    p2_ppo_fixed_best = p2[(p2["method"] == "PPO") & (p2["weather_label"] == "fixed_weather")].sort_values("deterministic_return", ascending=False).iloc[0]
    p2_ppo_random_best = p2[(p2["method"] == "PPO") & (p2["weather_label"] == "random_weather")].sort_values("deterministic_return", ascending=False).iloc[0]

    lines = [
        "# Final Experiments Reporting",
        "",
        "## Scope",
        "",
        "This report summarizes the two canonical experiment collections used for the thesis reporting pack.",
        "",
        f"- final_113: `{build_summary['datasets'][0]['expected_runs']}` runs with `{build_summary['datasets'][0]['matched_histories']}` matched recovered histories.",
        f"- final_42_ablation: `{build_summary['datasets'][1]['expected_runs']}` runs with `{build_summary['datasets'][1]['matched_histories']}` matched recovered histories.",
        "",
        "## 113-Run Study",
        "",
        "### Main Conclusions",
        "",
        f"- Fertilization core best grouped setting: **{final113_summary['best_groups']['fertilization_core']['group_key']}** with mean deterministic return `{final113_summary['best_groups']['fertilization_core']['mean']:.2f}` and 95% CI `[{final113_summary['best_groups']['fertilization_core']['ci_low']:.2f}, {final113_summary['best_groups']['fertilization_core']['ci_high']:.2f}]`.",
        f"- Crop-planning non-hierarchical best grouped setting: **{final113_summary['best_groups']['crop_planning_nonhier']['group_key']}** with mean evaluation reward `{final113_summary['best_groups']['crop_planning_nonhier']['mean']:.3f}`.",
        f"- Guarded hierarchical rerun best grouped setting: **{final113_summary['best_groups']['crop_planning_hierarchical_guarded_rerun']['group_key']}** with mean deterministic return `{final113_summary['best_groups']['crop_planning_hierarchical_guarded_rerun']['mean']:.2f}`.",
        f"- Best single fertilization run: **{final113_summary['best_single_runs']['fertilization_core']['label']}** with deterministic return `{final113_summary['best_single_runs']['fertilization_core']['value']:.2f}`.",
        f"- Best single non-hierarchical crop-planning run: **{final113_summary['best_single_runs']['crop_planning_nonhier']['label']}** with deterministic evaluation reward `{final113_summary['best_single_runs']['crop_planning_nonhier']['value']:.3f}`.",
        f"- Best single guarded hierarchical run: **{final113_summary['best_single_runs']['crop_planning_hierarchical_guarded_rerun']['label']}** with deterministic return `{final113_summary['best_single_runs']['crop_planning_hierarchical_guarded_rerun']['value']:.2f}`.",
        "",
        "### Interpretation",
        "",
        "- The fertilization matrix favored long-budget fixed-weather A2C at the grouped level, which points to strong stability under the simpler weather regime and the longest horizon.",
        "- The non-hierarchical crop-planning results favored fixed-weather PPO nonadaptive at the grouped level, which suggests that reduced environmental stochasticity improved consistency across seeds.",
        "- Guarded hierarchical reruns should be interpreted separately from the non-hierarchical crop-planning leaderboard because the guardrails change the decision process itself.",
        "- DQN reruns remain descriptive only and are useful primarily as baseline reference points, not as equally supported statistical winners.",
        "",
        "### Supporting Evidence",
        "",
        "- [final_113 leaderboard figure](final_113/figures/grouped/final_113__leaderboard_primary_metric.png)",
        "- [final_113 grouped comparison figure](final_113/figures/grouped/final_113__grouped_comparison.png)",
        "- [final_113 runtime comparison figure](final_113/figures/grouped/final_113__runtime_comparison.png)",
        "- [final_113 uplift vs baseline figure](final_113/figures/grouped/final_113__uplift_vs_baseline.png)",
        "- [final_113 grouped metrics table](final_113/tables/grouped/final_113__grouped_metrics.csv)",
        "- [final_113 run-level metrics table](final_113/tables/grouped/final_113__run_level_metrics.csv)",
        "- [final_113 statistical tests table](final_113/tables/grouped/final_113__statistical_tests.csv)",
        "",
        "## 42-Run Ablation Study",
        "",
        "### Point 1: Entropy Coefficient in Fertilization",
        "",
        f"- Under fixed weather, ent_coef `0.0` beat `0.01` on mean deterministic return: `{p1_fixed.iloc[0]['primary_metric_value__mean']:.2f}` vs `{p1_fixed.iloc[1]['primary_metric_value__mean']:.2f}`.",
        f"- Under random weather, ent_coef `0.01` beat `0.0` on mean deterministic return: `{p1_random.iloc[1]['primary_metric_value__mean']:.2f}` vs `{p1_random.iloc[0]['primary_metric_value__mean']:.2f}`.",
        f"- The paired random-weather deterministic-return delta for `0.01 - 0.0` was `{p1_random_stat['mean_delta']:.2f}` with `p={p1_random_stat['p_value']:.4f}` across `n={int(p1_random_stat['n'])}` matched seeds.",
        "- Conclusion: extra entropy helped in random weather but hurt fixed-weather performance and increased fixed-weather runtime, so the value of entropy depended on environmental stochasticity.",
        "",
        "Evidence:",
        "",
        "- [point1 primary metric figure](final_42_ablation/figures/grouped/final_42_ablation__point1_entropy_primary_metric.png)",
        "- [point1 paired delta figure](final_42_ablation/figures/grouped/final_42_ablation__point1_entropy_paired_deltas.png)",
        "- [point1 grouped metrics table](final_42_ablation/tables/grouped/final_42_ablation__point1_grouped_metrics.csv)",
        "- [point1 paired stats table](final_42_ablation/tables/grouped/final_42_ablation__point1_paired_stats.csv)",
        "",
        "### Point 2: Hierarchical Shaping With Blocked Nutrient Penalty",
        "",
        f"- A2C fixed-weather improved from `{p2[(p2['method']=='A2C') & (p2['weather_label']=='fixed_weather') & (p2['blocked_penalty']==0.0)].iloc[0]['deterministic_return']:.2f}` at penalty `0.0` to `{p2_a2c_fixed_best['deterministic_return']:.2f}` at penalty `{p2_a2c_fixed_best['blocked_penalty']:.2f}`.",
        f"- A2C random-weather improved from `{p2[(p2['method']=='A2C') & (p2['weather_label']=='random_weather') & (p2['blocked_penalty']==0.0)].iloc[0]['deterministic_return']:.2f}` at penalty `0.0` to `{p2_a2c_random_best['deterministic_return']:.2f}` at penalty `{p2_a2c_random_best['blocked_penalty']:.2f}`.",
        f"- PPO fixed-weather was best at penalty `{p2_ppo_fixed_best['blocked_penalty']:.2f}` with deterministic return `{p2_ppo_fixed_best['deterministic_return']:.2f}`.",
        f"- PPO random-weather was best at penalty `{p2_ppo_random_best['blocked_penalty']:.2f}` with deterministic return `{p2_ppo_random_best['deterministic_return']:.2f}`.",
        "- Compliance stayed at 1.0 for all 12 point2 runs and total cost stayed nearly constant within method families, so the shaping penalty mainly altered reward optimization rather than explicit guardrail compliance.",
        "- Conclusion: blocked-nutrient shaping helped A2C more than PPO. For PPO, stronger penalties usually reduced return while leaving compliance unchanged.",
        "",
        "Evidence:",
        "",
        "- [point2 primary comparison figure](final_42_ablation/figures/grouped/final_42_ablation__point2_primary_comparison.png)",
        "- [point2 compliance figure](final_42_ablation/figures/grouped/final_42_ablation__point2_thesis_compliance.png)",
        "- [point2 grouped metrics table](final_42_ablation/tables/grouped/final_42_ablation__point2_grouped_metrics.csv)",
        "- [example point2 weekly NPK trace](final_42_ablation/figures/per_run/013_p2_a2c_fixed_weather_seed0_blockpen0__weekly_npk_behavior.png)",
        "- [example point2 crop timeline](final_42_ablation/figures/per_run/013_p2_a2c_fixed_weather_seed0_blockpen0__crop_decision_timeline.png)",
        "",
        "### Point 3: Nutrient Cost Weight in Fertilization",
        "",
        f"- Under fixed weather, the best mean deterministic return occurred at cost_weight `{p3_fixed_best['nutrient_cost_weight']:.1f}` with `{p3_fixed_best['primary_metric_value__mean']:.2f}`.",
        f"- Under random weather, the best mean deterministic return occurred at cost_weight `{p3_random_best['nutrient_cost_weight']:.1f}` with `{p3_random_best['primary_metric_value__mean']:.2f}`.",
        f"- The low-cost setting `0.8` was clearly weaker than `1.0` in fixed weather: `{p3_fixed.iloc[0]['primary_metric_value__mean']:.2f}` vs `{p3_fixed.iloc[1]['primary_metric_value__mean']:.2f}`.",
        "- Conclusion: cost_weight `1.0` remains the safest default. `1.2` is effectively tied with it and slightly best in random weather, while `0.8` consistently underperforms.",
        "",
        "Evidence:",
        "",
        "- [point3 primary metric figure](final_42_ablation/figures/grouped/final_42_ablation__point3_cost_weight_primary_metric.png)",
        "- [point3 paired delta figure](final_42_ablation/figures/grouped/final_42_ablation__point3_cost_weight_paired_deltas.png)",
        "- [point3 grouped metrics table](final_42_ablation/tables/grouped/final_42_ablation__point3_grouped_metrics.csv)",
        "- [point3 paired stats table](final_42_ablation/tables/grouped/final_42_ablation__point3_paired_stats.csv)",
        "",
        "## Cross-Study Conclusions",
        "",
        "- The 113-run matrix identifies which broad method and environment combinations are consistently strong enough to serve as thesis-level reference settings.",
        "- The 42-run ablation pack refines those conclusions by showing which local design changes actually help performance and which mostly change optimization behavior without improving outcomes.",
        "- Across the fertilization experiments, random-weather settings benefited more from added exploration pressure than fixed-weather settings did.",
        "- Across the cost-weight ablation, underpenalizing nutrient cost (`0.8`) was not competitive with the default cost balance.",
        "- In the hierarchical shaping study, compliance was already saturated, so reward shaping mainly changed return and optimization dynamics rather than explicit rule-following rates.",
        "",
        "## Evidence Quality and Limitations",
        "",
        "- The reporting pack verification found `0` CSV files missing JSON companions, `0` PNG files missing JSON companions, and `0` runs missing run-level metrics JSON. See [build_verification.json](qa/build_verification.json).",
        "- The 12 point2 runs without vec_normalize were all validated as usable reporting targets. See [smoke_tests.json](qa/smoke_tests.json).",
        "- DQN comparisons remain descriptive because they do not have the same repeated-group evidence structure as the main PPO/A2C runs.",
        "- Remaining skipped artifacts in final_113 are source-driven: some runs did not log checkpoint evaluations, rollout reward, or episode length. The ablation pack completed without skips.",
        "",
    ]
    FINAL_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not ROOT.exists():
        raise FileNotFoundError(f"reporting root missing: {ROOT}")
    for directory in sorted(path for path in ROOT.rglob("*") if path.is_dir()):
        if directory == ROOT:
            continue
        write_directory_readme(directory)
    write_root_readme()
    write_final_experiments_report()


if __name__ == "__main__":
    main()
