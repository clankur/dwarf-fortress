"""3D tile grid backed by NumPy arrays."""

from __future__ import annotations

import numpy as np

from backend.config import MAP_DEPTH, MAP_HEIGHT, MAP_WIDTH
from backend.world.tile import TileFlag, TileType


class Position:
    """3D position in the world."""
    __slots__ = ("x", "y", "z")

    def __init__(self, x: int, y: int, z: int) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            return NotImplemented
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))

    def __repr__(self) -> str:
        return f"Position({self.x}, {self.y}, {self.z})"

    def manhattan_distance(self, other: Position) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y) + abs(self.z - other.z)

    def to_tuple(self) -> tuple[int, int, int]:
        return (self.x, self.y, self.z)


class WorldGrid:
    """3D world grid storing tile data in NumPy arrays.

    Arrays are indexed as [z, y, x] for cache-friendly z-level iteration.
    """

    def __init__(
        self,
        width: int = MAP_WIDTH,
        height: int = MAP_HEIGHT,
        depth: int = MAP_DEPTH,
    ) -> None:
        self.width = width
        self.height = height
        self.depth = depth

        # Wall type for each tile (what fills the tile volume)
        self.wall_types = np.zeros((depth, height, width), dtype=np.uint8)
        # Floor type for each tile (what you walk on)
        self.floor_types = np.zeros((depth, height, width), dtype=np.uint8)
        # Bit flags for each tile
        self.flags = np.zeros((depth, height, width), dtype=np.uint16)
        # Liquid level (0-7)
        self.liquid_levels = np.zeros((depth, height, width), dtype=np.uint8)

    def in_bounds(self, x: int, y: int, z: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth

    def get_wall_type(self, x: int, y: int, z: int) -> TileType:
        return TileType(self.wall_types[z, y, x])

    def get_floor_type(self, x: int, y: int, z: int) -> TileType:
        return TileType(self.floor_types[z, y, x])

    def get_flags(self, x: int, y: int, z: int) -> TileFlag:
        return TileFlag(int(self.flags[z, y, x]))

    def set_wall_type(self, x: int, y: int, z: int, wall_type: TileType) -> None:
        self.wall_types[z, y, x] = wall_type.value

    def set_floor_type(self, x: int, y: int, z: int, floor_type: TileType) -> None:
        self.floor_types[z, y, x] = floor_type.value

    def set_flags(self, x: int, y: int, z: int, flags: TileFlag) -> None:
        self.flags[z, y, x] = flags.value

    def add_flag(self, x: int, y: int, z: int, flag: TileFlag) -> None:
        self.flags[z, y, x] |= flag.value

    def remove_flag(self, x: int, y: int, z: int, flag: TileFlag) -> None:
        self.flags[z, y, x] = int(self.flags[z, y, x]) & ~flag.value

    def has_flag(self, x: int, y: int, z: int, flag: TileFlag) -> bool:
        return bool(self.flags[z, y, x] & flag.value)

    def is_walkable(self, x: int, y: int, z: int) -> bool:
        if not self.in_bounds(x, y, z):
            return False
        return self.has_flag(x, y, z, TileFlag.WALKABLE)

    def get_neighbors_2d(self, x: int, y: int, z: int) -> list[Position]:
        """Get walkable cardinal neighbors on the same z-level."""
        neighbors = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if self.is_walkable(nx, ny, z):
                neighbors.append(Position(nx, ny, z))
        return neighbors

    def get_neighbors_3d(self, x: int, y: int, z: int) -> list[Position]:
        """Get walkable neighbors including z-level transitions via stairs/ramps."""
        neighbors = self.get_neighbors_2d(x, y, z)

        # Check stair transitions
        flags = self.get_flags(x, y, z)

        # Can go up via up-stairs at current tile + down-stairs at tile above
        if TileFlag.HAS_STAIR_UP in flags:
            above_z = z + 1
            if self.in_bounds(x, y, above_z) and self.has_flag(x, y, above_z, TileFlag.HAS_STAIR_DOWN):
                if self.is_walkable(x, y, above_z):
                    neighbors.append(Position(x, y, above_z))

        # Can go down via down-stairs at current tile + up-stairs at tile below
        if TileFlag.HAS_STAIR_DOWN in flags:
            below_z = z - 1
            if self.in_bounds(x, y, below_z) and self.has_flag(x, y, below_z, TileFlag.HAS_STAIR_UP):
                if self.is_walkable(x, y, below_z):
                    neighbors.append(Position(x, y, below_z))

        # Can go down via ramp (ramp at this tile means you can walk to z-1 neighbors)
        if TileFlag.HAS_RAMP in flags:
            below_z = z - 1
            if self.in_bounds(x, y, below_z) and self.is_walkable(x, y, below_z):
                neighbors.append(Position(x, y, below_z))

        return neighbors

    def get_tiles_in_rect(
        self, x1: int, y1: int, x2: int, y2: int, z: int
    ) -> list[Position]:
        """Get all positions in a rectangle on a given z-level."""
        positions = []
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if self.in_bounds(x, y, z):
                    positions.append(Position(x, y, z))
        return positions

    def dig_tile(self, x: int, y: int, z: int) -> TileType:
        """Dig out a tile: remove wall, make walkable, add floor. Returns old wall type."""
        old_wall = self.get_wall_type(x, y, z)
        self.set_wall_type(x, y, z, TileType.AIR)
        self.set_flags(
            x, y, z,
            TileFlag.WALKABLE | TileFlag.HAS_FLOOR,
        )
        # Ensure the tile above has a floor if it's also air
        above_z = z + 1
        if self.in_bounds(x, y, above_z):
            above_wall = self.get_wall_type(x, y, above_z)
            if above_wall == TileType.AIR:
                self.add_flag(x, y, above_z, TileFlag.HAS_FLOOR)
        return old_wall

    def channel_tile(self, x: int, y: int, z: int) -> TileType:
        """Channel a tile: remove wall AND floor, creating a hole. Returns old wall type."""
        old_wall = self.get_wall_type(x, y, z)
        self.set_wall_type(x, y, z, TileType.AIR)
        self.set_floor_type(x, y, z, TileType.AIR)
        self.set_flags(x, y, z, TileFlag.NONE)
        # Add a ramp on the tile below if it's solid
        below_z = z - 1
        if self.in_bounds(x, y, below_z):
            below_wall = self.get_wall_type(x, y, below_z)
            if below_wall != TileType.AIR:
                self.dig_tile(x, y, below_z)
                self.add_flag(x, y, below_z, TileFlag.HAS_RAMP)
                # dig_tile adds HAS_FLOOR to the tile above (z) since it's air,
                # but we channeled it so it should have no floor
                self.set_flags(x, y, z, TileFlag.NONE)
        return old_wall

    def carve_stair_up(self, x: int, y: int, z: int) -> TileType:
        """Carve upward stairs in a tile."""
        old_wall = self.get_wall_type(x, y, z)
        self.set_wall_type(x, y, z, TileType.AIR)
        self.set_flags(
            x, y, z,
            TileFlag.WALKABLE | TileFlag.HAS_FLOOR | TileFlag.HAS_STAIR_UP,
        )
        return old_wall

    def carve_stair_down(self, x: int, y: int, z: int) -> TileType:
        """Carve downward stairs in a tile."""
        old_wall = self.get_wall_type(x, y, z)
        self.set_wall_type(x, y, z, TileType.AIR)
        self.set_flags(
            x, y, z,
            TileFlag.WALKABLE | TileFlag.HAS_FLOOR | TileFlag.HAS_STAIR_DOWN,
        )
        return old_wall

    def carve_stair_updown(self, x: int, y: int, z: int) -> TileType:
        """Carve up/down stairs in a tile."""
        old_wall = self.get_wall_type(x, y, z)
        self.set_wall_type(x, y, z, TileType.AIR)
        self.set_flags(
            x, y, z,
            TileFlag.WALKABLE | TileFlag.HAS_FLOOR | TileFlag.HAS_STAIR_UP | TileFlag.HAS_STAIR_DOWN,
        )
        return old_wall
