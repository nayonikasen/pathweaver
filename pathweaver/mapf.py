from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from .algorithms import heuristic_manhattan
from .grid import Coord, Grid


@dataclass
class AgentPlan:
    path: List[Coord]


@dataclass
class Constraint:
    agent: int
    time: int
    cell: Coord
    edge_from: Optional[Coord] = None

    @property
    def is_edge(self) -> bool:
        return self.edge_from is not None


@dataclass(order=True)
class CBSNode:
    priority: int
    cost: int = field(compare=False)
    constraints: List[Constraint] = field(compare=False, default_factory=list)
    paths: List[List[Coord]] = field(compare=False, default_factory=list)


def manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors_with_wait(grid: Grid, cell: Coord) -> Iterable[Coord]:
    yield cell
    for nxt in grid.neighbors(cell):
        yield nxt


def position_at(path: List[Coord], t: int) -> Coord:
    if not path:
        raise ValueError("empty path")
    if t < len(path):
        return path[t]
    return path[-1]


def detect_first_conflict(paths: List[List[Coord]]) -> Optional[Tuple[int, int, int, Coord, Optional[Coord]]]:
    if not paths:
        return None
    horizon = max(len(p) for p in paths)
    for t in range(horizon):
        occupied: Dict[Coord, int] = {}
        for i, path in enumerate(paths):
            pos = position_at(path, t)
            if pos in occupied:
                return i, occupied[pos], t, pos, None
            occupied[pos] = i
        if t == 0:
            continue
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                a_prev = position_at(paths[i], t - 1)
                a_now = position_at(paths[i], t)
                b_prev = position_at(paths[j], t - 1)
                b_now = position_at(paths[j], t)
                if a_prev == b_now and b_prev == a_now:
                    return i, j, t, a_now, b_now
    return None


def build_constraint_index(constraints: List[Constraint]) -> Dict[int, List[Constraint]]:
    index: Dict[int, List[Constraint]] = {}
    for c in constraints:
        index.setdefault(c.agent, []).append(c)
    return index


def constraint_violated(constraints: List[Constraint], time: int, cell: Coord, edge_from: Coord) -> bool:
    for c in constraints:
        if c.time != time:
            continue
        if c.is_edge:
            if c.cell == cell and c.edge_from == edge_from:
                return True
        else:
            if c.cell == cell:
                return True
    return False


def time_expanded_a_star(
    grid: Grid,
    start: Coord,
    goal: Coord,
    max_time: int,
    reservations: Optional[Dict[int, set]] = None,
    edge_reservations: Optional[Dict[int, set]] = None,
    constraints: Optional[List[Constraint]] = None,
) -> List[Coord]:
    reservations = reservations or {}
    edge_reservations = edge_reservations or {}
    constraints = constraints or []

    frontier: List[Tuple[int, int, Coord, int]] = []
    heapq.heappush(frontier, (0, 0, start, 0))
    came_from: Dict[Tuple[Coord, int], Tuple[Coord, int] | None] = {(start, 0): None}
    cost_so_far: Dict[Tuple[Coord, int], int] = {(start, 0): 0}
    tie = 0

    while frontier:
        _, _, current, t = heapq.heappop(frontier)
        if current == goal:
            # Reconstruct path to this time
            key = (current, t)
            path = [current]
            while came_from[key] is not None:
                key = came_from[key]
                path.append(key[0])
            path.reverse()
            return path
        if t >= max_time:
            continue
        for nxt in neighbors_with_wait(grid, current):
            nt = t + 1
            if nt in reservations and nxt in reservations[nt]:
                continue
            if nt in edge_reservations and (current, nxt) in edge_reservations[nt]:
                continue
            if constraint_violated(constraints, nt, nxt, current):
                continue
            new_cost = cost_so_far[(current, t)] + 1
            key = (nxt, nt)
            if key not in cost_so_far or new_cost < cost_so_far[key]:
                cost_so_far[key] = new_cost
                priority = new_cost + manhattan(nxt, goal)
                tie += 1
                heapq.heappush(frontier, (priority, tie, nxt, nt))
                came_from[key] = (current, t)
    return []


