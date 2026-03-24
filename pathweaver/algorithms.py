from __future__ import annotations

import heapq
import math
import time
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
