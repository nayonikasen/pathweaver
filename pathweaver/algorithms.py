from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from .grid import Coord, Grid, SearchResult, SearchStats


Heuristic = Callable[[Coord, Coord], float]


def heuristic_manhattan(a: Coord, b: Coord) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def heuristic_euclidean(a: Coord, b: Coord) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def heuristic_chebyshev(a: Coord, b: Coord) -> float:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def reconstruct_path(came_from: Dict[Coord, Optional[Coord]], start: Coord, goal: Coord) -> List[Coord]:
    if goal not in came_from:
        return []
    current = goal
    path = [current]
    while current != start:
        current = came_from[current]
        if current is None:
            return []
        path.append(current)
    path.reverse()
    return path


def bfs(grid: Grid, start: Coord, goal: Coord) -> SearchResult:
    t0 = time.perf_counter()
    frontier: List[Coord] = [start]
    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    head = 0

    while head < len(frontier):
        current = frontier[head]
        head += 1
        if current == goal:
            break
        for nxt in grid.neighbors(current):
            if nxt not in came_from:
                came_from[nxt] = current
                frontier.append(nxt)

    path = reconstruct_path(came_from, start, goal)
    t1 = time.perf_counter()
    stats = SearchStats(
        visited=len(came_from),
        path_length=max(len(path) - 1, 0),
        cost=max(len(path) - 1, 0),
        runtime_ms=(t1 - t0) * 1000.0,
        found=bool(path),
        algorithm="BFS",
        heuristic=None,
    )
    return SearchResult(path=path, came_from=came_from, stats=stats)


def dfs(grid: Grid, start: Coord, goal: Coord) -> SearchResult:
    t0 = time.perf_counter()
    stack: List[Coord] = [start]
    came_from: Dict[Coord, Optional[Coord]] = {start: None}

    while stack:
        current = stack.pop()
        if current == goal:
            break
        for nxt in grid.neighbors(current):
            if nxt not in came_from:
                came_from[nxt] = current
                stack.append(nxt)

    path = reconstruct_path(came_from, start, goal)
    t1 = time.perf_counter()
    stats = SearchStats(
        visited=len(came_from),
        path_length=max(len(path) - 1, 0),
        cost=max(len(path) - 1, 0),
        runtime_ms=(t1 - t0) * 1000.0,
        found=bool(path),
        algorithm="DFS",
        heuristic=None,
    )
    return SearchResult(path=path, came_from=came_from, stats=stats)


def dijkstra(grid: Grid, start: Coord, goal: Coord) -> SearchResult:
    t0 = time.perf_counter()
    frontier: List[Tuple[float, int, Coord]] = []
    heapq.heappush(frontier, (0.0, 0, start))
    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    dist: Dict[Coord, float] = {start: 0.0}
    tie = 0

    while frontier:
        current_cost, _, current = heapq.heappop(frontier)
        if current == goal:
            break
        if current_cost > dist[current]:
            continue
        for nxt in grid.neighbors(current):
            new_cost = dist[current] + 1.0
            if nxt not in dist or new_cost < dist[nxt]:
                dist[nxt] = new_cost
                tie += 1
                heapq.heappush(frontier, (new_cost, tie, nxt))
                came_from[nxt] = current

    path = reconstruct_path(came_from, start, goal)
    t1 = time.perf_counter()
    stats = SearchStats(
        visited=len(came_from),
        path_length=max(len(path) - 1, 0),
        cost=max(len(path) - 1, 0),
        runtime_ms=(t1 - t0) * 1000.0,
        found=bool(path),
        algorithm="Dijkstra",
        heuristic=None,
    )
    return SearchResult(path=path, came_from=came_from, stats=stats)


