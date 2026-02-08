"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket

from backend.api.routes import router
from backend.api.websocket import manager
from backend.simulation.game_loop import GameLoop
from backend.simulation.game_state import GameState
from backend.world.worldgen import generate_world

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

game_state: GameState | None = None
game_loop: GameLoop | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global game_state, game_loop

    logger.info("Generating world...")
    world = generate_world(seed=42)
    logger.info("World generated")

    game_state = GameState(world)
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
