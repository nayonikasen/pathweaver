from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set, Tuple

Coord = Tuple[int, int]


@dataclass
class Grid:
    width: int
    height: int
    obstacles: Set[Coord]

    def in_bounds(self, cell: Coord) -> bool:
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def passable(self, cell: Coord) -> bool:
        return cell not in self.obstacles

    def neighbors(self, cell: Coord) -> Iterable[Coord]:
        x, y = cell
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        for nx, ny in candidates:
            nxt = (nx, ny)
            if self.in_bounds(nxt) and self.passable(nxt):
                yield nxt

    def clear(self) -> None:
        self.obstacles.clear()

    def toggle(self, cell: Coord) -> None:
        if cell in self.obstacles:
            self.obstacles.remove(cell)
        else:
            self.obstacles.add(cell)

    def clone(self) -> "Grid":
        return Grid(self.width, self.height, set(self.obstacles))


@dataclass
class SearchStats:
    visited: int
    path_length: int
    cost: int
    runtime_ms: float
    found: bool
    algorithm: str
    heuristic: str | None


@dataclass
class SearchResult:
    path: List[Coord]
    came_from: dict[Coord, Coord | None]
    stats: SearchStats
