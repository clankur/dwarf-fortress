"""Tests for world grid, tiles, and world generation."""

import pytest
from backend.world.grid import WorldGrid, Position
from backend.world.tile import TileType, TileFlag
from backend.world.worldgen import generate_world
from backend.config import SURFACE_Z


class TestPosition:
    def test_equality(self):
        p1 = Position(1, 2, 3)
        p2 = Position(1, 2, 3)
        assert p1 == p2

    def test_inequality(self):
        p1 = Position(1, 2, 3)
        p2 = Position(4, 5, 6)
        assert p1 != p2

    def test_hash(self):
        p1 = Position(1, 2, 3)
        p2 = Position(1, 2, 3)
        assert hash(p1) == hash(p2)
        assert len({p1, p2}) == 1

    def test_manhattan_distance(self):
        p1 = Position(0, 0, 0)
        p2 = Position(3, 4, 5)
        assert p1.manhattan_distance(p2) == 12


class TestWorldGrid:
    def test_in_bounds(self, small_grid):
        assert small_grid.in_bounds(0, 0, 0)
        assert small_grid.in_bounds(15, 15, 15)
        assert not small_grid.in_bounds(-1, 0, 0)
        assert not small_grid.in_bounds(16, 0, 0)
        assert not small_grid.in_bounds(0, 16, 0)
        assert not small_grid.in_bounds(0, 0, 16)

    def test_set_get_wall_type(self, small_grid):
        small_grid.set_wall_type(5, 5, 5, TileType.STONE)
        assert small_grid.get_wall_type(5, 5, 5) == TileType.STONE

    def test_set_get_floor_type(self, small_grid):
        small_grid.set_floor_type(3, 3, 3, TileType.GRANITE)
        assert small_grid.get_floor_type(3, 3, 3) == TileType.GRANITE

    def test_flags(self, small_grid):
        small_grid.set_flags(1, 1, 1, TileFlag.WALKABLE | TileFlag.HAS_FLOOR)
        assert small_grid.has_flag(1, 1, 1, TileFlag.WALKABLE)
        assert small_grid.has_flag(1, 1, 1, TileFlag.HAS_FLOOR)
        assert not small_grid.has_flag(1, 1, 1, TileFlag.DIGGABLE)

    def test_add_remove_flag(self, small_grid):
        small_grid.set_flags(2, 2, 2, TileFlag.WALKABLE)
        small_grid.add_flag(2, 2, 2, TileFlag.HAS_FLOOR)
        assert small_grid.has_flag(2, 2, 2, TileFlag.WALKABLE)
        assert small_grid.has_flag(2, 2, 2, TileFlag.HAS_FLOOR)

        small_grid.remove_flag(2, 2, 2, TileFlag.WALKABLE)
        assert not small_grid.has_flag(2, 2, 2, TileFlag.WALKABLE)
        assert small_grid.has_flag(2, 2, 2, TileFlag.HAS_FLOOR)

    def test_is_walkable(self, small_grid):
        assert not small_grid.is_walkable(0, 0, 0)
        small_grid.add_flag(0, 0, 0, TileFlag.WALKABLE)
        assert small_grid.is_walkable(0, 0, 0)

    def test_is_walkable_out_of_bounds(self, small_grid):
        assert not small_grid.is_walkable(-1, 0, 0)
        assert not small_grid.is_walkable(100, 0, 0)

    def test_get_neighbors_2d(self, small_grid):
        # Make a walkable cross pattern at z=5
        for x, y in [(5, 5), (4, 5), (6, 5), (5, 4), (5, 6)]:
            small_grid.add_flag(x, y, 5, TileFlag.WALKABLE)

        neighbors = small_grid.get_neighbors_2d(5, 5, 5)
        positions = {(n.x, n.y, n.z) for n in neighbors}
        assert positions == {(4, 5, 5), (6, 5, 5), (5, 4, 5), (5, 6, 5)}

    def test_get_neighbors_3d_stairs(self, small_grid):
        # Set up stair connection between z=5 and z=6
        small_grid.set_flags(
            5, 5, 5,
            TileFlag.WALKABLE | TileFlag.HAS_FLOOR | TileFlag.HAS_STAIR_UP,
        )
        small_grid.set_flags(
            5, 5, 6,
            TileFlag.WALKABLE | TileFlag.HAS_FLOOR | TileFlag.HAS_STAIR_DOWN,
        )

        neighbors = small_grid.get_neighbors_3d(5, 5, 5)
        positions = {(n.x, n.y, n.z) for n in neighbors}
        assert (5, 5, 6) in positions

        # Going down from z=6
        neighbors_down = small_grid.get_neighbors_3d(5, 5, 6)
        positions_down = {(n.x, n.y, n.z) for n in neighbors_down}
        assert (5, 5, 5) in positions_down

    def test_get_tiles_in_rect(self, small_grid):
        tiles = small_grid.get_tiles_in_rect(2, 3, 4, 5, 0)
        assert len(tiles) == 9  # 3x3

    def test_dig_tile(self, small_grid):
        small_grid.set_wall_type(5, 5, 5, TileType.STONE)
        small_grid.set_flags(5, 5, 5, TileFlag.DIGGABLE)

        old_type = small_grid.dig_tile(5, 5, 5)
        assert old_type == TileType.STONE
        assert small_grid.get_wall_type(5, 5, 5) == TileType.AIR
        assert small_grid.is_walkable(5, 5, 5)
        assert small_grid.has_flag(5, 5, 5, TileFlag.HAS_FLOOR)

    def test_carve_stairs(self, small_grid):
        small_grid.set_wall_type(5, 5, 5, TileType.STONE)
        small_grid.carve_stair_updown(5, 5, 5)

        assert small_grid.get_wall_type(5, 5, 5) == TileType.AIR
        assert small_grid.is_walkable(5, 5, 5)
        assert small_grid.has_flag(5, 5, 5, TileFlag.HAS_STAIR_UP)
        assert small_grid.has_flag(5, 5, 5, TileFlag.HAS_STAIR_DOWN)

    def test_channel_tile(self, small_grid):
        small_grid.set_wall_type(5, 5, 5, TileType.STONE)
        small_grid.set_wall_type(5, 5, 4, TileType.STONE)

        small_grid.channel_tile(5, 5, 5)
        # Channeled tile has no floor
        assert not small_grid.has_flag(5, 5, 5, TileFlag.HAS_FLOOR)
        # Tile below should be dug out with a ramp
        assert small_grid.is_walkable(5, 5, 4)
        assert small_grid.has_flag(5, 5, 4, TileFlag.HAS_RAMP)


