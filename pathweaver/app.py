"""PathWeaver — Streamlit UI for multi-agent path planning."""
from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from pathweaver.mapf import position_at
from pathweaver.metrics import format_comparison_table, run_comparison
from pathweaver.scenarios import ALL_SCENARIOS, get_scenario

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCENARIO_NAMES = [s.name for s in ALL_SCENARIOS]
ALGO_LABELS = ["Independent", "Prioritized", "Cooperative A*", "CBS"]

# Distinct colours for up to 8 agents (RGB 0-1)
AGENT_PALETTE = [
    (0.17, 0.48, 0.71),  # blue
    (0.90, 0.49, 0.24),  # orange
    (0.33, 0.70, 0.47),  # green
    (0.71, 0.31, 0.51),  # pink
    (0.48, 0.60, 0.36),  # olive
    (0.80, 0.37, 0.38),  # red
    (0.31, 0.44, 0.69),  # indigo
    (0.79, 0.64, 0.22),  # gold
]

# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------

DEFAULTS: dict = {
    "result": None,          # AlgorithmResult for the chosen algo
    "all_results": None,     # List[AlgorithmResult] from run_comparison
    "scenario": None,        # Scenario object
    "algo_label": "CBS",
    "frame": 0,
    "makespan": 0,
}


def _init_state() -> None:
    for key, val in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _reset() -> None:
    for key, val in DEFAULTS.items():
        st.session_state[key] = val


# ---------------------------------------------------------------------------
# Grid drawing
# ---------------------------------------------------------------------------

