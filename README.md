# FF Intelligent Neo

FFmpeg batch processing desktop tool built with Python + Vue.js.

## Features

- **Batch Processing** - Add multiple files to the task queue, start all at once, pause/resume/stop any task
- **Real-time Command Preview** - See the generated FFmpeg command update live as you adjust parameters
- **20+ Encoders** - CPU (libx264, libx265, libsvtav1, AV1) and GPU (NVIDIA NVENC, AMD AMF, Intel QSV) with auto hardware detection
- **Video Filters** - Crop, rotate, watermark (drag & drop), audio normalization (EBU R128), aspect ratio conversion (H2V/V2H with 6 modes)
- **Video Clipping** - Extract mode (trim intro/outro) and cut mode (precise time range), supports `-c copy` lossless
- **Audio & Subtitle Mixing** - Replace/add external audio tracks and subtitle files
- **Multi-video Merging** - Concat (TS/demuxer) and filter_complex modes with intro/outro appending, drag-to-reorder
- **Custom Commands** - Write raw FFmpeg arguments with real-time preview
- **Preset System** - Save and load encoder/filter configurations
- **Dark/Light Theme** - Follows system preference, manual toggle, DaisyUI themed
- **Auto Cut (v2.2.0)** - Silence/motion-based auto-editing via auto-editor, curated encoder lists (Recommended / GPU Hardware / Custom)
- **Chinese/English UI** - Full i18n support via vue-i18n
- **Cross-platform** - Windows, macOS, Linux

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, PyWebView |
| Frontend | Vue 3, TypeScript, TailwindCSS, DaisyUI |
| Build | PyInstaller (onedir / onefile) |
| Package | uv (backend), bun (frontend) |

## Project Structure

```
ff-intelligent-neo/
  main.py              # Entry point, Bridge API, event system
  core/                # Python backend modules
    auto_editor_runner.py  # auto-editor: command builder, progress parser (v2.2.0)
    auto_editor_api.py     # auto-editor: path mgmt, task ops, preview (v2.2.0)
    command_builder.py # FFmpeg command generation
    task_runner.py     # Task execution & process control
    task_queue.py      # Task persistence
    models.py          # Data models (TaskConfig, FilterConfig, etc.)
    paths.py           # Centralized path management
    config.py          # Settings persistence
    preset_manager.py  # Preset CRUD
    ffmpeg_setup.py    # FFmpeg detection & download
    file_info.py       # ffprobe file probing
    logging.py         # loguru configuration
  frontend/            # Vue.js SPA
    src/
      components/      # UI components
        auto-cut/      # Auto Cut (BasicTab, AdvancedTab) (v2.2.0)
        config/        # Command config forms (Transcode, Filters, Clip, Merge, Encoder)
        task-queue/    # Queue components (TaskList, TaskRow, ProgressBar)
        settings/      # Settings panels
        common/        # Shared components (ComboInput, FileDropInput, SplitDropZone)
        layout/        # AppNavbar
      composables/     # Reactive logic (useAutoEditor, useCommandPreview, useTaskQueue, ...)
      pages/           # Route pages (TaskQueuePage, CommandConfigPage, MergePage, etc.)
      i18n/            # zh-CN / en-US language packs
      types/           # TypeScript type definitions
      data/            # Encoder registry
  docs/                # Design documents (StateMachine, BusinessRules, Procedure, Structure)
  presets/             # Default preset JSON files
```

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [bun](https://bun.sh/)
- FFmpeg (auto-detected or downloaded via built-in downloader on Windows)
- auto-editor v30.1.x (optional, for Auto Cut feature; downloadable from GitHub Releases)

### Development

```bash
# Install backend dependencies
uv sync

# Install frontend dependencies
cd frontend && bun install && cd ..

# Run in development mode
uv run dev.py
```

### Build

```bash
# Build frontend
cd frontend && bun run build && cd ..

# Build distributable (PyInstaller)
uv run build.py                  # default: onedir with bundled FFmpeg
uv run build.py --onefile        # single executable
uv run build.py --no-ffmpeg      # without bundled FFmpeg
```

## Pages

| Route | Description |
|-------|-------------|
| `/` (Task Queue) | Add files, manage tasks, view progress and logs |
| `/config` (Command Config) | Configure transcode, filters, clip parameters with live preview |
| `/audio-subtitle` (A/V Mix) | Mix external audio/subtitle tracks into video |
| `/merge` (Merge) | Multi-video merging with intro/outro support |
| `/custom-command` | Write raw FFmpeg arguments |
| `/auto-cut` (v2.2.0) | Auto-Editor silence/motion detection cutting with curated encoder lists |
| `/settings` | FFmpeg/auto-editor setup, output folder, theme, language |

## License

AGPL-3.0 (see [LICENSE](LICENSE))

## Acknowledgments

- **[FFmpeg](https://github.com/FFmpeg/FFmpeg)**: Mirror of https://git.ffmpeg.org/ffmpeg.git
- **[auto-editor](https://github.com/WyattBlue/auto-editor)**: Effort free video editing!
- **[FFmpegFreeUI](https://github.com/Lake1059/FFmpegFreeUI)**: 3FUI 是 ffmpeg 在 Windows 上的轻度专业交互外壳，收录大量参数，界面美观，交互友好。此项目面向国内使用环境，让普通人也能够轻松压制视频和转换格式。
- **[VidExtConcat](https://github.com/wish2333/VidExtConcat)**: This project aims to develop a user-friendly graphical interface application for the quick cutting and merging of video intros and outros.