def a_star(grid: Grid, start: Coord, goal: Coord, heuristic: Heuristic, name: str) -> SearchResult:
    t0 = time.perf_counter()
    frontier: List[Tuple[float, int, Coord]] = []
    heapq.heappush(frontier, (0.0, 0, start))
    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    g_score: Dict[Coord, float] = {start: 0.0}
    tie = 0

    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current == goal:
            break
        for nxt in grid.neighbors(current):
            tentative = g_score[current] + 1.0
            if nxt not in g_score or tentative < g_score[nxt]:
                g_score[nxt] = tentative
                priority = tentative + heuristic(nxt, goal)
                tie += 1
                heapq.heappush(frontier, (priority, tie, nxt))
                came_from[nxt] = current

    path = reconstruct_path(came_from, start, goal)
    t1 = time.perf_counter()
    stats = SearchStats(
        visited=len(came_from),
        path_length=max(len(path) - 1, 0),
        cost=max(len(path) - 1, 0),
        runtime_ms=(t1 - t0) * 1000.0,
        found=bool(path),
        algorithm="A*",
        heuristic=name,
    )
    return SearchResult(path=path, came_from=came_from, stats=stats)


def astar_path(grid: Grid, start: Coord, goal: Coord, heuristic: Heuristic) -> List[Coord]:
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        return []
    if not grid.passable(start) or not grid.passable(goal):
        return []
    if start == goal:
        return [start]
    result = a_star(grid, start, goal, heuristic, "custom")
    return result.path


def bfs_path(grid: Grid, start: Coord, goal: Coord) -> List[Coord]:
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        return []
    if not grid.passable(start) or not grid.passable(goal):
        return []
    if start == goal:
        return [start]
    result = bfs(grid, start, goal)
    return result.path


def dfs_path(grid: Grid, start: Coord, goal: Coord) -> List[Coord]:
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        return []
    if not grid.passable(start) or not grid.passable(goal):
        return []
    if start == goal:
        return [start]
    result = dfs(grid, start, goal)
    return result.path


def dijkstra_path(grid: Grid, start: Coord, goal: Coord) -> List[Coord]:
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        return []
    if not grid.passable(start) or not grid.passable(goal):
        return []
    if start == goal:
        return [start]
    result = dijkstra(grid, start, goal)
    return result.path


def independent_planning(grid: Grid, agents: List[Tuple[Coord, Coord]]) -> List[List[Coord]]:
    paths: List[List[Coord]] = []
    for start, goal in agents:
        path = astar_path(grid, start, goal, heuristic_manhattan)
        paths.append(path)
    return paths


class ReservationTable:
    def __init__(self) -> None:
        self._reserved: set = set()
        self._edge_reserved: set = set()

    def reserve(self, path: List[Coord]) -> None:
        if not path:
            return
        for t, coord in enumerate(path):
            self._reserved.add((coord, t))
        goal = path[-1]
        goal_t = len(path) - 1
        for t in range(goal_t, goal_t + 201):
            self._reserved.add((goal, t))
        if len(path) > 1:
            for t in range(len(path) - 1):
                self._edge_reserved.add((path[t], path[t + 1], t))

    def is_reserved(self, coord: Coord, t: int) -> bool:
        return (coord, t) in self._reserved

    def is_edge_reserved(self, coord_from: Coord, coord_to: Coord, t: int) -> bool:
        return (coord_to, coord_from, t) in self._edge_reserved


