"""Tile model and enums for the 3D world grid."""

from enum import IntEnum, IntFlag


class TileType(IntEnum):
    """Types of wall/floor materials."""
    AIR = 0
    SOIL = 1
    STONE = 2
    GRANITE = 3
    WATER = 4
    MAGMA = 5
    GRASS = 6
    IRON_ORE = 7
    COPPER_ORE = 8
    GOLD_ORE = 9


class TileFlag(IntFlag):
    """Bit flags for tile properties."""
    NONE = 0
    WALKABLE = 1 << 0
    DIGGABLE = 1 << 1
    HAS_FLOOR = 1 << 2
    HAS_STAIR_UP = 1 << 3
    HAS_STAIR_DOWN = 1 << 4
    HAS_RAMP = 1 << 5
    HAS_BUILDING = 1 << 6
    DESIGNATED = 1 << 7
