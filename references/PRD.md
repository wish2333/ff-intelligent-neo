# FF Intelligent MVP - PRD

## Overview

A desktop FFmpeg batch processing tool built on the pywebvue framework. Users drag-and-drop audio/video files, select editable command presets, and run multi-threaded batch FFmpeg conversions with real-time progress display.

## Target Users

- Content creators who need to batch-convert media files
- Users who frequently transcode between formats
- Anyone needing quick batch audio/video operations

## Core Features (MVP)

### 1. File Management
- Drag-and-drop media files from OS file explorer
- Display file metadata: name, duration, codec, resolution, size
- Multi-select files (ctrl+click, shift+click)
- Clear all / remove selected

### 2. Preset System
- 8 built-in presets (H264 MP4, H265 MP4, Audio to MP3, etc.)
- Command template preview
- Create / edit / delete custom presets
- Presets persist across restarts (user presets in APPDATA)

### 3. Batch Processing
- Select preset + output directory + thread count (1-4)
- Multi-threaded FFmpeg execution via ThreadPoolExecutor
- Real-time per-file and overall progress bars
- Live FFmpeg stderr log viewer
- Cancel batch mid-execution

### 4. FFmpeg Setup
- Uses `static-ffmpeg` package (bundled binaries, no external install)
- First-run auto-download of ffmpeg/ffprobe binaries
- Status indicator showing ffmpeg ready/not ready

## Technical Stack

- **Backend**: Python 3.10+ with pywebview + static-ffmpeg
- **Frontend**: Vue 3 + TypeScript + Vite + Tailwind CSS v3 + DaisyUI v4
- **Bridge**: pywebvue built-in Bridge system
- **Build**: PyInstaller (onedir / onefile)

## UI Layout

```
+------------------------------------------+
|  Navbar (title, ffmpeg status, theme)    |
+------------------------------------------+
|  [Add Files] [Clear] [Select Output Dir] |
+------------------------------------------+
|  Preset: [dropdown v]  [Edit] [New]      |
|  Command: -i {input} -c:v ...            |
+------------------------------------------+
|  File Table (sortable, multi-select)     |
|  [x] name.mp4   00:05:30  H264  1080p    |
|  [x] name2.mp4  00:02:15  H265  720p     |
+------------------------------------------+
|  [Start Batch] [Cancel]  Workers: [1-4]  |
|  Overall: [==========        ] 45%       |
|  File 1:  [=============     ] 80%       |
|  File 2:  [=====              ] 30%       |
+------------------------------------------+
|  FFmpeg Log (scrollable, monospace)      |
|  frame= 120 fps=30 ...                   |
+------------------------------------------+
```

## Event Protocol (Python -> Frontend)

| Event | Payload | Description |
|---|---|---|
| `task_start` | `{file_index, file_name}` | Before ffmpeg starts on a file |
| `task_progress` | `{file_index, file_name, percent, time_str}` | Progress update (throttled 500ms) |
| `task_complete` | `{file_index, file_name, output_path}` | File conversion succeeded |
| `task_error` | `{file_index, file_name, error}` | File conversion failed |
| `batch_progress` | `{total, completed, overall_percent}` | After each file completes |
| `batch_complete` | `{total, completed, errors}` | All files done or cancelled |

## Non-Goals

- Video preview / playback
- Stream mapping editor
- GPU encoding options (future)
- CLI interface
- Plugin system
