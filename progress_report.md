# Progress Report: PathWeaver – A Visual Multi-Agent Pathfinding System
**Team:** Ansh Sarin, Jay Parikh, Nayonika Sen

## What have you already achieved?
We have completed a functional prototype covering the core grid simulation and several multi-agent planning strategies:
- Interactive 2D grid editor with obstacle placement and scenario presets (warehouse, corridor, dense obstacles).
- Single-agent pathfinding using BFS and A* with Manhattan, Euclidean, and Chebyshev heuristics.
- Multi-agent independent planning with vertex and edge conflict detection.
- Prioritized planning with reservation tables (vertex + edge constraints).
- Cooperative A* (prioritized planning with vertex reservations only).
- Baseline CBS implementation for optimal conflict resolution on small instances, capped at 200 expanded nodes to keep it interactive.
- Animated visualization with per-agent paths, conflict highlighting, and metrics (makespan, total cost, conflict count).

## Immediate next steps
- Add structured performance comparison charts per algorithm and exportable metrics.
- Improve CBS performance through heuristic ordering and caching.
- Expand the UI to show per-agent statistics and algorithm selection context.
- Document reproducible test scenarios for 2–8 agents with scalability results.

## Challenges / adjustments
CBS becomes slow as agent count and obstacle density increase. It is currently best suited as a baseline for small instances (2–5 agents) and is capped at 200 expanded nodes. Our focus will be on demonstrating algorithmic tradeoffs across the four planning strategies rather than scaling CBS to large instances. We may also simplify the Cooperative A* visualization to reduce clutter on dense maps.

## Overall plan for the next month
Polish the metrics dashboard and visualization, finalize algorithm comparisons on a consistent scenario set, document scalability results for 2–8 agents, and assemble the final demo and write-up.

## Code Submission
Full codebase: https://github.com/nayonikasen/pathweaver

Main entry points:
- `pathweaver/main.py` — single-agent demo
- `pathweaver/multi_demo.py` — multi-agent planning demo
