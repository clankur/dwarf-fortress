"""Tests for creatures, needs, and the creature system."""

import pytest

from backend.entities.creature import (
    Animal,
    Creature,
    CreatureType,
    Dwarf,
    LaborType,
)
from backend.simulation.creature_system import CreatureSystem
from backend.simulation.game_state import GameState
from backend.world.grid import Position, WorldGrid
from backend.world.tile import TileFlag


@pytest.fixture
def walkable_world():
    """A small world with a walkable surface layer."""
    grid = WorldGrid(width=20, height=20, depth=10)
    # Make z=5 a walkable surface
    for y in range(20):
        for x in range(20):
            grid.set_flags(x, y, 5, TileFlag.WALKABLE | TileFlag.HAS_FLOOR)
    return grid


@pytest.fixture
def game_state(walkable_world):
    return GameState(walkable_world)


class TestCreatureNeeds:
    def test_initial_needs_full(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        assert dwarf.hunger == 100.0
        assert dwarf.thirst == 100.0
        assert dwarf.energy == 100.0

    def test_needs_decay_per_tick(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        dwarf.tick_needs()
        assert dwarf.hunger < 100.0
        assert dwarf.thirst < 100.0
        assert dwarf.energy < 100.0

    def test_needs_decay_rate(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        # Tick 100 times
        for _ in range(100):
            dwarf.tick_needs()
        assert dwarf.hunger == pytest.approx(100.0 - 100 * 0.02)
        assert dwarf.thirst == pytest.approx(100.0 - 100 * 0.03)
        assert dwarf.energy == pytest.approx(100.0 - 100 * 0.015)

    def test_needs_floor_at_zero(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        for _ in range(10000):
            if not dwarf.alive:
                break
            dwarf.tick_needs()
        assert dwarf.hunger >= 0.0
        assert dwarf.thirst >= 0.0
        assert dwarf.energy >= 0.0

    def test_starvation_kills(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        dwarf.hunger = 0.01
        dwarf.tick_needs()
        assert not dwarf.alive

    def test_dehydration_kills(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        dwarf.thirst = 0.01
        dwarf.tick_needs()
        assert not dwarf.alive

    def test_low_energy_does_not_kill(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        dwarf.energy = 0.01
        dwarf.tick_needs()
        # Energy depletion alone doesn't kill
        assert dwarf.alive

    def test_dead_creature_no_decay(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        dwarf.alive = False
        dwarf.hunger = 50.0
        dwarf.tick_needs()
        assert dwarf.hunger == 50.0

    def test_needs_food_threshold(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        dwarf.hunger = 30.0
        assert not dwarf.needs_food()
        dwarf.hunger = 29.9
        assert dwarf.needs_food()

    def test_critical_need_sleep(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        dwarf.energy = 5.0
        assert dwarf.critical_need() == "sleep"

    def test_critical_need_eat(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        dwarf.hunger = 10.0
        assert dwarf.critical_need() == "eat"

    def test_critical_need_drink(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        dwarf.thirst = 10.0
        assert dwarf.critical_need() == "drink"

    def test_no_critical_need(self):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        assert dwarf.critical_need() is None


class TestCreatureTypes:
    def test_dwarf_has_labors(self):
        dwarf = Dwarf("Urist", Position(0, 0, 0))
        assert LaborType.MINING in dwarf.enabled_labors
        assert LaborType.HAULING in dwarf.enabled_labors

    def test_animal_slower_decay(self):
        cat = Animal("Mittens", CreatureType.CAT, Position(0, 0, 0))
        assert cat.hunger_decay < Dwarf("X", Position(0, 0, 0)).hunger_decay

    def test_creature_display(self):
        dwarf = Dwarf("Urist", Position(0, 0, 0))
        char, color = dwarf.get_display()
        assert char == "@"
        assert color == "#fff"

    def test_creature_serialize(self):
        dwarf = Dwarf("Urist", Position(3, 4, 5))
        data = dwarf.serialize()
        assert data["name"] == "Urist"
        assert data["x"] == 3
        assert data["y"] == 4
        assert data["z"] == 5
        assert data["char"] == "@"
        assert data["alive"] is True


class TestCreatureSystem:
    def test_add_creature(self):
        system = CreatureSystem()
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        system.add_creature(dwarf)
        assert dwarf.id in system.creatures

    def test_remove_creature(self):
        system = CreatureSystem()
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        system.add_creature(dwarf)
        removed = system.remove_creature(dwarf.id)
        assert removed is dwarf
        assert dwarf.id not in system.creatures

    def test_spatial_index(self):
        system = CreatureSystem()
        pos = Position(5, 5, 5)
        dwarf = Dwarf("Urist", pos)
        system.add_creature(dwarf)
        found = system.get_at_position(pos)
        assert len(found) == 1
        assert found[0] is dwarf

    def test_spatial_index_after_remove(self):
        system = CreatureSystem()
        pos = Position(5, 5, 5)
        dwarf = Dwarf("Urist", pos)
        system.add_creature(dwarf)
        system.remove_creature(dwarf.id)
        found = system.get_at_position(pos)
        assert len(found) == 0

    def test_move_updates_spatial(self):
        system = CreatureSystem()
        old_pos = Position(5, 5, 5)
        new_pos = Position(6, 5, 5)
        dwarf = Dwarf("Urist", old_pos)
        system.add_creature(dwarf)
        system._move_creature(dwarf, new_pos)
        assert len(system.get_at_position(old_pos)) == 0
        assert len(system.get_at_position(new_pos)) == 1

    @pytest.mark.asyncio
    async def test_tick_decays_needs(self, game_state):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        game_state.creature_system.add_creature(dwarf)
        original_hunger = dwarf.hunger
        await game_state.creature_system.tick(game_state, 1)
        assert dwarf.hunger < original_hunger

    @pytest.mark.asyncio
    async def test_tick_moves_creature_along_path(self, game_state):
        dwarf = Dwarf("Urist", Position(5, 5, 5))
        dwarf.current_path = [
            Position(5, 5, 5),
            Position(6, 5, 5),
            Position(7, 5, 5),
        ]
        dwarf.path_index = 1
        dwarf.move_cooldown = 0
        game_state.creature_system.add_creature(dwarf)

        await game_state.creature_system.tick(game_state, 1)
        assert dwarf.position == Position(6, 5, 5)

    def test_serialize_all(self):
        system = CreatureSystem()
        system.add_creature(Dwarf("A", Position(0, 0, 0)))
        system.add_creature(Dwarf("B", Position(1, 0, 0)))
        data = system.serialize_all()
        assert len(data) == 2
        names = {d["name"] for d in data}
        assert names == {"A", "B"}
