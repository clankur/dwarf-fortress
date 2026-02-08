"""Serialization of world state for WebSocket transmission."""

from __future__ import annotations

from typing import Any

from backend.config import MAP_DEPTH, MAP_HEIGHT, MAP_WIDTH, SURFACE_Z
from backend.world.grid import WorldGrid
from backend.world.tile import TileFlag, TileType


def serialize_tile(world: WorldGrid, x: int, y: int, z: int) -> dict[str, Any]:
    """Serialize a single tile to a JSON-compatible dict."""
    return {
        "x": x,
        "y": y,
        "z": z,
        "wall": int(world.get_wall_type(x, y, z)),
        "floor": int(world.get_floor_type(x, y, z)),
        "flags": int(world.get_flags(x, y, z)),
    }


def serialize_z_level(world: WorldGrid, z: int) -> list[list[dict[str, int]]]:
    """Serialize an entire z-level as a 2D array of tile data.

    Returns a 2D list [y][x] of compact tile dicts {w, f, fl}.
    """
    level = []
    for y in range(world.height):
        row = []
        for x in range(world.width):
            row.append({
                "w": int(world.wall_types[z, y, x]),
                "f": int(world.floor_types[z, y, x]),
                "fl": int(world.flags[z, y, x]),
            })
        level.append(row)
    return level


def serialize_world_snapshot(world: WorldGrid) -> dict[str, Any]:
    """Serialize the full world state for initial WebSocket connection."""
    return {
        "type": "snapshot",
        "width": world.width,
        "height": world.height,
        "depth": world.depth,
        "surface_z": SURFACE_Z,
        "creatures": [],
        "items": [],
    }


def serialize_z_level_snapshot(world: WorldGrid, z: int) -> dict[str, Any]:
    """Serialize a single z-level snapshot (sent on z-level change)."""
    return {
        "type": "z_level",
        "z": z,
        "tiles": serialize_z_level(world, z),
    }


def serialize_delta(
    world: WorldGrid,
    changed_tiles: set[tuple[int, int, int]],
    creatures: list[dict[str, Any]] | None = None,
    items: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Serialize only changed data since last tick."""
    if not changed_tiles and not creatures and not items:
        return None

    delta: dict[str, Any] = {"type": "delta"}

    if changed_tiles:
        delta["tiles"] = [
            serialize_tile(world, x, y, z)
            for x, y, z in changed_tiles
        ]

    if creatures:
        delta["creatures"] = creatures

    if items:
        delta["items"] = items

    return delta
