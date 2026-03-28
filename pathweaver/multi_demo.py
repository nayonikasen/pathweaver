from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

from pathweaver.grid import Coord, Grid
from pathweaver.mapf import (
    cooperative_a_star,
    cbs,
    independent_planning,
    position_at,
    prioritized_planning,
)


@dataclass
class Agent:
    start: Coord
    goal: Coord
    color: Tuple[int, int, int]
    path: List[Coord]


@dataclass
class Conflict:
    kind: str
    time: int
    cell: Coord
    other_cell: Optional[Coord] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PathWeaver multi-agent planner")
    parser.add_argument("--size", type=int, default=30, help="Grid size (20-60 recommended)")
    parser.add_argument("--cell", type=int, default=22, help="Cell size in pixels")
    return parser.parse_args()


def clamp_grid_size(size: int) -> int:
    return max(10, min(80, size))


def screen_to_cell(pos: Tuple[int, int], cell_size: int) -> Coord:
    x, y = pos
    return x // cell_size, y // cell_size


def detect_conflicts(agents: List[Agent], t: int) -> List[Conflict]:
    conflicts: List[Conflict] = []
    occupied = {}
    for idx, agent in enumerate(agents):
        pos = position_at(agent.path, t) if agent.path else agent.start
        if pos in occupied:
            conflicts.append(Conflict("vertex", t, pos))
        else:
            occupied[pos] = idx
    if t == 0:
        return conflicts
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            a_prev = position_at(agents[i].path, t - 1)
            a_now = position_at(agents[i].path, t)
            b_prev = position_at(agents[j].path, t - 1)
            b_now = position_at(agents[j].path, t)
            if a_prev == b_now and b_prev == a_now:
                conflicts.append(Conflict("edge", t, a_now, b_now))
    return conflicts


def scenario_warehouse(grid_size: int) -> Tuple[Grid, List[Coord], List[Coord]]:
    grid = Grid(grid_size, grid_size, set())
    for x in range(2, grid_size - 2, 4):
        for y in range(2, grid_size - 2):
            if y % 3 != 0:
                grid.obstacles.add((x, y))
    starts = [(1, 1), (1, grid_size - 2), (grid_size - 2, 1), (grid_size - 2, grid_size - 2)]
    goals = [(grid_size - 3, 2), (grid_size - 3, grid_size - 3), (2, grid_size - 3), (2, 2)]
    return grid, starts, goals