def _build_frame(scenario, result, frame: int) -> plt.Figure:
    """Return a matplotlib Figure showing agent positions at *frame*."""
    grid = scenario.grid
    paths = result.paths
    n_agents = len(paths)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(-0.5, grid.width - 0.5)
    ax.set_ylim(-0.5, grid.height - 0.5)
    ax.set_aspect("equal")
    ax.invert_yaxis()  # (0,0) top-left, matching grid convention
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#f5f5f5")

    # Grid lines
    for x in range(grid.width + 1):
        ax.axvline(x - 0.5, color="#dddddd", linewidth=0.5, zorder=0)
    for y in range(grid.height + 1):
        ax.axhline(y - 0.5, color="#dddddd", linewidth=0.5, zorder=0)

    # Obstacles
    for (ox, oy) in grid.obstacles:
        ax.add_patch(
            mpatches.Rectangle(
                (ox - 0.5, oy - 0.5), 1, 1,
                color="#2a2a2a", zorder=1,
            )
        )

    # Per-agent: path trail, start, goal, current position
    for i, path in enumerate(paths):
        color = AGENT_PALETTE[i % len(AGENT_PALETTE)]

        # Start marker (hollow square)
        sx, sy = scenario.agents[i][0]
        ax.add_patch(
            mpatches.Rectangle(
                (sx - 0.45, sy - 0.45), 0.9, 0.9,
                fill=False, edgecolor=color, linewidth=2, zorder=2,
            )
        )

        # Goal marker (X)
        gx, gy = scenario.agents[i][1]
        ax.plot(
            [gx - 0.3, gx + 0.3], [gy - 0.3, gy + 0.3],
            color=color, linewidth=2, zorder=2,
        )
        ax.plot(
            [gx - 0.3, gx + 0.3], [gy + 0.3, gy - 0.3],
            color=color, linewidth=2, zorder=2,
        )

        if not path:
            continue

        # Path trail up to current frame (faded line)
        trail_t = min(frame, len(path) - 1)
        xs = [p[0] for p in path[: trail_t + 1]]
        ys = [p[1] for p in path[: trail_t + 1]]
        ax.plot(xs, ys, color=color, alpha=0.25, linewidth=2, zorder=3)

        # Current agent position (solid circle)
        cx, cy = position_at(path, frame)
        ax.add_patch(
            mpatches.Circle(
                (cx, cy), 0.35,
                color=color, zorder=4,
            )
        )

    # Conflict highlight: any two agents at the same cell at this frame
    occupied: dict = {}
    for i, path in enumerate(paths):
        if not path:
            continue
        pos = position_at(path, frame)
        if pos in occupied:
            cx, cy = pos
            ax.add_patch(
                mpatches.Circle(
                    (cx, cy), 0.45,
                    fill=False, edgecolor="#cc0000", linewidth=3, zorder=5,
                )
            )
        else:
            occupied[pos] = i

    # Legend
    handles = [
        mpatches.Patch(color=AGENT_PALETTE[i % len(AGENT_PALETTE)], label=f"Agent {i}")
        for i in range(n_agents)
    ]
    ax.legend(handles=handles, loc="upper right", fontsize=8, framealpha=0.8)

    ax.set_title(
        f"{scenario.name.capitalize()} — {result.algorithm}   t = {frame}",
        fontsize=11,
        pad=6,
    )
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="PathWeaver", layout="wide")
    _init_state()

    st.title("PathWeaver — Multi-Agent Path Planning")

    # -----------------------------------------------------------------------
    # Sidebar
    # -----------------------------------------------------------------------
    with st.sidebar:
        st.header("Settings")

        chosen_scenario = st.selectbox(
            "Scenario",
            SCENARIO_NAMES,
            index=0,
            key="_scenario_select",
        )

        chosen_algo = st.radio(
            "Algorithm",
            ALGO_LABELS,
            index=ALGO_LABELS.index(st.session_state.algo_label)
            if st.session_state.algo_label in ALGO_LABELS
            else 3,
            key="_algo_radio",
        )

        run_clicked = st.button("Run", type="primary", use_container_width=True)
        reset_clicked = st.button("Reset", use_container_width=True)

        if reset_clicked:
            _reset()
            st.rerun()

        st.markdown("---")
        st.caption(
            "**Controls**\n\n"
            "1. Pick a scenario and algorithm\n"
            "2. Click **Run**\n"
            "3. Drag the frame slider to animate\n\n"
            "Red ring = conflict at that timestep."
        )

    # -----------------------------------------------------------------------
    # Run planning
    # -----------------------------------------------------------------------
    if run_clicked:
        scenario = get_scenario(chosen_scenario)
        with st.spinner("Planning paths…"):
            all_results = run_comparison(scenario.grid, scenario.agents)
        # Find the result matching the chosen algorithm
        result = next(r for r in all_results if r.algorithm == chosen_algo)
        st.session_state.scenario = scenario
        st.session_state.all_results = all_results
        st.session_state.result = result
        st.session_state.algo_label = chosen_algo
        st.session_state.makespan = result.makespan
        st.session_state.frame = 0

    # -----------------------------------------------------------------------
    # Main content (only shown after a run)
    # -----------------------------------------------------------------------
    if st.session_state.result is None:
        st.info("Choose a scenario and algorithm in the sidebar, then click **Run**.")
        return

    scenario = st.session_state.scenario
    result = st.session_state.result
    all_results = st.session_state.all_results
    makespan = st.session_state.makespan

    # If the user changes algo without re-running, swap result live
    if chosen_algo != st.session_state.algo_label and all_results:
        result = next(r for r in all_results if r.algorithm == chosen_algo)
        st.session_state.result = result
        st.session_state.algo_label = chosen_algo
        st.session_state.makespan = result.makespan
        st.session_state.frame = 0
        makespan = result.makespan

    col_main, col_metrics = st.columns([3, 2])

    # -----------------------------------------------------------------------
    # Grid animation (left column)
    # -----------------------------------------------------------------------
    with col_main:
        st.subheader("Grid Animation")

        frame = st.slider(
            "Timestep",
            min_value=0,
            max_value=max(makespan, 1),
            value=st.session_state.frame,
            key="_frame_slider",
        )
        st.session_state.frame = frame

        fig = _build_frame(scenario, result, frame)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        st.caption(
            f"**{scenario.name.capitalize()}** — {scenario.description}  \n"
            f"Grid: {scenario.grid.width}×{scenario.grid.height}  |  "
            f"Agents: {len(scenario.agents)}  |  "
            f"Obstacles: {len(scenario.grid.obstacles)}"
        )

    # -----------------------------------------------------------------------
    # Metrics panel (right column)
    # -----------------------------------------------------------------------
    with col_metrics:
        st.subheader("Metrics")

        # Top-level KPIs for the selected algorithm
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("Makespan", result.makespan)
        kpi2.metric("Total Cost", result.total_cost)

        kpi3, kpi4 = st.columns(2)
        kpi3.metric("Conflicts", result.conflicts, delta=None)
        kpi4.metric("Runtime (ms)", f"{result.runtime_ms:.1f}")

        if result.capped:
            st.warning("CBS hit its node expansion cap — solution may not be optimal.")
        if not result.success:
            st.error("One or more agents have no valid path.")
        if result.conflicts == 0 and result.success:
            st.success("No conflicts — all agents reach their goals safely.")

        # Per-agent breakdown
        st.markdown("**Per-Agent Breakdown**")
        per_agent_data = {
            "Agent": [f"Agent {s.agent_id}" for s in result.per_agent],
            "Path Length": [s.path_length for s in result.per_agent],
            "Wait Steps": [s.wait_steps for s in result.per_agent],
        }
        st.dataframe(per_agent_data, use_container_width=True, hide_index=True)

        # -----------------------------------------------------------------------
        # Comparison table (all 4 algorithms)
        # -----------------------------------------------------------------------
        st.markdown("---")
        st.subheader("Algorithm Comparison")

        rows = []
        for r in all_results:
            rows.append(
                {
                    "Algorithm": r.algorithm,
                    "Success": "Yes" if r.success else "No",
                    "Makespan": r.makespan,
                    "Total Cost": r.total_cost,
                    "Conflicts": r.conflicts,
                    "Time (ms)": round(r.runtime_ms, 1),
                    "CBS Capped": "Yes" if r.capped else "-",
                }
            )

        # Highlight the currently selected algorithm
        def _highlight_row(row):
            if row["Algorithm"] == result.algorithm:
                return ["background-color: #e8f4fd"] * len(row)
            return [""] * len(row)

        import pandas as pd

        df = pd.DataFrame(rows)
        st.dataframe(
            df.style.apply(_highlight_row, axis=1),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
