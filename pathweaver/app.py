from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from pathweaver.grid import Grid
from pathweaver.mapf import position_at
from pathweaver.metrics import run_comparison
from pathweaver.scenarios import ALL_SCENARIOS, Scenario, get_scenario

SCENARIO_NAMES = [s.name for s in ALL_SCENARIOS]
ALGO_LABELS = ["Independent", "Prioritized", "Cooperative A*", "CBS"]

AGENT_PALETTE = [
    (0.17, 0.48, 0.71),
    (0.90, 0.49, 0.24),
    (0.33, 0.70, 0.47),
    (0.71, 0.31, 0.51),
    (0.48, 0.60, 0.36),
    (0.80, 0.37, 0.38),
    (0.31, 0.44, 0.69),
    (0.79, 0.64, 0.22),
]

_DEFAULTS = {
    "result": None,
    "all_results": None,
    "scenario": None,
    "algo_label": "CBS",
    "frame": 0,
    "makespan": 0,
    "editor_grid_w": 10,
    "editor_grid_h": 10,
    "using_custom": False,
}


def _init_state():
    for k, v in _DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "custom_obstacles" not in st.session_state:
        st.session_state.custom_obstacles = set()
    if "custom_agents" not in st.session_state:
        st.session_state.custom_agents = []


def _reset():
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.custom_obstacles = set()
    st.session_state.custom_agents = []


def _draw_grid_base(ax, grid):
    ax.set_xlim(-0.5, grid.width - 0.5)
    ax.set_ylim(-0.5, grid.height - 0.5)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#f5f5f5")
    for x in range(grid.width + 1):
        ax.axvline(x - 0.5, color="#dddddd", linewidth=0.5, zorder=0)
    for y in range(grid.height + 1):
        ax.axhline(y - 0.5, color="#dddddd", linewidth=0.5, zorder=0)
    for ox, oy in grid.obstacles:
        ax.add_patch(mpatches.Rectangle((ox - 0.5, oy - 0.5), 1, 1, color="#2a2a2a", zorder=1))