def scenario_corridor(grid_size: int) -> Tuple[Grid, List[Coord], List[Coord]]:
    grid = Grid(grid_size, grid_size, set())
    for x in range(grid_size):
        for y in range(grid_size):
            if y not in (grid_size // 2 - 1, grid_size // 2, grid_size // 2 + 1):
                if x % 2 == 0:
                    grid.obstacles.add((x, y))
    starts = [(0, grid_size // 2 - 1), (0, grid_size // 2 + 1)]
    goals = [(grid_size - 1, grid_size // 2 + 1), (grid_size - 1, grid_size // 2 - 1)]
    return grid, starts, goals


def scenario_dense(grid_size: int) -> Tuple[Grid, List[Coord], List[Coord]]:
    grid = Grid(grid_size, grid_size, set())
    for x in range(1, grid_size - 1):
        for y in range(1, grid_size - 1):
            if (x + y) % 5 == 0:
                grid.obstacles.add((x, y))
    starts = [(1, 1), (1, grid_size - 2), (grid_size - 2, 1)]
    goals = [(grid_size - 2, grid_size - 2), (grid_size - 2, 1), (1, grid_size - 2)]
    return grid, starts, goals


def run() -> None:
    args = parse_args()
    grid_size = clamp_grid_size(args.size)
    cell_size = max(12, min(32, args.cell))
    width_px = grid_size * cell_size
    height_px = grid_size * cell_size + 190

    pygame.init()
    screen = pygame.display.set_mode((width_px, height_px))
    pygame.display.set_caption("PathWeaver - Multi-Agent Planning")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 16)
    font_small = pygame.font.SysFont("Arial", 14)

    grid = Grid(grid_size, grid_size, set())
    agents: List[Agent] = []
    palette = [
        (44, 123, 182),
        (230, 124, 60),
        (84, 179, 119),
        (180, 78, 129),
        (122, 154, 91),
        (204, 94, 98),
        (78, 111, 176),
        (201, 162, 56),
    ]

    placing_mode: Optional[str] = None
    pending_start: Optional[Coord] = None
    sim_running = False
    sim_time = 0
    conflicts: List[Conflict] = []
    algo = "independent"

    def add_agent(start: Coord, goal: Coord) -> None:
        color = palette[len(agents) % len(palette)]
        agents.append(Agent(start=start, goal=goal, color=color, path=[]))

    def reset_sim() -> None:
        nonlocal sim_time, sim_running, conflicts
        sim_time = 0
        sim_running = False
        conflicts = []

    def plan_all() -> None:
        nonlocal sim_time, conflicts
        starts = [a.start for a in agents]
        goals = [a.goal for a in agents]
        if algo == "independent":
            paths = independent_planning(grid, starts, goals)
        elif algo == "prioritized":
            paths = prioritized_planning(grid, starts, goals, use_edge_constraints=True)
        elif algo == "cooperative":
            paths = cooperative_a_star(grid, starts, goals)
        else:
            paths = cbs(grid, starts, goals)
        for agent, path in zip(agents, paths):
            agent.path = path
        sim_time = 0
        conflicts = detect_conflicts(agents, sim_time)

    def load_scenario(kind: str) -> None:
        nonlocal grid, agents
        if kind == "warehouse":
            grid, starts, goals = scenario_warehouse(grid_size)
        elif kind == "corridor":
            grid, starts, goals = scenario_corridor(grid_size)
        else:
            grid, starts, goals = scenario_dense(grid_size)
        agents = []
        for s, g in zip(starts, goals):
            add_agent(s, g)
        reset_sim()

    def draw_cell(cell: Coord, color: Tuple[int, int, int]) -> None:
        x, y = cell
        rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
        pygame.draw.rect(screen, color, rect)

    def draw_grid() -> None:
        for x in range(grid_size):
            pygame.draw.line(screen, (220, 220, 220), (x * cell_size, 0), (x * cell_size, grid_size * cell_size))
        for y in range(grid_size):
            pygame.draw.line(screen, (220, 220, 220), (0, y * cell_size), (grid_size * cell_size, y * cell_size))

    def draw_agents() -> None:
        for agent in agents:
            draw_cell(agent.goal, tuple(min(255, c + 60) for c in agent.color))
        for agent in agents:
            if agent.path:
                for cell in agent.path:
                    if cell not in (agent.start, agent.goal):
                        draw_cell(cell, tuple(max(0, c - 40) for c in agent.color))
        for agent in agents:
            pos = position_at(agent.path, sim_time) if agent.path else agent.start
            draw_cell(pos, agent.color)

    def draw_conflicts() -> None:
        for conflict in conflicts:
            x, y = conflict.cell
            rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, (200, 40, 40), rect, 3)

    def metrics() -> Tuple[int, int, int]:
        if not agents:
            return 0, 0, 0
        makespan = max((len(a.path) - 1 for a in agents if a.path), default=0)
        total_cost = sum((len(a.path) - 1 for a in agents if a.path))
        conflict_count = len(conflicts)
        return makespan, total_cost, conflict_count

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_n:
                    placing_mode = "agent_start"
                    pending_start = None
                elif event.key == pygame.K_c:
                    grid.clear()
                    reset_sim()
                elif event.key == pygame.K_x:
                    agents.clear()
                    reset_sim()
                elif event.key == pygame.K_SPACE:
                    plan_all()
                elif event.key == pygame.K_r:
                    reset_sim()
                elif event.key == pygame.K_p:
                    if agents:
                        sim_running = not sim_running
                elif event.key == pygame.K_o:
                    placing_mode = "obstacle"
                elif event.key == pygame.K_1:
                    algo = "independent"
                elif event.key == pygame.K_2:
                    algo = "prioritized"
                elif event.key == pygame.K_3:
                    algo = "cooperative"
                elif event.key == pygame.K_4:
                    algo = "cbs"
                elif event.key == pygame.K_w:
                    load_scenario("warehouse")
                elif event.key == pygame.K_d:
                    load_scenario("dense")
                elif event.key == pygame.K_k:
                    load_scenario("corridor")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[1] < grid_size * cell_size:
                    cell = screen_to_cell(event.pos, cell_size)
                    if placing_mode == "agent_start":
                        if cell not in grid.obstacles:
                            pending_start = cell
                            placing_mode = "agent_goal"
                    elif placing_mode == "agent_goal":
                        if cell not in grid.obstacles and pending_start and cell != pending_start:
                            add_agent(pending_start, cell)
                            placing_mode = None
                            pending_start = None
                            reset_sim()
                    else:
                        if cell not in {a.start for a in agents} and cell not in {a.goal for a in agents}:
                            grid.toggle(cell)
                            reset_sim()

        if sim_running and agents:
            sim_time += 1
            conflicts = detect_conflicts(agents, sim_time)

        screen.fill((245, 245, 245))
        for cell in grid.obstacles:
            draw_cell(cell, (40, 40, 40))
        draw_agents()
        draw_conflicts()
        draw_grid()

        y0 = grid_size * cell_size + 10
        lines = [
            "Controls: click toggle obstacle, N add agent (start then goal), O obstacle mode",
            "SPACE plan, P play/pause, R reset sim, X clear agents, C clear obstacles",
            "1 independent, 2 prioritized, 3 cooperative A*, 4 CBS",
            "W warehouse, K corridor, D dense scenario",
        ]
        for i, line in enumerate(lines):
            screen.blit(font_small.render(line, True, (30, 30, 30)), (10, y0 + i * 18))

        makespan, total_cost, conflict_count = metrics()
        status = f"Agents: {len(agents)}  Time: {sim_time}  Conflicts: {conflict_count}"
        screen.blit(font.render(status, True, (20, 20, 20)), (10, y0 + 78))
        summary = f"Algo: {algo}  Makespan: {makespan}  Total Cost: {total_cost}"
        screen.blit(font.render(summary, True, (20, 20, 20)), (10, y0 + 102))

        pygame.display.flip()
        clock.tick(8)

    pygame.quit()


if __name__ == "__main__":
    run()
