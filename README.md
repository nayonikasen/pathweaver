# PathWeaver

PathWeaver is a multi-agent pathfinding (MAPF) simulator that plans collision-free routes for multiple agents on a 2D grid and compares the behavior of four coordination algorithms side by side. It is designed for educational use and as a foundation for visual tooling, with real-world applications in warehouse robotics, autonomous vehicle coordination, and drone fleet management.

## Algorithms

| Algorithm | Approach | Conflict-free? |
|---|---|---|
| Independent Planning | Each agent plans without awareness of others | No — baseline only |
| Prioritized Planning | Sequential space-time A\* with a shared reservation table; blocks vertex and edge (swap) conflicts | Usually, but not guaranteed |
| Cooperative A\* | Same as Prioritized but checks vertex conflicts only, not edge conflicts | Usually, but not guaranteed |
| Conflict-Based Search (CBS) | Two-level search: low-level space-time A\* with per-agent constraints, high-level constraint tree expanded by cost; detects and resolves both vertex and swap (edge) conflicts | Yes, within node cap |

CBS detects and resolves both vertex and swap (edge) conflicts, and is optimal when it completes within its node cap (default 200). Prioritized and Cooperative A\* may leave residual conflicts when an earlier agent's path passes through a later agent's permanent goal cell — this is a known property of priority-based planning, not a bug.

## Project Structure

```
pathweaver/
  grid.py          Grid, Coord, neighbors, in_bounds, passable
  algorithms.py    All four MAPF algorithms plus supporting types
                   (ReservationTable, Constraint, CBSNode)
  metrics.py       run_comparison(), format_comparison_table(),
                   AlgorithmResult, AgentStats
  scenarios.py     Four preset scenarios (Scenario, ALL_SCENARIOS,
                   get_scenario())
  app.py           Streamlit UI — primary demo
  main.py          Single-agent development demo
  mapf.py          Legacy module — position_at used by app.py
  multi_demo.py    Multi-agent development demo
results.md            Latest benchmark output from validate_scenarios.py
person1_smoke.py      Single-agent algorithm smoke tests
person2_handoff.py    Full integration checks for MAPF core
validate_scenarios.py Scenario validation script
```

## Preset Scenarios

| Name | Grid | Description |
|---|---|---|
| `crossing` | 20×20 | Two pairs of agents whose paths intersect head-on at guaranteed collision timesteps |
| `bottleneck` | 20×20 | Four agents must funnel through a single-cell gap in a vertical wall |
| `warehouse` | 20×20 | Four agents navigate around shelf-style obstacle rows |
| `dense` | 15×15 | Four agents in a tighter grid with a checkerboard obstacle pattern |

## Grid Editor

The app includes a built-in **Grid Editor** for creating custom scenarios directly in the browser. Open the "Grid Editor — Build Your Own Scenario" expander at the top of the page to:

- Set a custom grid size (5×5 up to 30×30)
- Add or remove individual obstacle cells by coordinate
- Place agents by specifying start and goal coordinates

Check **Use custom grid for next Run** before clicking **Run** to plan paths on your custom layout with all four algorithms simultaneously.

## Setup and Usage

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the integration checks:

```bash
python3 person1_smoke.py
python3 person2_handoff.py
```

Run the Streamlit UI:

```bash
python -m streamlit run pathweaver/app.py
```

> **Note:** `python -m streamlit` is required when running from the repo root so that the `pathweaver` package is resolved correctly on the Python path. The bare `streamlit run` command may fail with an import error on Windows.

Run the development demos:

```bash
# Single-agent pathfinding
python3 -m pathweaver.main

# Multi-agent planning with scenario presets
python3 -m pathweaver.multi_demo
```

## Metrics

Each algorithm run produces an `AlgorithmResult` with:

- **Makespan** — timesteps until the last agent reaches its goal
- **Total cost** — sum of all individual path lengths
- **Conflict count** — remaining vertex and swap (edge) conflicts in the final paths
- **Runtime** — wall-clock time in milliseconds
- **Per-agent stats** — path length and wait steps for each agent

Use `run_comparison(grid, agents)` to run all four algorithms on the same problem and `format_comparison_table(results)` to print a summary table.

## Known Limitations

- CBS is practical for 2–5 agents. The node cap (default 200) prevents exponential blowup on hard instances but means CBS may fall back to the best solution found rather than the proven optimum.
- Prioritized and Cooperative A\* are order-dependent. Earlier agents do not account for cells that later agents will occupy as permanent goals, which can leave isolated conflicts in adversarial layouts.
- Cooperative A\* uses vertex-only reservations and does not prevent swap conflicts. It is included as a comparison point to demonstrate the impact of edge constraint checking.
