from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .algorithms import (
    conflict_based_search,
    cooperative_astar,
    independent_planning,
    prioritized_planning,
)
from .grid import Coord, Grid


@dataclass
class AgentStats:
    agent_id: int
    path_length: int
    wait_steps: int


@dataclass
class AlgorithmResult:
    algorithm: str
    paths: List[List[Coord]]
    makespan: int
    total_cost: int
    conflicts: int
    runtime_ms: float
    success: bool
    per_agent: List[AgentStats]
    capped: bool = False


def compute_wait_steps(path: List[Coord]) -> int:
    return sum(1 for t in range(1, len(path)) if path[t] == path[t - 1])


def count_conflicts(paths: List[List[Coord]]) -> int:
    if not paths:
        return 0
    max_t = max(len(p) for p in paths)

    def pos_at(path: List[Coord], t: int) -> Optional[Coord]:
        if not path:
            return None
        return path[min(t, len(path) - 1)]

    count = 0
    for t in range(max_t):
        # Vertex conflicts
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                pi = pos_at(paths[i], t)
                pj = pos_at(paths[j], t)
                if pi is not None and pj is not None and pi == pj:
                    count += 1

        # Swap conflicts
        if t > 0:
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    a_prev = pos_at(paths[i], t - 1)
                    a_now  = pos_at(paths[i], t)
                    b_prev = pos_at(paths[j], t - 1)
                    b_now  = pos_at(paths[j], t)
                    if a_prev == b_now and b_prev == a_now:
                        count += 1
    return count


def _build_result(algorithm: str, paths: List[List[Coord]], runtime_ms: float) -> AlgorithmResult:
    success = all(len(p) > 0 for p in paths)
    path_lengths = [max(len(p) - 1, 0) for p in paths]
    makespan = max(path_lengths) if path_lengths else 0
    total_cost = sum(path_lengths)
    conflicts = count_conflicts(paths)
    per_agent = [
        AgentStats(
            agent_id=i,
            path_length=path_lengths[i],
            wait_steps=compute_wait_steps(paths[i]) if paths[i] else 0,
        )
        for i in range(len(paths))
    ]
    return AlgorithmResult(
        algorithm=algorithm,
        paths=paths,
        makespan=makespan,
        total_cost=total_cost,
        conflicts=conflicts,
        runtime_ms=runtime_ms,
        success=success,
        per_agent=per_agent,
    )


def run_comparison(grid: Grid, agents: List[Tuple[Coord, Coord]]) -> List[AlgorithmResult]:
    results = []
    for name, fn in [
        ("Independent", independent_planning),
        ("Prioritized", prioritized_planning),
        ("Cooperative A*", cooperative_astar),
    ]:
        t0 = time.perf_counter()
        paths = fn(grid, agents)
        t1 = time.perf_counter()
        results.append(_build_result(name, paths, (t1 - t0) * 1000.0))

    t0 = time.perf_counter()
    cbs_paths, capped = conflict_based_search(grid, agents)
    t1 = time.perf_counter()
    cbs_result = _build_result("CBS", cbs_paths, (t1 - t0) * 1000.0)
    cbs_result.capped = capped
    results.append(cbs_result)

    return results


def format_comparison_table(results: List[AlgorithmResult]) -> str:
    col_widths = [20, 8, 9, 11, 10, 9, 7]
    headers = ["Algorithm", "Success", "Makespan", "Total Cost", "Conflicts", "Time(ms)", "Capped"]
    header_line = "".join(h.ljust(w) for h, w in zip(headers, col_widths))
    rows = [header_line]
    for r in results:
        row = [
            r.algorithm,
            "Yes" if r.success else "No",
            str(r.makespan),
            str(r.total_cost),
            str(r.conflicts),
            f"{r.runtime_ms:.1f}",
            "YES" if r.capped else "-",
        ]
        rows.append("".join(v.ljust(w) for v, w in zip(row, col_widths)))
    return "\n".join(rows)
