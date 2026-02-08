"""Terrain generation for the world grid."""

from __future__ import annotations

import random

import numpy as np

from backend.config import MAP_DEPTH, MAP_HEIGHT, MAP_WIDTH, SURFACE_Z
from backend.world.grid import WorldGrid
from backend.world.tile import TileFlag, TileType


def generate_world(
    width: int = MAP_WIDTH,
    height: int = MAP_HEIGHT,
    depth: int = MAP_DEPTH,
    seed: int | None = None,
) -> WorldGrid:
    """Generate a new world with terrain, ores, and caverns."""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    grid = WorldGrid(width, height, depth)

    _generate_terrain(grid)
    _generate_ores(grid)
    _generate_caverns(grid)
    _generate_water(grid)

    return grid


def _generate_terrain(grid: WorldGrid) -> None:
    """Generate basic terrain layers."""
    soil_depth = 4  # layers of soil below surface

    for z in range(grid.depth):
        if z > SURFACE_Z:
            # Sky: empty air
            grid.wall_types[z, :, :] = TileType.AIR
            grid.flags[z, :, :] = TileFlag.NONE
        elif z == SURFACE_Z:
            # Surface: open air with grass floor, walkable
            grid.wall_types[z, :, :] = TileType.AIR
            grid.floor_types[z, :, :] = TileType.GRASS
            grid.flags[z, :, :] = TileFlag.WALKABLE | TileFlag.HAS_FLOOR
        elif z > SURFACE_Z - soil_depth:
            # Soil layers (solid, diggable)
            grid.wall_types[z, :, :] = TileType.SOIL
            grid.floor_types[z, :, :] = TileType.SOIL
            grid.flags[z, :, :] = TileFlag.DIGGABLE
        else:
            # Stone layers (solid, diggable)
            grid.wall_types[z, :, :] = TileType.STONE
            grid.floor_types[z, :, :] = TileType.STONE
            grid.flags[z, :, :] = TileFlag.DIGGABLE


def _generate_ores(grid: WorldGrid) -> None:
    """Sprinkle ore veins in stone layers."""
    ore_types = [TileType.IRON_ORE, TileType.COPPER_ORE, TileType.GOLD_ORE]
    ore_counts = [30, 25, 10]  # number of clusters per ore type

    for ore_type, count in zip(ore_types, ore_counts):
        max_z = min(SURFACE_Z - 5, grid.depth - 2)
        if max_z < 1 or grid.width < 12 or grid.height < 12:
            continue
        for _ in range(count):
            # Pick a random center in stone layers
            cx = random.randint(5, grid.width - 6)
            cy = random.randint(5, grid.height - 6)
            cz = random.randint(1, max_z)

            # Create a small cluster (3-8 tiles)
            cluster_size = random.randint(3, 8)
            for _ in range(cluster_size):
                ox = cx + random.randint(-2, 2)
                oy = cy + random.randint(-2, 2)
                oz = cz + random.randint(-1, 1)
                if grid.in_bounds(ox, oy, oz) and grid.get_wall_type(ox, oy, oz) == TileType.STONE:
                    grid.set_wall_type(ox, oy, oz, ore_type)


def _generate_caverns(grid: WorldGrid) -> None:
    """Create 1-2 cavern layers."""
    cavern_depths = [15, 8]  # z-levels for cavern ceilings

    for cavern_z in cavern_depths:
        if cavern_z >= SURFACE_Z or cavern_z >= grid.depth:
            continue

        # Need enough space for rooms
        margin = min(20, grid.width // 4, grid.height // 4)
        if margin < 2 or grid.width - margin - 1 < margin or grid.height - margin - 1 < margin:
            continue

        # Create irregular cavern shape using random walk
        num_rooms = random.randint(3, 6)
        for _ in range(num_rooms):
            cx = random.randint(margin, grid.width - margin - 1)
            cy = random.randint(margin, grid.height - margin - 1)
            room_w = random.randint(4, 12)
            room_h = random.randint(4, 12)

            for dy in range(-room_h // 2, room_h // 2 + 1):
                for dx in range(-room_w // 2, room_w // 2 + 1):
                    x, y = cx + dx, cy + dy
                    if not grid.in_bounds(x, y, cavern_z):
                        continue
                    # Rounded edges
                    if dx * dx + dy * dy > (max(room_w, room_h) // 2 + 1) ** 2:
                        continue
                    grid.dig_tile(x, y, cavern_z)


def _generate_water(grid: WorldGrid) -> None:
    """Create a few surface water pools."""
    if grid.width < 22 or grid.height < 22:
        return

    num_pools = random.randint(1, 3)

    for _ in range(num_pools):
        cx = random.randint(10, grid.width - 11)
        cy = random.randint(10, grid.height - 11)
        pool_r = random.randint(2, 5)

        for dy in range(-pool_r, pool_r + 1):
            for dx in range(-pool_r, pool_r + 1):
                if dx * dx + dy * dy > pool_r * pool_r:
                    continue
                x, y = cx + dx, cy + dy
                z = SURFACE_Z
                if not grid.in_bounds(x, y, z):
                    continue
                grid.set_wall_type(x, y, z, TileType.WATER)
                grid.set_floor_type(x, y, z, TileType.WATER)
                grid.set_flags(x, y, z, TileFlag.HAS_FLOOR)
