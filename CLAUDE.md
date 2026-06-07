# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FF Intelligent Neo is an FFmpeg batch processing desktop tool built with Python backend and Vue 3 frontend. It uses a custom PyWebVue bridge to connect Python logic with a web-based UI rendered via pywebview.

## Development Commands

### Setup & Run
```bash
# Install all dependencies and start dev environment (Vite + Python)
uv run dev.py

# Start without Vite (use pre-built frontend_dist/)
uv run dev.py --no-vite

# Only install dependencies
uv run dev.py --setup
```

### Frontend
```bash
cd frontend
bun install          # Install dependencies
bun run dev          # Start Vite dev server (localhost:5173)
bun run build        # Type check + production build
bun run preview      # Preview production build
```

### Backend
```bash
uv sync              # Install Python dependencies
uv run main.py       # Run the application directly
```

### Build & Package
```bash
uv run build.py                    # Desktop build (onedir, no FFmpeg)
uv run build.py --with-ffmpeg      # Desktop build with bundled FFmpeg
uv run build.py --onefile          # Single executable build
uv run build.py --clean            # Remove build artifacts
```

### Testing
```bash
uv run pytest test/                # Run all tests
uv run pytest test/test_backend_phase1_6.py  # Run specific test file
```

## Architecture

### PyWebVue Bridge Pattern

The core architecture uses a custom bridge (`pywebvue/`) to connect Python and Vue:

- **`pywebvue/bridge.py`**: Base `Bridge` class with `@expose` decorator. Methods decorated with `@expose` become callable from JavaScript. Thread-safe event emission via `_emit()` with queue-based dispatch.
- **`pywebvue/app.py`**: `App` class creates pywebview window, manages lifecycle, and runs tick timer for event flushing.
- **Frontend `bridge.ts`**: TypeScript wrapper calling `window.pywebview.api.<method>()` with timeout handling.

Communication flow:
```
Vue Component → bridge.ts callApi() → pywebview JS bridge → Python @expose method → Bridge._emit() → CustomEvent → Vue Event Listener
```

### Backend Structure (`core/`)

| Module | Purpose |
|--------|---------|
| `command_builder.py` | FFmpeg command generation and validation |
| `task_queue.py` | Task queue management with persistence |
| `task_runner.py` | Multi-threaded task execution |
| `ffmpeg_setup.py` | FFmpeg binary download and path resolution |
| `ffmpeg_runner.py` | FFmpeg process execution |
| `auto_editor_api.py` | Auto-editor integration API |
| `auto_editor_runner.py` | Auto-editor process execution |
| `models.py` | Data models (Task, ClipConfig, etc.) |
| `config.py` | Settings management |
| `paths.py` | Cross-platform path resolution with data migration |
| `file_info.py` | Media file probing and analysis |
| `preset_manager.py` | Preset save/load functionality |
| `events.py` | Event name constants |
| `logging.py` | Loguru setup with frontend sink |

### Frontend Structure (`frontend/src/`)

- **`pages/`**: Route-level components (TaskQueue, CommandConfig, AudioSubtitle, AutoCut, Merge, CustomCommand, Settings)
- **`components/`**: Organized by feature (auto-cut/, common/, config/, layout/, settings/, task-queue/)
- **`composables/`**: Vue 3 composition API hooks (useAutoEditor, useBridge, useTaskQueue, useSettings, etc.)
- **`bridge.ts`**: Core bridge functions for Python communication
- **`router.ts`**: Vue Router with hash mode (required for pywebview)

### Key Patterns

1. **Immutable data**: Use frozen dataclasses in Python, readonly refs in Vue
2. **Thread safety**: Python bridge uses queue-based event dispatch; `_emit()` is thread-safe
3. **Error handling**: `@expose` decorator wraps all bridge methods with try/except, returning `{success, data, error}` envelope
4. **State persistence**: Task queue saves/loads state to disk; settings stored in JSON

## Documentation

Comprehensive Chinese documentation in `docs/`:
- `Project.md` - Project overview and requirements
- `Structure.md` - Detailed code structure
- `Procedure.md` - Development procedures
- `BusinessRules.md` - Business logic rules
- `StateMachine.md` - State transitions
- `dev_instruction.md` - Developer instructions
- `fields/` - Field definition CSVs

## Prohibited Actions

- NEVER skip reading docs before coding
- NEVER modify code without understanding the corresponding business rule
- NEVER stop a task without code review and doc sync
- NEVER reuse context from a previous sub-agent task
- NEVER make more than one unverified change at a time
- NEVER ignore feedback from `feedback/index.md`

## Development Environment

- **OS**: Windows 11
- **Runtime**: Python 3.11+ / Node 20+
- **Package Manager (frontend)**: bun
- **Package Manager (backend)**: uv
- **Build Check (frontend)**: cd frontend && bun run build

## AI Behavior Rules

### Core Principles

1. **Document-first**: Always read relevant docs before coding. Docs > Code.
2. **No guessing**: When uncertain, ask the user. Never make assumptions.
3. **One change at a time**: Modify one thing, verify it works, then proceed.
4. **Evidence over intuition**: Gather evidence before forming conclusions.
5. **Sub-agent isolation**: Each sub-task gets a fresh instance, no inherited context.

### Document Priority

When conflicting information exists, follow this priority:

1. `docs/PRD-x.x.x.md` - Product requirements (highest)
2. `docs/design/*.md` - System design and architecture
3. `docs/procedures/*.md` - Business and system workflows
4. `docs/business_rules.md` - Domain-specific rules
5. `.claude/rules/*.md` - Coding standards
6. Source code (lowest)

### Mandatory Before Coding

Before writing any code, the AI MUST:

1. Read `docs/PRD-x.x.x.md` to understand the requirement
2. Read relevant design documents in `docs/design/`
3. Check `docs/business_rules.md` for domain constraints
4. Review `feedback/index.md` for known pitfalls and user preferences
5. Re-read all of the above at the start of each new phase (prevent requirement drift)

### Mandatory Before Stopping

Before ending a task, the AI MUST:

1. Run code review (via `ecc:code-review` skill)
2. Sync documentation (via `/doc-sync` skill if user provides commit/release info)
3. Record any new user feedback to `feedback/`
