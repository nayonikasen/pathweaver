from dataclasses import dataclass
from typing import List, Tuple

from pathweaver.grid import Coord, Grid


@dataclass
class Scenario:
    name: str
    grid: Grid
    agents: List[Tuple[Coord, Coord]]
    description: str
    max_agents: int = 5


def scenario_crossing() -> Scenario:
    grid = Grid(20, 20, set())
    agents = [
        ((3, 8),  (16, 8)),   # horizontal through row 8, reaches (9,8) at t=6
        ((9, 2),  (9, 16)),   # vertical through col 9, reaches (9,8) at t=6 — collision
        ((3, 12), (16, 12)),  # horizontal through row 12, reaches (11,12) at t=8
        ((11, 4), (11, 16)),  # vertical through col 11, reaches (11,12) at t=8 — collision
    ]
    return Scenario(
        name="crossing",
        grid=grid,
        agents=agents,
        description="4 agents whose straight-line paths intersect at the center",
    )


def scenario_bottleneck() -> Scenario:
    obstacles = set()
    for y in range(0, 9):      # y=0..8
        obstacles.add((9, y))
    for y in range(10, 20):    # y=10..19
        obstacles.add((9, y))
    grid = Grid(20, 20, obstacles)
    agents = [
        ((2, 5),  (17, 5)),
        ((2, 9),  (17, 9)),
        ((2, 14), (17, 14)),
        ((17, 5), (2, 5)),
    ]
    return Scenario(
        name="bottleneck",
        grid=grid,
        agents=agents,
        description="4 agents must funnel through a narrow 1-cell corridor",
    )


def scenario_warehouse() -> Scenario:
    obstacles = set()
    for x in range(3, 9):     # row 1: x=3..8, y=4
        obstacles.add((x, 4))
    for x in range(3, 9):     # row 2: x=3..8, y=10
        obstacles.add((x, 10))
    for x in range(11, 17):   # row 3: x=11..16, y=4
        obstacles.add((x, 4))
    for x in range(11, 17):   # row 4: x=11..16, y=10
        obstacles.add((x, 10))
    grid = Grid(20, 20, obstacles)
    agents = [
        ((0, 0),  (19, 19)),
        ((0, 19), (19, 0)),
        ((0, 9),  (19, 9)),
        ((9, 0),  (9, 19)),
    ]
    return Scenario(
        name="warehouse",
        grid=grid,
        agents=agents,
        description="6 agents navigate shelf-style obstacles in a warehouse layout",
    )


def scenario_dense() -> Scenario:
    agent_starts_goals = {
        (0, 0), (14, 14),
        (0, 14), (14, 0),
        (0, 7),  (14, 7),
        (7, 0),  (7, 14),
    }
    obstacles = {
        (x, y)
        for x in range(15)
        for y in range(15)
        if x % 3 == 1 and y % 3 == 1
    } - agent_starts_goals
    grid = Grid(15, 15, obstacles)
    agents = [
        ((0, 0),  (14, 14)),
        ((0, 14), (14, 0)),
        ((0, 7),  (14, 7)),
        ((7, 0),  (7, 14)),
    ]
    return Scenario(
        name="dense",
        grid=grid,
        agents=agents,
        description="4 agents in a tighter grid with high obstacle density",
    )


ALL_SCENARIOS: List[Scenario] = [
    scenario_crossing(),
    scenario_bottleneck(),
    scenario_warehouse(),
    scenario_dense(),
]


def get_scenario(name: str) -> Scenario:
    for s in ALL_SCENARIOS:
        if s.name == name:
            return s
    raise ValueError(f"Unknown scenario: {name!r}. Available: {[s.name for s in ALL_SCENARIOS]}")