class TestWorldGen:
    def test_generates_valid_terrain(self):
        world = generate_world(width=32, height=32, depth=32, seed=42)
        assert world.width == 32
        assert world.height == 32
        assert world.depth == 32

    def test_surface_is_grass(self):
        world = generate_world(width=32, height=32, depth=48, seed=42)
        # Surface at SURFACE_Z should have grass floor
        grass_count = 0
        for y in range(world.height):
            for x in range(world.width):
                if world.get_floor_type(x, y, SURFACE_Z) == TileType.GRASS:
                    grass_count += 1
        # Most surface tiles should be grass (some may be water)
        assert grass_count > world.width * world.height * 0.8

    def test_surface_is_walkable(self):
        world = generate_world(width=32, height=32, depth=48, seed=42)
        # Surface z-level should be walkable
        walkable_count = 0
        for y in range(world.height):
            for x in range(world.width):
                if world.is_walkable(x, y, SURFACE_Z):
                    walkable_count += 1
        assert walkable_count > 0

    def test_underground_is_stone(self):
        world = generate_world(width=32, height=32, depth=48, seed=42)
        # Deep underground should be stone (or ore)
        stone_like = {TileType.STONE, TileType.IRON_ORE, TileType.COPPER_ORE, TileType.GOLD_ORE}
        stone_count = 0
        z = 5  # Deep underground
        for y in range(world.height):
            for x in range(world.width):
                wt = world.get_wall_type(x, y, z)
                if wt in stone_like:
                    stone_count += 1
        # Most deep tiles should be stone-like (caverns may have dug-out areas)
        total = world.width * world.height
        assert stone_count > total * 0.5

    def test_deterministic_with_seed(self):
        world1 = generate_world(width=16, height=16, depth=32, seed=123)
        world2 = generate_world(width=16, height=16, depth=32, seed=123)

        import numpy as np
        assert np.array_equal(world1.wall_types, world2.wall_types)
        assert np.array_equal(world1.floor_types, world2.floor_types)
        assert np.array_equal(world1.flags, world2.flags)

    def test_ores_exist(self):
        world = generate_world(width=64, height=64, depth=48, seed=42)
        ore_types = {TileType.IRON_ORE, TileType.COPPER_ORE, TileType.GOLD_ORE}
        found_ores = set()
        for z in range(SURFACE_Z):
            for y in range(world.height):
                for x in range(world.width):
                    wt = world.get_wall_type(x, y, z)
                    if wt in ore_types:
                        found_ores.add(wt)
        assert len(found_ores) == 3  # All three ore types should be present
