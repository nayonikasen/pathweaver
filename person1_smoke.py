from pathweaver.algorithms import (
    astar_path,
    bfs_path,
    dfs_path,
    dijkstra_path,
    heuristic_chebyshev,
    heuristic_euclidean,
    heuristic_manhattan,
    independent_planning,
)
from pathweaver.grid import Grid


def main() -> int:
    grid = Grid(10, 10, {(3, 3), (3, 4), (3, 5), (4, 5), (5, 5)})
    start = (1, 1)
    goal = (8, 8)

    for heuristic in (heuristic_manhattan, heuristic_euclidean, heuristic_chebyshev):
        path = astar_path(grid, start, goal, heuristic)
        if not path:
            print("A* failed to find a path.")
            return 1

    if not bfs_path(grid, start, goal):
        print("BFS failed to find a path.")
        return 1
    if not dfs_path(grid, start, goal):
        print("DFS failed to find a path.")
        return 1
    if not dijkstra_path(grid, start, goal):
        print("Dijkstra failed to find a path.")
        return 1

    agents = [
        ((1, 1), (8, 8)),
        ((1, 8), (8, 1)),
    ]
    paths = independent_planning(grid, agents)
    if len(paths) != len(agents):
        print("Independent planning returned the wrong number of paths.")
        return 1

    print("Person 1 smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
