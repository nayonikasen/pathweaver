# Progress Report: PathWeaver – A Visual Multi‑Agent Pathfinding System
**Team:** Ansh Sarin, Jay Parikh, Nayonika Sen

## What have you already achieved?
We have completed a functional prototype that covers the core grid simulation and several multi‑agent planning strategies. The current system includes:
- An interactive 2D grid editor with obstacle placement.
- Single‑agent pathfinding (BFS and A* with Manhattan/Euclidean/Chebyshev heuristics).
- Multi‑agent independent planning with conflict detection (vertex and edge conflicts).
- Prioritized planning with reservation tables.
- Cooperative A* (vertex reservations).
- A baseline CBS implementation for optimal conflict resolution on small instances.
- Animated visualization with per‑agent paths, conflict highlighting, and basic metrics (makespan, total cost, conflicts).
- Scenario presets (warehouse, corridor, dense obstacles) for quick demonstrations.

## Immediate next steps
- Add structured performance comparison charts (per algorithm) and exportable metrics.
- Improve CBS performance (node limits, heuristic ordering, caching).
- Expand the UI to show algorithm selection context and per‑agent statistics.
- Add documented test scenarios for 2–8 agents and report scalability.

## Challenges / adjustments
CBS becomes slow as the number of agents and obstacles increases; it is currently best used as a baseline on small instances. We will focus on demonstrating algorithmic tradeoffs rather than pushing CBS to large‑scale performance. We may also simplify cooperative A* visualization to avoid clutter in dense maps.

## Overall plan for the next month (short summary)
Polish the visualization and metrics dashboard, finalize comparisons across algorithms on a consistent scenario set, document scalability results for 2–8 agents, and assemble the final demo + write‑up.

## Code base
Current code is in the local workspace:
`/Users/nayonika/Desktop/FAI/Code`

Main entry points:
- `/Users/nayonika/Desktop/FAI/Code/pathweaver/main.py`
- `/Users/nayonika/Desktop/FAI/Code/pathweaver/multi_demo.py`
