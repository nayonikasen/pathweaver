# Progress Report: PathWeaver – A Visual Multi-Agent Pathfinding System
**Team:** Ansh Sarin, Jay Parikh, Nayonika Sen

## What have you already achieved?

We have completed a fully functional system covering grid infrastructure, all four coordination algorithms, a metrics layer, and an interactive Streamlit UI:

- Interactive 2D grid with obstacle placement and four validated scenario presets (crossing, bottleneck, warehouse, dense).
- Single-agent pathfinding using BFS, DFS, Dijkstra, and A* with Manhattan, Euclidean, and Chebyshev heuristics.
- Multi-agent independent planning as a baseline, with vertex and edge conflict detection.
- Prioritized planning using a shared reservation table with vertex and edge constraints.
- Cooperative A* using vertex-only reservations via space-time A*.
- Conflict-Based Search (CBS) for optimal conflict resolution, capped at 200 expanded nodes to remain interactive. Returns the best solution found if the cap is hit, with a flag surfaced in the UI.
- Metrics module (`metrics.py`) computing makespan, total cost, conflict count, runtime, and per-agent path length and wait steps across all four algorithms on the same scenario.
- Streamlit UI (`app.py`) with scenario dropdown, algorithm selector, frame-by-frame animation slider, conflict highlights, per-agent breakdown table, and a side-by-side algorithm comparison table with the selected algorithm highlighted.

## Challenges / adjustments

CBS becomes slow as agent count and obstacle density increase and is capped at 200 expanded nodes, making it practical for 2–5 agents. A known limitation of Prioritized Planning is that earlier agents cannot be retroactively replanned around later agents' goal cells, which can leave residual conflicts in some scenarios. This is expected behavior and is explained in the UI with an inline info message. Our focus is on demonstrating algorithmic tradeoffs clearly rather than scaling CBS to large instances.

## What remains before final submission

- Scalability analysis: recorded comparison runs for 2–4 agents across all scenarios documenting how makespan and runtime scale with agent count.
- Final report covering problem formulation, algorithm design decisions, results, and limitations.
- Minor UI polish: legend refinement and edge-case handling.

## Code Submission

Full codebase: https://github.com/nayonikasen/pathweaver

Main entry points:
- `pathweaver/app.py` — Streamlit UI (primary demo)
- `pathweaver/main.py` — single-agent dev demo
- `pathweaver/multi_demo.py` — multi-agent dev demo