def astar_spacetime(
    grid: Grid,
    start: Coord,
    goal: Coord,
    heuristic: Heuristic,
    reservation_table: ReservationTable,
    max_t: int = 200,
    check_edge_conflicts: bool = True,
) -> List[Coord]:
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        return []
    if not grid.passable(start) or not grid.passable(goal):
        return []
    if start == goal and not reservation_table.is_reserved(start, 0):
        return [start]

    # State: (coord, t)
    # frontier entries: (f, tie, coord, t)
    frontier: List[Tuple[float, int, Coord, int]] = []
    heapq.heappush(frontier, (heuristic(start, goal), 0, start, 0))
    came_from: Dict[Tuple[Coord, int], Optional[Tuple[Coord, int]]] = {(start, 0): None}
    g_score: Dict[Tuple[Coord, int], float] = {(start, 0): 0.0}
    tie = 0

    while frontier:
        _, _, current, t = heapq.heappop(frontier)

        if current == goal:
            # Reconstruct path
            path: List[Coord] = []
            state: Optional[Tuple[Coord, int]] = (current, t)
            while state is not None:
                path.append(state[0])
                state = came_from[state]
            path.reverse()
            return path

        if t >= max_t:
            continue

        next_t = t + 1
        # Candidate next positions: neighbors + wait in place
        candidates = list(grid.neighbors(current)) + [current]
        for nxt in candidates:
            if reservation_table.is_reserved(nxt, next_t):
                continue
            if check_edge_conflicts and nxt != current and reservation_table.is_edge_reserved(current, nxt, t):
                continue
            new_g = g_score[(current, t)] + 1.0
            state_key = (nxt, next_t)
            if state_key not in g_score or new_g < g_score[state_key]:
                g_score[state_key] = new_g
                priority = new_g + heuristic(nxt, goal)
                tie += 1
                heapq.heappush(frontier, (priority, tie, nxt, next_t))
                came_from[state_key] = (current, t)

    return []


def prioritized_planning(grid: Grid, agents: List[Tuple[Coord, Coord]]) -> List[List[Coord]]:
    table = ReservationTable()
    paths: List[List[Coord]] = []
    for start, goal in agents:
        path = astar_spacetime(grid, start, goal, heuristic_manhattan, table, check_edge_conflicts=True)
        if path:
            table.reserve(path)
        paths.append(path)
    return paths


def cooperative_astar(grid: Grid, agents: List[Tuple[Coord, Coord]]) -> List[List[Coord]]:
    table = ReservationTable()
    paths: List[List[Coord]] = []
    for start, goal in agents:
        path = astar_spacetime(grid, start, goal, heuristic_manhattan, table, check_edge_conflicts=False)
        if path:
            table.reserve(path)
        paths.append(path)
    return paths


@dataclass
class Constraint:
    agent: int
    coord: Coord
    timestep: int
    edge_from: Optional[Coord] = None


@dataclass
class CBSNode:
    constraints: List[Constraint]
    paths: List[List[Coord]]
    cost: int


def astar_with_constraints(
    grid: Grid,
    start: Coord,
    goal: Coord,
    heuristic: Heuristic,
    agent: int,
    constraints: List[Constraint],
    max_t: int = 200,
) -> List[Coord]:
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        return []
    if not grid.passable(start) or not grid.passable(goal):
        return []

    agent_constraints = [c for c in constraints if c.agent == agent]
    forbidden: set = {(c.coord, c.timestep) for c in agent_constraints}
    edge_forbidden: set = set()
    for c in agent_constraints:
        if c.edge_from is not None:
            edge_forbidden.add((c.edge_from, c.coord, c.timestep))

    if start == goal and (start, 0) not in forbidden:
        return [start]

    frontier: List[Tuple[float, int, Coord, int]] = []
    heapq.heappush(frontier, (heuristic(start, goal), 0, start, 0))
    came_from: Dict[Tuple[Coord, int], Optional[Tuple[Coord, int]]] = {(start, 0): None}
    g_score: Dict[Tuple[Coord, int], float] = {(start, 0): 0.0}
    tie = 0

    while frontier:
        _, _, current, t = heapq.heappop(frontier)

        if current == goal:
            path: List[Coord] = []
            state: Optional[Tuple[Coord, int]] = (current, t)
            while state is not None:
                path.append(state[0])
                state = came_from[state]
            path.reverse()
            return path

        if t >= max_t:
            continue

        next_t = t + 1
        for nxt in list(grid.neighbors(current)) + [current]:
            if (nxt, next_t) in forbidden:
                continue
            if (current, nxt, next_t) in edge_forbidden:
                continue
            new_g = g_score[(current, t)] + 1.0
            state_key = (nxt, next_t)
            if state_key not in g_score or new_g < g_score[state_key]:
                g_score[state_key] = new_g
                priority = new_g + heuristic(nxt, goal)
                tie += 1
                heapq.heappush(frontier, (priority, tie, nxt, next_t))
                came_from[state_key] = (current, t)

    return []


