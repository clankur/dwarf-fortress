"""Central game state container - holds all systems and world data."""

from __future__ import annotations

import logging
from typing import Any

from backend.simulation.creature_system import CreatureSystem
from backend.world.grid import WorldGrid

logger = logging.getLogger(__name__)


class GameState:
    """Holds the entire game state and orchestrates system ticks."""

    def __init__(self, world: WorldGrid) -> None:
        self.world = world
        self.creature_system = CreatureSystem()
        self.systems: list[Any] = []
        self._changed_tiles: set[tuple[int, int, int]] = set()

    def register_system(self, system: Any) -> None:
        self.systems.append(system)

    def mark_tile_changed(self, x: int, y: int, z: int) -> None:
        self._changed_tiles.add((x, y, z))

    def pop_changed_tiles(self) -> set[tuple[int, int, int]]:
        changed = self._changed_tiles
        self._changed_tiles = set()
        return changed

    async def tick(self, tick_number: int) -> None:
        # Creature system always ticks first
        await self.creature_system.tick(self, tick_number)

        for system in self.systems:
            await system.tick(self, tick_number)
