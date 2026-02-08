"""Shared test fixtures."""

import pytest

from backend.world.grid import WorldGrid, Position
from backend.world.worldgen import generate_world
from backend.world.tile import TileType, TileFlag
from backend.config import SURFACE_Z


@pytest.fixture
def small_grid():
    """A small 16x16x16 world grid for fast tests."""
    return WorldGrid(width=16, height=16, depth=16)


@pytest.fixture
def generated_world():
    """A fully generated world with deterministic seed."""
    return generate_world(width=32, height=32, depth=32, seed=42)
