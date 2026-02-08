"""Need-based autonomous decision making for creatures."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from backend.ai.pathfinding import find_path
from backend.world.grid import Position

if TYPE_CHECKING:
    from backend.entities.creature import Creature
    from backend.simulation.game_state import GameState


async def decide_action(creature: Creature, game_state: GameState) -> None:
    """Decide what a creature should do this tick.

    Priority order:
    1. Critical needs (sleep if energy<10, eat if hunger<15, drink if thirst<15)
    2. Continue current job
    3. Find new job from job board
    4. Address non-critical needs (eat if hunger<30, etc.)
    5. Idle wander
    """
    if not creature.alive:
        return

    # If already moving along a path, continue
    if creature.current_path and creature.path_index < len(creature.current_path):
        return

    # Critical needs override everything
    critical = creature.critical_need()
    if critical == "sleep":
        # Just sleep in place for now (restores energy)
        # TODO: requires a bed
        creature.energy = min(100.0, creature.energy + 1.0)
        return

    if critical in ("eat", "drink"):
        # TODO: requires: seeking food/drink
        # For now, slowly restore to prevent death
        if critical == "eat":
            creature.hunger = min(100.0, creature.hunger + 0.5)
        else:
            creature.thirst = min(100.0, creature.thirst + 0.5)
        return

    # Check if we have a current job (Phase 3 will implement this fully)
    if creature.current_job_id:
        return

    # Try to find a new job from the job board (Phase 3)
    job_board = getattr(game_state, "job_board", None)
    if job_board is not None:
        from backend.jobs.job_board import try_claim_job
        await try_claim_job(creature, game_state)
        if creature.current_job_id:
            return

    # Non-critical needs
    if creature.needs_food() or creature.needs_drink() or creature.needs_sleep():
        if creature.needs_sleep():
            creature.energy = min(100.0, creature.energy + 0.5)
        return

    # Idle: wander randomly
    await _wander(creature, game_state)


async def _wander(creature: Creature, game_state: GameState) -> None:
    """Pick a random nearby walkable tile and path to it."""
    world = game_state.world
    pos = creature.position

    # TODO: actions like walking should incorporate personality
    # ie). lazy guy will walk slowly, very motivated energetic fast but burns energy

    # Try random directions
    candidates = []
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            nx, ny = pos.x + dx, pos.y + dy
            if world.is_walkable(nx, ny, pos.z) and (dx != 0 or dy != 0):
                candidates.append(Position(nx, ny, pos.z))

    if candidates:
        target = random.choice(candidates)
        path = await find_path(pos, target, world, max_iterations=200)
        if path and len(path) > 1:
            creature.current_path = path
            creature.path_index = 1  # Skip starting position
