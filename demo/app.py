from __future__ import annotations

from pathlib import Path

import streamlit as st

from inference_engine import (
    get_experiment_artifact_rows,
    get_preset_runtime_info,
    list_fertilization_presets,
    run_fertilization_inference,
)


st.set_page_config(page_title="CYCLES Gym Thesis Demo", layout="wide")

st.title("CYCLES Gym Demo: Cost-Driven Agricultural RL")
st.caption(
    "Thesis demo for: Optimizing Agricultural Resource Allocation through Reinforcement Learning: "
    "A Cost-Driven Approach to Crop Efficiency Enhancement."
)

with st.sidebar:
    st.header("Mode")
    page = st.radio(
        "Select view",
        [
            "Live Inference (Fertilization)",
            "Experiment Results Explorer",
            "Deployment Notes",
        ],
    )
    st.markdown("---")
    st.write("Default demo path is inference-only. Retraining is optional.")


def _weather_override_from_ui(value: str):
    if value == "Model default":
        return None
    if value == "Force fixed weather":
        return True
    return False


if page == "Live Inference (Fertilization)":
    st.subheader("Live Inference: Fertilization Policy")
    st.write(
        "This runs inference directly on saved trained models and VecNormalize stats. "
        "No retraining is required for this demo."
    )

    presets = list_fertilization_presets()
    preset_ids = [p["id"] for p in presets]
    preset_labels = {p["id"]: f"{p['title']} ({p['id']})" for p in presets}

    selected_preset_id = st.selectbox(
        "Select model preset",
        options=preset_ids,
        format_func=lambda x: preset_labels[x],
        index=0,
    )
    selected_preset = next(p for p in presets if p["id"] == selected_preset_id)
    runtime_info = get_preset_runtime_info(selected_preset_id)

    st.info(selected_preset.get("notes", ""))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        episodes = st.number_input("Episodes", min_value=1, max_value=20, value=3, step=1)
    with c2:
        deterministic = st.checkbox("Deterministic actions", value=True)
    with c3:
        weather_mode = st.selectbox(
            "Weather mode",
            ["Model default", "Force fixed weather", "Force random weather"],
        )
    with c4:
        use_custom_years = st.checkbox("Override years", value=False)

    if use_custom_years:
        y1, y2 = st.columns(2)
        with y1:
            start_year = st.number_input("Start year", min_value=2005, max_value=2019, value=runtime_info["start_year_default"])
        with y2:
            end_year = st.number_input("End year", min_value=2005, max_value=2019, value=runtime_info["end_year_default"])
    else:
        start_year = None
        end_year = None

    if st.button("Run Inference", type="primary"):
        with st.spinner("Running simulation..."):
            result = run_fertilization_inference(
                preset_id=selected_preset_id,
                episodes=int(episodes),
                deterministic=bool(deterministic),
                start_year=int(start_year) if start_year is not None else None,
                end_year=int(end_year) if end_year is not None else None,
                fixed_weather_override=_weather_override_from_ui(weather_mode),
            )

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Mean Total Reward", f"{result.mean_total_reward:.2f}")
        with m2:
            st.metric("Mean Total N (kg/ha)", f"{result.mean_total_n_kg:.2f}")
        with m3:
            st.metric("Episodes", f"{len(result.episode_summaries)}")

        st.markdown("**Runtime Config Used**")
        st.json(result.used_config)

        st.markdown("**Per-Episode Summary**")
        st.dataframe(result.episode_summaries, use_container_width=True)

        st.markdown("**First Episode Fertilizer Schedule (kg N/ha per step)**")
        st.line_chart(result.first_episode_actions_kg, use_container_width=True)

        st.markdown("**First Episode Reward Trajectory**")
        st.line_chart(result.first_episode_rewards, use_container_width=True)


elif page == "Experiment Results Explorer":
    st.subheader("Experiment Evidence Explorer")
    st.write("This section replays already-audited experiment results for thesis reporting.")

    fert_rows = get_experiment_artifact_rows("fertilization_grouped_latest_success.csv")
    crop_rows = get_experiment_artifact_rows("crop_grouped_latest_success.csv")
    failure_rows = get_experiment_artifact_rows("failure_signature_counts.csv")
    coverage_rows = get_experiment_artifact_rows("run_all_2_coverage_vs_wandb.csv")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Fertilization Grouped Results**")
        st.dataframe(fert_rows, use_container_width=True)
    with c2:
        st.markdown("**Crop Planning Grouped Results**")
        st.dataframe(crop_rows, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Failure Signatures**")
        st.dataframe(failure_rows, use_container_width=True)
    with c4:
        covered_yes = sum(1 for row in coverage_rows if row.get("covered_successfully", "").lower() == "yes")
        total = len(coverage_rows)
        st.metric("run_all_2 Successful Coverage", f"{covered_yes}/{total}")
        st.markdown("**Coverage Detail (run_all_2)**")
        st.dataframe(coverage_rows[:30], use_container_width=True)

    st.success(
        "Practical recommendation from current evidence: use PPO adaptive random-weather policy for fertilization demo deployment."
    )


else:
    st.subheader("Deployment Notes")
    st.write(
        "For pilot/demo, inference mode is enough. Retraining is only needed if one of the following changes:"
    )
    st.markdown(
        "- New geography or climate regime outside Pakistan training setup\n"
        "- New crop calendar, fertilizer pricing logic, or reward definition\n"
        "- Performance drift observed in pilot usage logs\n"
        "- Full thesis matrix completion required for stronger statistical confidence"
    )
    st.markdown("Detailed instructions are in `demo/INSTRUCTIONS.md`.")
    instructions_path = Path(__file__).resolve().parent / "INSTRUCTIONS.md"
    if instructions_path.exists():
        st.download_button(
            label="Download INSTRUCTIONS.md",
            data=instructions_path.read_text(encoding="utf-8"),
            file_name="INSTRUCTIONS.md",
            mime="text/markdown",
        )
