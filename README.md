# FF Intelligent Neo

A desktop FFmpeg batch processing tool with a modern GUI. Add media files, configure transcode parameters and filters, then process them in a controllable task queue with real-time progress tracking.

## Features

- **Batch Processing** - Add multiple files and process them in a managed task queue
- **Individual Task Control** - Start, pause, resume, stop, and retry each task independently
- **Batch Operations** - Pause all, resume all, or stop all tasks at once
- **Rich FFmpeg Configuration** - Video/audio codecs, bitrate, resolution, framerate, output format
- **Filter Chains** - Rotate, crop, scale, watermark overlay, volume adjustment, speed change with automatic priority ordering
- **Preset Management** - Built-in and user-defined presets for common configurations
- **Real-time Progress** - Live progress bars with speed, FPS, and estimated remaining time
- **Command Preview** - See the generated FFmpeg command before execution with validation
- **Persistent State** - Task queue and settings survive application restarts
- **Cross-platform** - Windows, macOS, and Linux support

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop Container | [pywebview](https://pywebview.flowrl.com/) |
| Backend | Python 3.11+ |
| Frontend | [Vue 3](https://vuejs.org/) + TypeScript |
| UI Framework | [DaisyUI v5](https://daisyui.com/) + [Tailwind CSS v4](https://tailwindcss.com/) |
| Build | [Vite 6](https://vite.dev/) (frontend) + [PyInstaller](https://pyinstaller.org/) (packaging) |
| Package Manager | [uv](https://github.com/astral-sh/uv) (Python), [bun](https://bun.sh/) (Node) |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- [bun](https://bun.sh/)
- FFmpeg (auto-downloaded on first run, or set custom path in Settings)

### Development

```bash
# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend && bun install && cd ..

# Start development mode (with frontend hot reload)
uv run dev.py
```

### Build

```bash
# Build distributable executable
uv run build.py
```

The output is in `dist/`.

## Project Structure

```
ff-intelligent-neo/
├── main.py                  # Application entry point + Bridge API
├── build.py                 # PyInstaller build script
├── app.spec                 # PyInstaller configuration
├── core/                    # Python backend modules
│   ├── models.py            # Data models (Task, Config, Progress, etc.)
│   ├── task_queue.py        # Thread-safe task queue with persistence
│   ├── task_runner.py       # Task execution engine (ThreadPool)
│   ├── ffmpeg_runner.py     # FFmpeg process management
│   ├── command_builder.py   # FFmpeg command construction
│   ├── process_control.py   # Cross-platform process tree termination
│   ├── config.py            # Settings persistence
│   ├── preset_manager.py    # Preset management
│   ├── ffmpeg_setup.py      # FFmpeg binary setup
│   ├── file_info.py         # Media file probing (ffprobe)
│   ├── app_info.py          # Application metadata
│   └── logging.py           # Logging configuration
├── pywebvue/                # PyWebView-Vue bridge layer
│   ├── app.py               # Window management + event system
│   └── bridge.py            # @expose decorator + Bridge base class
├── frontend/                # Vue 3 + TypeScript frontend
│   └── src/
│       ├── pages/           # Page components (TaskQueue, CommandConfig, Settings)
│       ├── components/      # Reusable UI components
│       ├── composables/     # Vue composables (business logic)
│       ├── types/           # TypeScript type definitions
│       └── utils/           # Utility functions
├── presets/                 # Built-in preset configurations
└── docs/                    # Project documentation
```

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Task Queue | `/task-queue` | Add files, manage tasks, monitor progress |
| Command Config | `/command-config` | Configure transcode parameters, filters, and presets |
| Settings | `/settings` | FFmpeg path, output directory, worker count |

## Documentation

Detailed documentation is available in `docs/`:

- [Project Overview](docs/Project.md) - Project background, tech stack, development setup
- [Architecture](docs/Structure.md) - System architecture and module relationships
- [Business Flows](docs/Procedure.md) - Process flow diagrams
- [Business Rules](docs/BusinessRules.md) - State machine rules and validation logic
- [State Machine](docs/StateMachine.md) - Task lifecycle state diagram
- [Field Reference](docs/fields/) - Data model field inventory (CSV)

## License

MIT
