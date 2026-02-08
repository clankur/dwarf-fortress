"""Async A* pathfinding on the 3D world grid."""

from __future__ import annotations

import asyncio
import heapq
from typing import TYPE_CHECKING

from backend.world.grid import Position

if TYPE_CHECKING:
    from backend.world.grid import WorldGrid


def _find_path_sync(
    start: Position,
    goal: Position,
    world: WorldGrid,
    max_iterations: int = 10000,
) -> list[Position] | None:
    """A* pathfinding on the 3D grid. Returns path as list of positions, or None."""
    if start == goal:
        return [start]

    if not world.is_walkable(goal.x, goal.y, goal.z):
        return None

    # Priority queue: (f_score, counter, position)
    counter = 0
    open_set: list[tuple[int, int, tuple[int, int, int]]] = []
    start_key = start.to_tuple()
    goal_key = goal.to_tuple()
    heapq.heappush(open_set, (0, counter, start_key))

    came_from: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    g_score: dict[tuple[int, int, int], int] = {start_key: 0}

    iterations = 0
    while open_set and iterations < max_iterations:
        iterations += 1
        _, _, current_key = heapq.heappop(open_set)

        if current_key == goal_key:
            # Reconstruct path
            path = []
            key = current_key
            while key in came_from:
                path.append(Position(key[0], key[1], key[2]))
                key = came_from[key]
            path.append(start)
            path.reverse()
            return path

        cx, cy, cz = current_key
        neighbors = world.get_neighbors_3d(cx, cy, cz)

        for neighbor in neighbors:
            n_key = neighbor.to_tuple()
            # Movement cost: 1 for horizontal, 2 for z-level change
            move_cost = 1 if neighbor.z == cz else 2
            tentative_g = g_score[current_key] + move_cost

            if n_key not in g_score or tentative_g < g_score[n_key]:
                g_score[n_key] = tentative_g
                # Heuristic: 3D Manhattan distance
                h = abs(neighbor.x - goal.x) + abs(neighbor.y - goal.y) + abs(neighbor.z - goal.z)
                f_score = tentative_g + h
                counter += 1
                heapq.heappush(open_set, (f_score, counter, n_key))
                came_from[n_key] = current_key

    return None  # No path found


async def find_path(
    start: Position,
    goal: Position,
    world: WorldGrid,
    max_iterations: int = 10000,
) -> list[Position] | None:
    """Async wrapper that runs A* in a thread pool to avoid blocking."""
    return await asyncio.to_thread(
        _find_path_sync, start, goal, world, max_iterations
    )
