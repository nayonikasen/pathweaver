from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import pygame

from .algorithms import (
    a_star,
    bfs,
    heuristic_chebyshev,
    heuristic_euclidean,
    heuristic_manhattan,
)
from .grid import Coord, Grid, SearchResult


@dataclass
class AlgoChoice:
    key: str
    label: str
    run: callable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PathWeaver single-agent prototype")
    parser.add_argument("--size", type=int, default=30, help="Grid size (20-60 recommended)")
    parser.add_argument("--cell", type=int, default=22, help="Cell size in pixels")
    return parser.parse_args()


def screen_to_cell(pos: Tuple[int, int], cell_size: int) -> Coord:
    x, y = pos
    return x // cell_size, y // cell_size


def clamp_grid_size(size: int) -> int:
    return max(10, min(80, size))


def run() -> None:
    args = parse_args()
    grid_size = clamp_grid_size(args.size)
    cell_size = max(12, min(32, args.cell))
    width_px = grid_size * cell_size
    height_px = grid_size * cell_size + 140

    pygame.init()
    screen = pygame.display.set_mode((width_px, height_px))
    pygame.display.set_caption("PathWeaver - Single Agent Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 16)
    font_small = pygame.font.SysFont("Arial", 14)

    grid = Grid(grid_size, grid_size, set())
    start: Coord = (2, 2)
    goal: Coord = (grid_size - 3, grid_size - 3)
    result: Optional[SearchResult] = None
    algo_choice = "1"
    placing_mode: Optional[str] = None

    def run_search() -> None:
        nonlocal result
        if start == goal:
            result = None
            return
        if algo_choice == "1":
            result = bfs(grid, start, goal)
        elif algo_choice == "2":
            result = a_star(grid, start, goal, heuristic_manhattan, "Manhattan")
        elif algo_choice == "3":
            result = a_star(grid, start, goal, heuristic_euclidean, "Euclidean")
        else:
            result = a_star(grid, start, goal, heuristic_chebyshev, "Chebyshev")

    def draw_cell(cell: Coord, color: Tuple[int, int, int]) -> None:
        x, y = cell
        rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
        pygame.draw.rect(screen, color, rect)

    def draw_grid() -> None:
        for x in range(grid_size):
            pygame.draw.line(screen, (220, 220, 220), (x * cell_size, 0), (x * cell_size, grid_size * cell_size))
        for y in range(grid_size):
            pygame.draw.line(screen, (220, 220, 220), (0, y * cell_size), (grid_size * cell_size, y * cell_size))

    def draw_overlay() -> None:
        y0 = grid_size * cell_size + 10
        lines = [
            "Controls: left click toggle obstacle, S set start, G set goal",
            "1 BFS, 2 A* Manhattan, 3 A* Euclidean, 4 A* Chebyshev, SPACE run, R reset path, C clear obstacles",
        ]
        for i, line in enumerate(lines):
            screen.blit(font_small.render(line, True, (30, 30, 30)), (10, y0 + i * 18))

        status = f"Algo: {algo_label()} | Start: {start} Goal: {goal}"
        screen.blit(font.render(status, True, (20, 20, 20)), (10, y0 + 46))

        if result:
            stats = result.stats
            summary = (
                f"Visited: {stats.visited}  Path: {stats.path_length}  "
                f"Runtime: {stats.runtime_ms:.2f} ms  Found: {stats.found}"
            )
            screen.blit(font.render(summary, True, (20, 20, 20)), (10, y0 + 70))

    def algo_label() -> str:
        if algo_choice == "1":
            return "BFS"
        if algo_choice == "2":
            return "A* Manhattan"
        if algo_choice == "3":
            return "A* Euclidean"
        return "A* Chebyshev"

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_1:
                    algo_choice = "1"
                elif event.key == pygame.K_2:
                    algo_choice = "2"
                elif event.key == pygame.K_3:
                    algo_choice = "3"
                elif event.key == pygame.K_4:
                    algo_choice = "4"
                elif event.key == pygame.K_SPACE:
                    run_search()
                elif event.key == pygame.K_r:
                    result = None
                elif event.key == pygame.K_c:
                    grid.clear()
                    result = None
                elif event.key == pygame.K_s:
                    placing_mode = "start"
                elif event.key == pygame.K_g:
                    placing_mode = "goal"
                elif event.key == pygame.K_o:
                    placing_mode = "obstacle"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[1] < grid_size * cell_size:
                    cell = screen_to_cell(event.pos, cell_size)
                    if placing_mode == "start":
                        if cell not in grid.obstacles and cell != goal:
                            start = cell
                            result = None
                    elif placing_mode == "goal":
                        if cell not in grid.obstacles and cell != start:
                            goal = cell
                            result = None
                    else:
                        if cell != start and cell != goal:
                            grid.toggle(cell)
                            result = None

        screen.fill((245, 245, 245))
        for cell in grid.obstacles:
            draw_cell(cell, (40, 40, 40))

        if result:
            for cell in result.came_from.keys():
                if cell not in grid.obstacles and cell not in (start, goal):
                    draw_cell(cell, (210, 232, 255))
            for cell in result.path:
                if cell not in (start, goal):
                    draw_cell(cell, (255, 213, 128))

        draw_cell(start, (60, 170, 80))
        draw_cell(goal, (200, 80, 80))

        draw_grid()
        draw_overlay()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    run()
