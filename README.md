# Dwarf Fortress Clone

A Dwarf Fortress-inspired colony simulation. Python/FastAPI backend streams game state via WebSocket to a thin JS frontend.

## Quickstart

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest -v

# Start backend (terminal 1)
uv run uvicorn backend.main:app --reload --port 8000

# Serve frontend (terminal 2)
cd frontend && python -m http.server 3000
```

Then open http://localhost:3000

## Controls

- **Arrow keys / WASD**: Scroll viewport
- **< / >**: Change z-level
- **Space**: Pause/unpause