def independent_planning(grid: Grid, starts: List[Coord], goals: List[Coord]) -> List[List[Coord]]:
    paths = []
    for s, g in zip(starts, goals):
        result = time_expanded_a_star(grid, s, g, max_time=grid.width * grid.height * 2)
        if not result:
            # fallback to static A* (no time dimension)
            from .algorithms import a_star

            r = a_star(grid, s, g, heuristic_manhattan, "Manhattan")
            result = r.path or [s]
        paths.append(result)
    return paths


def prioritized_planning(
    grid: Grid,
    starts: List[Coord],
    goals: List[Coord],
    use_edge_constraints: bool = True,
) -> List[List[Coord]]:
    reservations: Dict[int, set] = {}
    edge_reservations: Dict[int, set] = {}
    paths: List[List[Coord]] = []
    max_time = grid.width * grid.height * 2 + 20

    for idx, (s, g) in enumerate(zip(starts, goals)):
        path = time_expanded_a_star(
            grid,
            s,
            g,
            max_time=max_time,
            reservations=reservations,
            edge_reservations=edge_reservations if use_edge_constraints else {},
        )
        if not path:
            paths.append([s])
            continue
        paths.append(path)
        for t, cell in enumerate(path):
            reservations.setdefault(t, set()).add(cell)
            if t > 0 and use_edge_constraints:
                edge_reservations.setdefault(t, set()).add((path[t - 1], cell))
        # reserve goal for remaining time to prevent collisions at rest
        goal_cell = path[-1]
        for t in range(len(path), max_time):
            reservations.setdefault(t, set()).add(goal_cell)

    return paths


def cooperative_a_star(grid: Grid, starts: List[Coord], goals: List[Coord]) -> List[List[Coord]]:
    return prioritized_planning(grid, starts, goals, use_edge_constraints=False)


def cbs(grid: Grid, starts: List[Coord], goals: List[Coord], max_nodes: int = 200) -> List[List[Coord]]:
    def low_level(agent: int, constraints: List[Constraint]) -> List[Coord]:
        return time_expanded_a_star(
            grid,
            starts[agent],
            goals[agent],
            max_time=grid.width * grid.height * 2 + 20,
            constraints=[c for c in constraints if c.agent == agent],
        )

    root_paths = []
    for i in range(len(starts)):
        path = low_level(i, [])
        if not path:
            path = [starts[i]]
        root_paths.append(path)

    root_cost = sum(len(p) - 1 for p in root_paths)
    root = CBSNode(priority=root_cost, cost=root_cost, constraints=[], paths=root_paths)
    open_list: List[CBSNode] = [root]

    expanded = 0
    while open_list and expanded < max_nodes:
        node = heapq.heappop(open_list)
        expanded += 1
        conflict = detect_first_conflict(node.paths)
        if not conflict:
            return node.paths
        a1, a2, t, cell, other = conflict
        if other is None:
            constraints = [
                Constraint(agent=a1, time=t, cell=cell),
                Constraint(agent=a2, time=t, cell=cell),
            ]
        else:
            constraints = [
                Constraint(agent=a1, time=t, cell=cell, edge_from=other),
                Constraint(agent=a2, time=t, cell=other, edge_from=cell),
            ]

        for c in constraints:
            new_constraints = node.constraints + [c]
            new_paths = [p[:] for p in node.paths]
            replanned = low_level(c.agent, new_constraints)
            if not replanned:
                continue
            new_paths[c.agent] = replanned
            new_cost = sum(len(p) - 1 for p in new_paths)
            heapq.heappush(
                open_list,
                CBSNode(priority=new_cost, cost=new_cost, constraints=new_constraints, paths=new_paths),
            )

    return root_paths
