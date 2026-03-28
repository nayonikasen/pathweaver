from pathweaver.algorithms import (
    conflict_based_search,
    cooperative_astar,
    prioritized_planning,
)
from pathweaver.grid import Grid
from pathweaver.metrics import format_comparison_table, run_comparison


def count_vertex_conflicts(paths):
    if not paths:
        return 0
    max_t = max(len(p) for p in paths)

    def pos_at(path, t):
        if not path:
            return None
        return path[min(t, len(path) - 1)]

    count = 0
    for t in range(max_t):
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                pi = pos_at(paths[i], t)
                pj = pos_at(paths[j], t)
                if pi is not None and pj is not None and pi == pj:
                    count += 1
    return count


def main() -> int:
    grid = Grid(10, 10, {(3, 3), (3, 4), (3, 5), (4, 5), (5, 5)})
    agents = [
        ((1, 1), (8, 8)),
        ((1, 8), (8, 1)),
        ((0, 5), (9, 5)),
    ]

    failures = []

    # Test 1: prioritized_planning — 3 non-empty paths, no vertex conflicts
    paths_pp = prioritized_planning(grid, agents)
    if len(paths_pp) == 3 and all(len(p) > 0 for p in paths_pp) and count_vertex_conflicts(paths_pp) == 0:
        print("PASS  1: prioritized_planning")
    else:
        print(f"FAIL  1: prioritized_planning — paths={[len(p) for p in paths_pp]}, conflicts={count_vertex_conflicts(paths_pp)}")
        failures.append(1)

    # Test 2: cooperative_astar — 3 non-empty paths
    paths_ca = cooperative_astar(grid, agents)
    if len(paths_ca) == 3 and all(len(p) > 0 for p in paths_ca):
        print("PASS  2: cooperative_astar")
    else:
        print(f"FAIL  2: cooperative_astar — paths={[len(p) for p in paths_ca]}")
        failures.append(2)

    # Test 3: conflict_based_search — 3 non-empty paths, no vertex conflicts
    paths_cbs, _ = conflict_based_search(grid, agents)
    if len(paths_cbs) == 3 and all(len(p) > 0 for p in paths_cbs) and count_vertex_conflicts(paths_cbs) == 0:
        print("PASS  3: conflict_based_search")
    else:
        print(f"FAIL  3: conflict_based_search — paths={[len(p) for p in paths_cbs]}, conflicts={count_vertex_conflicts(paths_cbs)}")
        failures.append(3)

    # Test 4: run_comparison — 4 results, all with algorithm name set
    results = run_comparison(grid, agents)
    expected_names = {"Independent", "Prioritized", "Cooperative A*", "CBS"}
    actual_names = {r.algorithm for r in results}
    if len(results) == 4 and actual_names == expected_names:
        print("PASS  4: run_comparison")
    else:
        print(f"FAIL  4: run_comparison — got {len(results)} results with names {actual_names}")
        failures.append(4)

    # Test 5: formatted comparison table
    print()
    print(format_comparison_table(results))
    print()

    if not failures:
        print("Person 2 smoke test passed.")
        return 0
    else:
        print(f"Failed checks: {failures}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
