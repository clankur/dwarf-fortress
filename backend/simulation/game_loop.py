"""Fixed-timestep game loop running as an asyncio task."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from backend.config import TICK_INTERVAL

if TYPE_CHECKING:
    from backend.simulation.game_state import GameState

logger = logging.getLogger(__name__)


class GameLoop:
    """Runs the simulation at a fixed tick rate."""

    def __init__(self, game_state: GameState) -> None:
        self.game_state = game_state
        self.running = False
        self.tick_count = 0
        self.paused = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self.running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Game loop started at %.0f ticks/sec", 1.0 / TICK_INTERVAL)

    async def stop(self) -> None:
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Game loop stopped after %d ticks", self.tick_count)

    async def _run(self) -> None:
        last_time = time.monotonic()
        accumulator = 0.0

        while self.running:
            current_time = time.monotonic()
            frame_time = current_time - last_time
            last_time = current_time

            if not self.paused:
                accumulator += frame_time

                # Process ticks, capping at 5 to prevent spiral of death
                ticks_this_frame = 0
                while accumulator >= TICK_INTERVAL and ticks_this_frame < 5:
                    await self._tick()
                    accumulator -= TICK_INTERVAL
                    ticks_this_frame += 1

                if accumulator > TICK_INTERVAL * 5:
                    accumulator = 0.0

            # Sleep to avoid busy-waiting
            await asyncio.sleep(TICK_INTERVAL / 2)

    async def _tick(self) -> None:
        self.tick_count += 1
        await self.game_state.tick(self.tick_count)
