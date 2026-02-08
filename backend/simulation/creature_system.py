"""System that ticks all creatures: needs, AI decisions, movement."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.ai.decision import decide_action
from backend.entities.creature import Creature
from backend.world.grid import Position

if TYPE_CHECKING:
    from backend.simulation.game_state import GameState

logger = logging.getLogger(__name__)

# How many ticks between AI decisions (don't re-decide every tick)
AI_DECISION_INTERVAL = 10
# How many ticks between moves along a path
MOVE_INTERVAL = 3


class CreatureSystem:
    """Manages all creatures: stores them, ticks needs/AI/movement."""

    def __init__(self) -> None:
        self.creatures: dict[str, Creature] = {}
        # Spatial index: position tuple -> set of creature IDs
        self._spatial: dict[tuple[int, int, int], set[str]] = {}

    def add_creature(self, creature: Creature) -> None:
        self.creatures[creature.id] = creature
        self._add_to_spatial(creature)

    def remove_creature(self, creature_id: str) -> Creature | None:
        creature = self.creatures.pop(creature_id, None)
        if creature:
            self._remove_from_spatial(creature)
        return creature

    def get_at_position(self, pos: Position) -> list[Creature]:
        key = pos.to_tuple()
        ids = self._spatial.get(key, set())
        return [self.creatures[cid] for cid in ids if cid in self.creatures]

    def _add_to_spatial(self, creature: Creature) -> None:
        key = creature.position.to_tuple()
        if key not in self._spatial:
            self._spatial[key] = set()
        self._spatial[key].add(creature.id)

    def _remove_from_spatial(self, creature: Creature) -> None:
        key = creature.position.to_tuple()
        if key in self._spatial:
            self._spatial[key].discard(creature.id)
            if not self._spatial[key]:
                del self._spatial[key]

    def _move_creature(self, creature: Creature, new_pos: Position) -> None:
        self._remove_from_spatial(creature)
        creature.position = new_pos
        self._add_to_spatial(creature)

    async def tick(self, game_state: GameState, tick_number: int) -> None:
        for creature in list(self.creatures.values()):
            if not creature.alive:
                continue

            # 1. Decay needs every tick
            creature.tick_needs()
            if not creature.alive:
                continue

            # 2. Move along current path
            if creature.current_path and creature.path_index < len(creature.current_path):
                if creature.move_cooldown <= 0:
                    next_pos = creature.current_path[creature.path_index]
                    if game_state.world.is_walkable(next_pos.x, next_pos.y, next_pos.z):
                        self._move_creature(creature, next_pos)
                    creature.path_index += 1
                    creature.move_cooldown = MOVE_INTERVAL

                    # Clear path if we've reached the end
                    if creature.path_index >= len(creature.current_path):
                        creature.current_path = []
                        creature.path_index = 0
                else:
                    creature.move_cooldown -= 1
                continue

            # 3. AI decision (not every tick)
            if tick_number % AI_DECISION_INTERVAL == 0:
                await decide_action(creature, game_state)

    def serialize_all(self) -> list[dict]:
        return [c.serialize() for c in self.creatures.values()]