def find_first_conflict(paths: List[List[Coord]]) -> Optional[Tuple[int, int, Coord, int]]:
    if not paths:
        return None
    max_t = max(len(p) for p in paths) if paths else 0

    def pos_at(path: List[Coord], t: int) -> Optional[Coord]:
        if not path:
            return None
        return path[t] if t < len(path) else path[-1]

    for t in range(max_t):
        # Vertex conflicts
        occupied: Dict[Coord, int] = {}
        for i, path in enumerate(paths):
            pi = pos_at(path, t)
            if pi is None:
                continue
            if pi in occupied:
                return (occupied[pi], i, pi, t)
            occupied[pi] = i

        # Swap/edge conflicts
        if t > 0:
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    a_prev = pos_at(paths[i], t - 1)
                    a_now  = pos_at(paths[i], t)
                    b_prev = pos_at(paths[j], t - 1)
                    b_now  = pos_at(paths[j], t)
                    if (a_prev == b_now and b_prev == a_now
                            and a_prev is not None and b_prev is not None):
                        return (i, j, a_now, t)

    return None


def conflict_based_search(
    grid: Grid,
    agents: List[Tuple[Coord, Coord]],
    max_nodes: int = 200,
) -> Tuple[List[List[Coord]], bool]:
    root_paths = [astar_path(grid, start, goal, heuristic_manhattan) for start, goal in agents]
    root_cost = sum(max(len(p) - 1, 0) for p in root_paths)
    root = CBSNode(constraints=[], paths=root_paths, cost=root_cost)

    counter = 0
    heap: List[Tuple[int, int, CBSNode]] = [(root_cost, counter, root)]
    best_node = root

    nodes_expanded = 0
    while heap and nodes_expanded < max_nodes:
        cost, _, node = heapq.heappop(heap)
        nodes_expanded += 1

        if node.cost < best_node.cost:
            best_node = node

        conflict = find_first_conflict(node.paths)
        if conflict is None:
            return node.paths, False

        agent_i, agent_j, coord, t = conflict

        def _pos(path: List[Coord], k: int) -> Optional[Coord]:
            if not path:
                return None
            return path[k] if k < len(path) else path[-1]

        a_prev = _pos(node.paths[agent_i], t - 1)
        b_prev = _pos(node.paths[agent_j], t - 1)
        is_swap = (
            t > 0
            and a_prev is not None
            and b_prev is not None
            and a_prev == _pos(node.paths[agent_j], t)
            and b_prev == _pos(node.paths[agent_i], t)
        )

        if is_swap:
            new_constraint_pairs = [
                (agent_i, Constraint(agent=agent_i, coord=coord,  timestep=t, edge_from=a_prev)),
                (agent_j, Constraint(agent=agent_j, coord=a_prev, timestep=t, edge_from=coord)),
            ]
        else:
            new_constraint_pairs = [
                (agent_i, Constraint(agent=agent_i, coord=coord, timestep=t)),
                (agent_j, Constraint(agent=agent_j, coord=coord, timestep=t)),
            ]

        for agent_idx, new_constraint in new_constraint_pairs:
            new_constraints = node.constraints + [new_constraint]
            new_paths = list(node.paths)
            start, goal = agents[agent_idx]
            new_path = astar_with_constraints(
                grid, start, goal, heuristic_manhattan, agent_idx, new_constraints
            )
            if not new_path:
                continue
            new_paths[agent_idx] = new_path
            new_cost = sum(max(len(p) - 1, 0) for p in new_paths)
            counter += 1
            child = CBSNode(constraints=new_constraints, paths=new_paths, cost=new_cost)
            heapq.heappush(heap, (new_cost, counter, child))

    return best_node.paths, True
