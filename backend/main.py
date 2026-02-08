"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.api.websocket import manager
from backend.config import SURFACE_Z
from backend.entities.creature import Dwarf
from backend.simulation.game_loop import GameLoop
from backend.simulation.game_state import GameState
from backend.world.grid import Position
from backend.world.worldgen import generate_world

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DWARF_NAMES = [
    "Urist", "Doren", "Fikod", "Litast", "Zuglar", "Melbil", "Eshtan",
]

game_state: GameState | None = None
game_loop: GameLoop | None = None


def _spawn_starting_dwarves(state: GameState) -> None:
    """Spawn 7 dwarves on the surface near the map center."""
    world = state.world
    cx, cy = world.width // 2, world.height // 2
    walk_z = SURFACE_Z  # surface is walkable air with grass floor

    spawned = 0
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            if spawned >= len(DWARF_NAMES):
                return
            x, y = cx + dx, cy + dy
            if world.is_walkable(x, y, walk_z):
                dwarf = Dwarf(DWARF_NAMES[spawned], Position(x, y, walk_z))
                state.creature_system.add_creature(dwarf)
                spawned += 1
    logger.info("Spawned %d dwarves", spawned)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global game_state, game_loop

    logger.info("Generating world...")
    world = generate_world(seed=42)
    logger.info("World generated")

    game_state = GameState(world)
    _spawn_starting_dwarves(game_state)
    manager.set_game_state(game_state)

    game_loop = GameLoop(game_state)
    await game_loop.start()

    yield

    await game_loop.stop()


app = FastAPI(title="Dwarf Fortress", lifespan=lifespan)
app.include_router(router, prefix="/api")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await manager.handle_client(websocket)


# Serve frontend static files at root (must be after other routes)
_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
