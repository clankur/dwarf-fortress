"""Tests for A* pathfinding on the 3D grid."""

import pytest

from backend.ai.pathfinding import _find_path_sync, find_path
from backend.world.grid import Position, WorldGrid
from backend.world.tile import TileFlag


@pytest.fixture
def flat_grid():
    """A 20x20 world with a walkable flat surface at z=5."""
    grid = WorldGrid(width=20, height=20, depth=10)
    for y in range(20):
        for x in range(20):
            grid.set_flags(x, y, 5, TileFlag.WALKABLE | TileFlag.HAS_FLOOR)
    return grid


@pytest.fixture
def grid_with_wall(flat_grid):
    """Flat grid with a wall blocking the path at x=10."""
    for y in range(20):
        flat_grid.set_flags(10, y, 5, TileFlag.NONE)
    # Leave a gap at y=15
    flat_grid.set_flags(10, 15, 5, TileFlag.WALKABLE | TileFlag.HAS_FLOOR)
    return flat_grid


@pytest.fixture
def grid_with_stairs():
    """Grid with stair connections between z=5 and z=6."""
    grid = WorldGrid(width=10, height=10, depth=10)
    # Walkable surfaces at z=5 and z=6
    for y in range(10):
        for x in range(10):
            grid.set_flags(x, y, 5, TileFlag.WALKABLE | TileFlag.HAS_FLOOR)
            grid.set_flags(x, y, 6, TileFlag.WALKABLE | TileFlag.HAS_FLOOR)
    # Stair at (5, 5)
    grid.add_flag(5, 5, 5, TileFlag.HAS_STAIR_UP)
    grid.add_flag(5, 5, 6, TileFlag.HAS_STAIR_DOWN)
    return grid


class TestSyncPathfinding:
    def test_same_position(self, flat_grid):
        start = Position(5, 5, 5)
        path = _find_path_sync(start, start, flat_grid)
        assert path == [start]

    def test_straight_line(self, flat_grid):
        start = Position(0, 5, 5)
        goal = Position(5, 5, 5)
        path = _find_path_sync(start, goal, flat_grid)
        assert path is not None
        assert path[0] == start
        assert path[-1] == goal
        assert len(path) == 6  # 5 steps + start

    def test_path_around_wall(self, grid_with_wall):
        start = Position(5, 5, 5)
        goal = Position(15, 5, 5)
        path = _find_path_sync(start, goal, grid_with_wall)
        assert path is not None
        assert path[0] == start
        assert path[-1] == goal
        # Path should go through the gap at y=15
        positions = {(p.x, p.y) for p in path}
        assert (10, 15) in positions

    def test_no_path_to_unwalkable(self, flat_grid):
        start = Position(5, 5, 5)
        goal = Position(5, 5, 7)  # z=7 is not walkable
        path = _find_path_sync(start, goal, flat_grid)
        assert path is None

    def test_no_path_blocked(self):
        """Completely surrounded - no path exists."""
        grid = WorldGrid(width=10, height=10, depth=5)
        # Only one walkable tile
        grid.set_flags(5, 5, 2, TileFlag.WALKABLE | TileFlag.HAS_FLOOR)
        grid.set_flags(8, 8, 2, TileFlag.WALKABLE | TileFlag.HAS_FLOOR)
        start = Position(5, 5, 2)
        goal = Position(8, 8, 2)
        path = _find_path_sync(start, goal, grid)
        assert path is None

    def test_path_across_z_via_stairs(self, grid_with_stairs):
        start = Position(2, 2, 5)
        goal = Position(2, 2, 6)
        path = _find_path_sync(start, goal, grid_with_stairs)
        assert path is not None
        assert path[0] == start
        assert path[-1] == goal
        # Must go through the stair at (5,5)
        z_changes = [(path[i], path[i + 1]) for i in range(len(path) - 1) if path[i].z != path[i + 1].z]
        assert len(z_changes) == 1
        stair_from = z_changes[0][0]
        assert stair_from.x == 5 and stair_from.y == 5

    def test_max_iterations_limit(self, flat_grid):
        start = Position(0, 0, 5)
        goal = Position(19, 19, 5)
        # Very low iteration limit should fail to find path
        path = _find_path_sync(start, goal, flat_grid, max_iterations=5)
        assert path is None

    def test_path_is_contiguous(self, flat_grid):
        """Each step in the path should be adjacent to the previous."""
        start = Position(0, 0, 5)
        goal = Position(10, 10, 5)
        path = _find_path_sync(start, goal, flat_grid)
        assert path is not None
        for i in range(len(path) - 1):
            dist = path[i].manhattan_distance(path[i + 1])
            assert dist == 1 or (dist == 2 and path[i].z != path[i + 1].z)


class TestAsyncPathfinding:
    @pytest.mark.asyncio
    async def test_async_finds_path(self, flat_grid):
        start = Position(0, 5, 5)
        goal = Position(5, 5, 5)
        path = await find_path(start, goal, flat_grid)
        assert path is not None
        assert path[0] == start
        assert path[-1] == goal

    @pytest.mark.asyncio
    async def test_async_returns_none(self, flat_grid):
        start = Position(0, 0, 5)
        goal = Position(0, 0, 9)  # unreachable
        path = await find_path(start, goal, flat_grid)
        assert path is None

    @pytest.mark.asyncio
    async def test_async_does_not_block(self, flat_grid):
        """Verify the async version can be awaited (basic sanity)."""
        import asyncio
        start = Position(0, 0, 5)
        goal = Position(19, 19, 5)
        # Run multiple pathfinds concurrently
        results = await asyncio.gather(
            find_path(start, goal, flat_grid),
            find_path(goal, start, flat_grid),
        )
        assert all(r is not None for r in results)
