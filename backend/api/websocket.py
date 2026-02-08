"""WebSocket connection management and state streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from backend.api.serialization import (
    serialize_delta,
    serialize_world_snapshot,
    serialize_z_level_snapshot,
)
from backend.simulation.game_state import GameState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts state updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self._game_state: GameState | None = None

    def set_game_state(self, game_state: GameState) -> None:
        self._game_state = game_state

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Client connected (%d total)", len(self.active_connections))

        if self._game_state:
            # Send world metadata snapshot
            snapshot = serialize_world_snapshot(self._game_state.world)
            await websocket.send_json(snapshot)

            # Send the surface z-level tiles
            from backend.config import SURFACE_Z
            z_data = serialize_z_level_snapshot(self._game_state.world, SURFACE_Z + 1)
            await websocket.send_json(z_data)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)
        logger.info("Client disconnected (%d remaining)", len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a message to all connected clients."""
        if not self.active_connections:
            return

        data = json.dumps(message)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.active_connections.remove(conn)

    async def handle_client(self, websocket: WebSocket) -> None:
        """Handle messages from a connected client."""
        try:
            while True:
                data = await websocket.receive_json()
                await self._handle_message(websocket, data)
        except WebSocketDisconnect:
            self.disconnect(websocket)

    async def _handle_message(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        """Process an incoming client message."""
        msg_type = data.get("type")

        if msg_type == "request_z_level":
            z = data.get("z", 0)
            if self._game_state:
                z_data = serialize_z_level_snapshot(self._game_state.world, z)
                await websocket.send_json(z_data)

        elif msg_type == "designate":
            # Will be handled in Phase 3
            pass

        elif msg_type == "pause":
            if self._game_state:
                from backend.main import game_loop
                if game_loop:
                    game_loop.paused = not game_loop.paused
                    await websocket.send_json({
                        "type": "pause_state",
                        "paused": game_loop.paused,
                    })


manager = ConnectionManager()
