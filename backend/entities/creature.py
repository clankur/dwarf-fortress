"""Creature base class - all living entities inherit from this."""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from backend.world.grid import Position


class CreatureType(str, Enum):
    DWARF = "dwarf"
    CAT = "cat"
    DOG = "dog"
    GOBLIN = "goblin"


class LaborType(str, Enum):
    MINING = "mining"
    MASONRY = "masonry"
    CARPENTRY = "carpentry"
    FARMING = "farming"
    COOKING = "cooking"
    BREWING = "brewing"
    HAULING = "hauling"
    BUILDING = "building"
    WOODCUTTING = "woodcutting"
    HUNTING = "hunting"
    FISHING = "fishing"
    CRAFTING = "crafting"
    SMELTING = "smelting"
    SMITHING = "smithing"
    DOCTORING = "doctoring"


# Display chars and colors per creature type
CREATURE_DISPLAY = {
    CreatureType.DWARF: ("@", "#fff"),
    CreatureType.CAT: ("c", "#c84"),
    CreatureType.DOG: ("d", "#a60"),
    CreatureType.GOBLIN: ("g", "#0f0"),
}


class Creature:
    """Base class for all creatures in the game."""

    def __init__(
        self,
        name: str,
        creature_type: CreatureType,
        position: Position,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.name = name
        self.creature_type = creature_type
        self.position = position
        self.alive = True

        # Needs (0 = empty/critical, 100 = full/satisfied)
        self.hunger = 100.0
        self.thirst = 100.0
        self.energy = 100.0

        # Need decay rates per tick
        self.hunger_decay = 0.02
        self.thirst_decay = 0.03
        self.energy_decay = 0.015

        # Movement
        self.speed = 1.0  # tiles per movement action
        self.current_path: list[Position] = []
        self.path_index = 0
        self.move_cooldown = 0  # ticks until next move

        # Job
        self.current_job_id: str | None = None

        # Skills: SkillType -> Skill (added in Phase 3)
        self.skills: dict[str, Any] = {}

        # Labors this creature can perform
        self.enabled_labors: set[LaborType] = set()

    def tick_needs(self) -> None:
        """Decay needs each tick."""
        if not self.alive:
            return

        self.hunger = max(0.0, self.hunger - self.hunger_decay)
        self.thirst = max(0.0, self.thirst - self.thirst_decay)
        self.energy = max(0.0, self.energy - self.energy_decay)

        # Death from starvation/dehydration
        if self.hunger <= 0.0 or self.thirst <= 0.0:
            self.alive = False

    def needs_food(self) -> bool:
        return self.hunger < 30.0

    def needs_drink(self) -> bool:
        return self.thirst < 30.0

    def needs_sleep(self) -> bool:
        return self.energy < 20.0

    def critical_need(self) -> str | None:
        """Return the most critical unmet need, or None."""
        if self.energy < 10.0:
            return "sleep"
        if self.hunger < 15.0:
            return "eat"
        if self.thirst < 15.0:
            return "drink"
        return None

    def get_display(self) -> tuple[str, str]:
        """Return (char, color) for rendering."""
        char, color = CREATURE_DISPLAY.get(
            self.creature_type, ("?", "#f0f")
        )
        return char, color

    def serialize(self) -> dict[str, Any]:
        """Serialize for WebSocket transmission."""
        char, color = self.get_display()
        return {
            "id": self.id,
            "name": self.name,
            "type": self.creature_type.value,
            "x": self.position.x,
            "y": self.position.y,
            "z": self.position.z,
            "char": char,
            "color": color,
            "alive": self.alive,
            "hunger": round(self.hunger, 1),
            "thirst": round(self.thirst, 1),
            "energy": round(self.energy, 1),
            "job_id": self.current_job_id,
        }


class Dwarf(Creature):
    """A dwarf - the main controllable creature type."""

    def __init__(self, name: str, position: Position) -> None:
        super().__init__(name, CreatureType.DWARF, position)

        # Dwarves can do most labors by default
        self.enabled_labors = {
            LaborType.MINING,
            LaborType.HAULING,
            LaborType.BUILDING,
            LaborType.FARMING,
            LaborType.COOKING,
            LaborType.CRAFTING,
        }


class Animal(Creature):
    """An animal creature."""

    def __init__(
        self,
        name: str,
        creature_type: CreatureType,
        position: Position,
    ) -> None:
        super().__init__(name, creature_type, position)
        # Animals have slower need decay
        self.hunger_decay = 0.01
        self.thirst_decay = 0.015
        self.energy_decay = 0.01
