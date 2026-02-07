# CLAUDE.md

This file provides guidance for Claude Code (claude.ai/claude-code) when working with this codebase.

## Project Overview

A Dwarf Fortress-inspired colony simulation game. Key features:
- **Backend-authoritative architecture**: Python/FastAPI backend runs all simulation logic
- **Autonomous dwarf AI**: Dwarves autonomously select and execute jobs based on needs and skills
- **Multi-z-level world**: 3D world with digging, building, and terrain modification
- **Job/task system**: Prioritized job queue with skill requirements and resource dependencies
- **Resource management**: Mining, crafting, stockpiles, and production chains
- **WebSocket state streaming**: Real-time state updates to thin JS client

## Coding Principles

**CRITICAL RULES - You MUST follow these without exception:**

### 1. Backend Authority
- **NEVER** put game logic in the frontend. The backend is the ONLY source of truth.
- Frontend's job is ONLY: render `WorldState` and send user input (designations, orders) to backend.
- If you're tempted to add simulation logic to JS/frontend, STOP and put it in Python/backend instead.

### 2. Error Handling
- **NEVER** silently swallow errors with bare `except:` or empty catch blocks.
- Errors MUST be raised, logged, or explicitly handled. Fail loudly.

### 3. Entity Unification
- All creatures (dwarves, animals, enemies) MUST inherit from a common `Creature` base class.
- When adding capabilities, add them to `Creature` base class unless species-specific.
- **DO NOT** create separate action/job types for different creature types.

### 4. Testing Requirements
- **Every bug fix MUST include a regression test** in `tests/`. No exceptions.
- **Every new feature MUST have unit tests** in `tests/`. No "I'll test it manually" - write pytest tests.
- Run `uv run pytest` before considering any change complete.

### 5. Async for Expensive Operations
- Pathfinding, AI decisions, and any I/O MUST be async and non-blocking.
- The simulation loop must never block on expensive calculations.

### 6. No Backwards Compatibility Concerns
- **DO NOT** write migration code, compatibility shims, or preserve old formats.
- If your change breaks saves/cache, that's fine - user can delete `saves/` to reset.
- Just make the clean implementation.

### 7. Code Quality

#### No String-Encoded Data
- **NEVER** pack multiple values into a single string (e.g., `f"{job_type},{target_x},{target_y}"`).
- Use structured API payloads, typed models, or separate fields instead.

#### Type Safety
- **Use Enums** for all finite categories (e.g., `JobType`, `ResourceType`, `SkillType`).
- **Use `Literal` types** for string fields with fixed valid values.
- **NEVER use `str`** with only a comment or docstring hint for valid values.

#### Code Reuse
- **Before implementing new logic**, search for existing similar code.
- When two functions share substantial logic, extract the shared part into a helper.
- **Rule of thumb**: If you're about to copy-paste more than 5 lines, extract a helper function instead.

## Commands

```bash
# Install dependencies (requires uv)
uv sync
uv sync --dev  # Include test dependencies

# Run backend server
uv run uvicorn backend.main:app --reload --port 8000

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_jobs.py

# Run tests with verbose output
uv run pytest -v

# Serve frontend (separate terminal)
cd frontend && python -m http.server 3000
```

## Testing

Tests are in `tests/` using pytest + pytest-asyncio. Run with `uv run pytest -v` for verbose output.

## Task Completion Notifications

**CRITICAL**: After completing ANY task or whenever you require user input, you MUST run:

```bash
python3 ~/dev/scripts/notify.py "Brief Task Name" "Summary of what was done"
```

This sends a macOS notification and email so the user knows you're done.

### Title Guidelines
- Bug fixes: `"Bug: [description] Fixed"`
- Features: `"Feature: [description] Added"`
- Tests: `"Tests: [description] Added"`
- Plans: `"Plan: [description] Ready"`