def _build_frame(scenario, result, frame, figsize=(6, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    _draw_grid_base(ax, scenario.grid)

    for i, path in enumerate(result.paths):
        color = AGENT_PALETTE[i % len(AGENT_PALETTE)]
        sx, sy = scenario.agents[i][0]
        ax.add_patch(mpatches.Rectangle(
            (sx - 0.45, sy - 0.45), 0.9, 0.9,
            fill=False, edgecolor=color, linewidth=2, zorder=2,
        ))
        gx, gy = scenario.agents[i][1]
        ax.plot([gx - 0.3, gx + 0.3], [gy - 0.3, gy + 0.3], color=color, linewidth=2, zorder=2)
        ax.plot([gx - 0.3, gx + 0.3], [gy + 0.3, gy - 0.3], color=color, linewidth=2, zorder=2)
        if not path:
            continue
        trail = min(frame, len(path) - 1)
        ax.plot([p[0] for p in path[:trail + 1]], [p[1] for p in path[:trail + 1]],
                color=color, alpha=0.25, linewidth=2, zorder=3)
        cx, cy = position_at(path, frame)
        ax.add_patch(mpatches.Circle((cx, cy), 0.35, color=color, zorder=4))

    occupied = {}
    for i, path in enumerate(result.paths):
        if not path:
            continue
        pos = position_at(path, frame)
        if pos in occupied:
            cx, cy = pos
            ax.add_patch(mpatches.Circle((cx, cy), 0.45,
                fill=False, edgecolor="#cc0000", linewidth=3, zorder=5))
        else:
            occupied[pos] = i

    handles = [mpatches.Patch(color=AGENT_PALETTE[i % len(AGENT_PALETTE)], label=f"A{i}")
               for i in range(len(result.paths))]
    ax.legend(handles=handles, loc="upper right", fontsize=7, framealpha=0.8)
    ax.set_title(f"{result.algorithm}   t = {frame}", fontsize=10, pad=4)
    fig.tight_layout()
    return fig


def _build_editor_figure(grid_w, grid_h, obstacles, agents):
    fig, ax = plt.subplots(figsize=(5, 5))
    _draw_grid_base(ax, Grid(grid_w, grid_h, set(obstacles)))
    for i, (start, goal) in enumerate(agents):
        color = AGENT_PALETTE[i % len(AGENT_PALETTE)]
        sx, sy = start
        ax.add_patch(mpatches.Rectangle(
            (sx - 0.45, sy - 0.45), 0.9, 0.9,
            facecolor=color, edgecolor="white", linewidth=2, zorder=3,
        ))
        ax.text(sx, sy, f"S{i}", ha="center", va="center",
                fontsize=7, color="white", fontweight="bold", zorder=4)
        gx, gy = goal
        ax.plot([gx - 0.3, gx + 0.3], [gy - 0.3, gy + 0.3], color=color, linewidth=2.5, zorder=3)
        ax.plot([gx - 0.3, gx + 0.3], [gy + 0.3, gy - 0.3], color=color, linewidth=2.5, zorder=3)
        ax.text(gx, gy - 0.48, f"G{i}", ha="center", va="top", fontsize=6, color=color, zorder=4)
    ax.set_title(
        f"Custom Grid  ({grid_w}×{grid_h})   {len(obstacles)} obstacle(s)   {len(agents)} agent(s)",
        fontsize=9, pad=4,
    )
    fig.tight_layout()
    return fig


def _build_comparison_chart(all_results):
    labels = [r.algorithm for r in all_results]
    x = np.arange(len(labels))
    w = 0.25

    fig, ax = plt.subplots(figsize=(8, 3.8))
    b1 = ax.bar(x - w, [r.makespan   for r in all_results], w, label="Makespan",   color="#4c8eda", zorder=2)
    b2 = ax.bar(x,     [r.total_cost for r in all_results], w, label="Total Cost", color="#f28b44", zorder=2)
    b3 = ax.bar(x + w, [r.conflicts  for r in all_results], w, label="Conflicts",  color="#e05c5c", zorder=2)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Value", fontsize=9)
    ax.set_title("Algorithm Comparison — Makespan / Total Cost / Conflicts", fontsize=11)
    ax.legend(fontsize=9, loc="upper right")
    ax.set_facecolor("#fafafa")
    ax.yaxis.grid(True, color="#e0e0e0", zorder=0)
    ax.set_axisbelow(True)
    fig.patch.set_facecolor("#fafafa")

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.annotate(str(int(h)),
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 3), textcoords="offset points",
                ha="center", va="bottom", fontsize=8)

    fig.tight_layout()
    return fig


def main():
    st.set_page_config(page_title="PathWeaver", layout="wide")
    _init_state()

    st.title("PathWeaver — Multi-Agent Path Planning")

    s1, s2, s3 = st.columns(3)
    with s1:
        st.info("**Step 1** — Pick a preset scenario *or* build your own in the Grid Editor below")
    with s2:
        st.info("**Step 2** — Choose an algorithm & view mode, then click **Run** in the sidebar")
    with s3:
        st.info("**Step 3** — Drag the **Timestep** slider to animate and compare all 4 algorithms")

    st.markdown("---")

    with st.sidebar:
        st.header("Settings")

        chosen_scenario = st.selectbox("Scenario", SCENARIO_NAMES, index=0, key="_scenario_select")
        chosen_algo = st.radio(
            "Algorithm (single view)",
            ALGO_LABELS,
            index=ALGO_LABELS.index(st.session_state.algo_label)
            if st.session_state.algo_label in ALGO_LABELS else 3,
            key="_algo_radio",
        )
        view_mode = st.radio("View Mode", ["Single Algorithm", "Compare All (2x2)"],
                             index=0, key="_view_mode_radio")

        run_clicked = st.button("Run", type="primary", width="stretch")
        reset_clicked = st.button("Reset", width="stretch")

        if reset_clicked:
            _reset()
            st.rerun()

        st.markdown("---")
        st.caption(
            "**Legend**\n\n"
            "Hollow square = start\n\n"
            "× = goal\n\n"
            "Filled circle = agent position\n\n"
            "Red ring = conflict\n\n"
            "Dark cell = obstacle"
        )

    with st.expander("Grid Editor — Build Your Own Scenario",
                     expanded=(st.session_state.result is None)):
        st.caption(
            "Place obstacles and agents, tick **Use custom grid**, then click **Run**. "
            "The preview updates as you edit."
        )

        use_custom = st.checkbox("Use custom grid for next Run",
                                 value=st.session_state.using_custom, key="_use_custom_cb")
        st.session_state.using_custom = use_custom

        ctrl_col, preview_col = st.columns([1, 2], gap="medium")

        with ctrl_col:
            st.markdown("**Grid Size**")
            c1, c2 = st.columns(2)
            gw = c1.number_input("Width",  5, 30, st.session_state.editor_grid_w, key="_ed_gw")
            gh = c2.number_input("Height", 5, 30, st.session_state.editor_grid_h, key="_ed_gh")
            st.session_state.editor_grid_w = int(gw)
            st.session_state.editor_grid_h = int(gh)

            st.markdown("**Obstacles**")
            o1, o2 = st.columns(2)
            obs_x = o1.number_input("X", 0, int(gw) - 1, 0, key="_obs_x")
            obs_y = o2.number_input("Y", 0, int(gh) - 1, 0, key="_obs_y")

            tog_col, clr_col = st.columns(2)
            if tog_col.button("Add Obstacle", width="stretch", key="_toggle_obs"):
                obs = set(st.session_state.custom_obstacles)
                obs.add((int(obs_x), int(obs_y)))
                st.session_state.custom_obstacles = obs
                st.rerun()
            if clr_col.button("Clear Obstacles", width="stretch", key="_clear_obs"):
                st.session_state.custom_obstacles = set()
                st.rerun()
            if st.button("Remove Cell at (X, Y)", width="stretch", key="_rm_obs"):
                obs = set(st.session_state.custom_obstacles)
                obs.discard((int(obs_x), int(obs_y)))
                st.session_state.custom_obstacles = obs
                st.rerun()

            st.markdown("**Agents** (start → goal)")
            a1c, a2c = st.columns(2)
            a_sx = a1c.number_input("Start X", 0, int(gw) - 1, 0,            key="_a_sx")
            a_sy = a2c.number_input("Start Y", 0, int(gh) - 1, 0,            key="_a_sy")
            a_gx = a1c.number_input("Goal X",  0, int(gw) - 1, int(gw) - 1, key="_a_gx")
            a_gy = a2c.number_input("Goal Y",  0, int(gh) - 1, int(gh) - 1, key="_a_gy")

            add_col, clra_col = st.columns(2)
            if add_col.button("Add Agent", width="stretch", key="_add_agent"):
                agents_list = list(st.session_state.custom_agents)
                agents_list.append(((int(a_sx), int(a_sy)), (int(a_gx), int(a_gy))))
                st.session_state.custom_agents = agents_list
                st.rerun()
            if clra_col.button("Clear Agents", width="stretch", key="_clear_agents"):
                st.session_state.custom_agents = []
                st.rerun()

            st.caption(f"{len(st.session_state.custom_agents)} agent(s) | "
                       f"{len(st.session_state.custom_obstacles)} obstacle(s)")

        with preview_col:
            fig_ed = _build_editor_figure(int(gw), int(gh),
                                          st.session_state.custom_obstacles,
                                          st.session_state.custom_agents)
            st.pyplot(fig_ed, use_container_width=True)
            plt.close(fig_ed)
            st.caption("S0/S1… = start  |  G0/G1… = goal  |  dark cell = obstacle")

    if run_clicked:
        if st.session_state.using_custom:
            if not st.session_state.custom_agents:
                st.error("Add at least one agent in the Grid Editor before running.")
                st.stop()
            grid = Grid(st.session_state.editor_grid_w, st.session_state.editor_grid_h,
                        set(st.session_state.custom_obstacles))
            scenario = Scenario(name="custom", grid=grid,
                                agents=list(st.session_state.custom_agents),
                                description="Custom user-defined scenario")
        else:
            scenario = get_scenario(chosen_scenario)

        with st.spinner("Planning paths for all 4 algorithms…"):
            all_results = run_comparison(scenario.grid, scenario.agents)

        result = next(r for r in all_results if r.algorithm == chosen_algo)
        st.session_state.scenario    = scenario
        st.session_state.all_results = all_results
        st.session_state.result      = result
        st.session_state.algo_label  = chosen_algo
        st.session_state.makespan    = result.makespan
        st.session_state.frame       = 0

    if st.session_state.result is None:
        st.info("No results yet. Pick a scenario (or build one above) and click **Run**.")
        return

    scenario    = st.session_state.scenario
    result      = st.session_state.result
    all_results = st.session_state.all_results
    makespan    = st.session_state.makespan

    if chosen_algo != st.session_state.algo_label and all_results:
        result = next(r for r in all_results if r.algorithm == chosen_algo)
        st.session_state.result      = result
        st.session_state.algo_label  = chosen_algo
        st.session_state.makespan    = result.makespan
        st.session_state.frame       = 0
        makespan = result.makespan

    max_t = max((r.makespan for r in all_results), default=1)
    frame = st.slider("Timestep", 0, max(max_t, 1), st.session_state.frame, key="_frame_slider")
    st.session_state.frame = frame

    if view_mode == "Compare All (2x2)":
        st.subheader(f"Compare All — t = {frame}")

        top_l, top_r = st.columns(2, gap="small")
        bot_l, bot_r = st.columns(2, gap="small")

        for cell, res in zip([top_l, top_r, bot_l, bot_r], all_results):
            with cell:
                fig = _build_frame(scenario, res, frame, figsize=(4, 4))
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
                k1, k2, k3 = st.columns(3)
                k1.metric("Makespan",  res.makespan)
                k2.metric("Cost",      res.total_cost)
                k3.metric("Conflicts", res.conflicts)
                if res.capped:
                    st.warning("CBS capped", icon="⚠")
                if not res.success:
                    st.error("No valid path", icon="✗")

        st.caption(
            f"**{scenario.name.capitalize()}** — {scenario.description}  |  "
            f"Grid: {scenario.grid.width}×{scenario.grid.height}  |  "
            f"Agents: {len(scenario.agents)}  |  "
            f"Obstacles: {len(scenario.grid.obstacles)}"
        )

    else:
        col_main, col_metrics = st.columns([3, 2])

        with col_main:
            st.subheader("Grid Animation")
            fig = _build_frame(scenario, result, frame)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            st.caption(
                f"**{scenario.name.capitalize()}** — {scenario.description}  \n"
                f"Grid: {scenario.grid.width}×{scenario.grid.height}  |  "
                f"Agents: {len(scenario.agents)}  |  "
                f"Obstacles: {len(scenario.grid.obstacles)}"
            )

        with col_metrics:
            st.subheader("Metrics")
            kpi1, kpi2 = st.columns(2)
            kpi1.metric("Makespan",     result.makespan)
            kpi2.metric("Total Cost",   result.total_cost)
            kpi3, kpi4 = st.columns(2)
            kpi3.metric("Conflicts",    result.conflicts)
            kpi4.metric("Runtime (ms)", f"{result.runtime_ms:.1f}")

            if result.capped:
                st.warning("CBS hit its node expansion cap — solution may not be optimal.")
            if not result.success:
                st.error("One or more agents have no valid path.")
            if result.conflicts == 0 and result.success:
                st.success("No conflicts — all agents reached their goals.")

            st.markdown("**Per-Agent Breakdown**")
            st.dataframe({
                "Agent":       [f"Agent {s.agent_id}" for s in result.per_agent],
                "Path Length": [s.path_length         for s in result.per_agent],
                "Wait Steps":  [s.wait_steps          for s in result.per_agent],
            }, width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("Algorithm Comparison")
    chart_fig = _build_comparison_chart(all_results)
    st.pyplot(chart_fig, use_container_width=True)
    plt.close(chart_fig)

    summary_cols = st.columns(len(all_results))
    for col, r in zip(summary_cols, all_results):
        with col:
            st.caption(
                f"**{r.algorithm}**  \n"
                f"{'Success' if r.success else 'Failed'}"
                f"{'  CBS capped' if r.capped else ''}  \n"
                f"Runtime: {r.runtime_ms:.1f} ms"
            )


if __name__ == "__main__":
    main()
