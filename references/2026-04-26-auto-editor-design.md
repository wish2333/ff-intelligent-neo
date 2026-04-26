# Auto-Editor Integration Design

**Date:** 2026-04-26  
**Status:** Approved  
**Branch:** dev-2.2.0

---

目前版本基于https://github.com/WyattBlue/auto-editor/releases/tag/30.1.4此版本的auto-editor进行

## 1. Architecture Overview

The design follows the exact same architecture as the existing FFmpeg integration:

```
Frontend (Vue 3)                    Backend (Python)                    Task Queue
─────────                            ────────────                      ───────────
AutoCutPage.vue                       FFmpegApi (main.py)
  ├─ BasicTab.vue                    ├─ @expose run_auto_editor()
  ├─ AdvancedTab.vue                 ├─ @expose get_auto_editor_version()
  ├─ useAutoEditor.ts               └─ @expose set_auto_editor_path()
  └─ useCommandPreview (shared)          │
                                           ▼
                                  auto_editor_runner.py
                                           ├─ build_command(params)
                                           ├─ run_auto_editor(path, params)
                                           └─ parse_output(proc)
                                           │
                                           ▼
                                  task_runner.py (shared)
                                           └─ TaskQueue → emits events
                                                  │
                                                  ▼
                                          Frontend task-queue components
                                          (shared progress/log display)
```

**Key decisions:**
- New page `AutoCutPage.vue` with `BasicTab.vue` + `AdvancedTab.vue`
- New composable `useAutoEditor.ts` for state management
- New backend module `auto_editor_runner.py` - mirror of `ffmpeg_runner.py`
- Extend `main.py` FFmpegApi with auto-editor methods
- Settings page gets new "Auto-Editor Path" field (mirroring FFmpeg setup)
- Auto-editor jobs flow through the existing TaskQueue system

---

## 2. Frontend Page Design

**New page:** `frontend/src/pages/AutoCutPage.vue`

**Page structure:**
```
AutoCutPage.vue
├── FileDropInput (drag-drop video/audio files)
├── BasicTab.vue
│   ├── Edit method selector (audio/motion/subtitle)
│   ├── Silence threshold slider (0.01-0.20)
│   ├── When-silent action (cut / speed:X / volume:X / nil)
│   ├── When-normal action (nil / speed:X / volume:X)
│   ├── Margin input (default 0.2s)
│   └── Smooth input (mincut/minclip)
├── AdvancedTab.vue
│   ├── Actions section
│   │   ├── Cut-out ranges (--cut-out)
│   │   ├── Add-in ranges (--add-in)
│   │   └── Set-action custom ranges
│   ├── Timeline section
│   │   ├── Frame rate override
│   │   ├── Sample rate override
│   │   └── Resolution override
│   ├── Container section
│   │   ├── Toggle: -vn / -an / -sn / -dn
│   │   ├── Faststart toggle
│   │   └── Fragmented toggle
│   ├── Video rendering
│   │   ├── Codec select (h264/hevc/vp9/av1)
│   │   ├── Video bitrate input
│   │   └── CRF input
│   ├── Audio rendering
│   │   ├── Codec select (aac/fdk_aac/aac_at)
│   │   ├── Audio bitrate input
│   │   ├── Audio layout
│   │   └── Audio normalize (peak/ebu)
│   └── Misc: --no-cache, --open, output format
├── CommandPreview.vue (reused from config/)
└── Action buttons (Add to Queue / Run Now)
```

**Composables:**
- `useAutoEditor.ts` - mirrors `useCommandPreview` pattern:
  - `editMethod`, `threshold`, `whenSilentAction`, `whenNormalAction`
  - `advancedOptions` (reactive object for all advanced params)
  - `commandPreview` (computed, builds preview via backend call)
  - `runAutoEditor()` - calls backend to queue the job

**Router:** Add `/auto-cut` route in `router.ts`, add nav item in `AppNavbar.vue`.

---

## 3. Backend Design

**New file:** `core/auto_editor_runner.py`

Mirrors `ffmpeg_runner.py` pattern:
```python
class AutoEditorRunner:
    def __init__(self, auto_editor_path: str):
        self.path = auto_editor_path
    
    def build_command(self, input_file: str, params: dict) -> list[str]:
        # Build CLI args from params dict
        # Maps UI state → auto-editor CLI flags
        # e.g., params['edit_method']='audio' → ['--edit', 'audio:0.04']
        # e.g., params['when_silent']='cut' → ['--when-silent', 'cut']
        
    def run_auto_editor(self, input_file: str, params: dict, task_id: str):
        # subprocess.Popen()
        # Parse output differently from ffmpeg
        # Emit task_progress events for queue integration
```

**Command builder:** `core/auto_editor_command_builder.py`

Similar to `command_builder.py` but for auto-editor:
- Maps UI params to CLI args
- Handles Basic vs Advanced tier options
- Validates parameter combinations

**Extend `main.py` FFmpegApi:**
```python
class FFmpegApi(Bridge):
    # ... existing methods ...
    
    @expose
    def set_auto_editor_path(self, path: str) -> dict:
        # Save to settings, validate binary works
        
    @expose  
    def get_auto_editor_version(self) -> str:
        # Run `auto-editor --version` to verify
        
    @expose
    def add_auto_editor_task(self, input_file: str, params: dict) -> str:
        # Validate, build command, add to task_queue
        # Returns task_id
```

**Output parsing:** auto-editor outputs progress differently than ffmpeg. Need to parse its stdout/stderr to emit `task_progress` events. Key difference: auto-editor shows frame counts and percentages, not the same time/speed/fps format.

**Settings integration:** Add `auto_editor_path` to the settings model (mirroring `ffmpeg_path`).

---

## 4. Data Flow

**Complete flow for running an auto-editor job:**

```
1. User drops file in AutoCutPage
   └─ FileDropInput validates file type (video/audio)
   
2. User configures options (Basic tab or Advanced tab)
   └─ UI state updates reactive refs in useAutoEditor.ts
   
3. User clicks "Add to Queue"
   └─ useAutoEditor.runAutoEditor()
       └─ call('add_auto_editor_task', inputFile, params)
       
4. Backend: FFmpegApi.add_auto_editor_task()
   └─ auto_editor_command_builder.build_command(input_file, params)
       └─ Returns [auto-editor, input, --edit, audio:0.04, --when-silent, cut, ...]
       
5. Task created in task_queue.py
   └─ task_runner.py picks up task from thread pool
       └─ auto_editor_runner.run_auto_editor(path, params, task_id)
           └─ subprocess.Popen(command)
               ├─ Parse stdout/stderr → emit task_progress
               └─ On complete → emit task_complete
               
6. Frontend receives events via useTaskProgress
   └─ TaskProgressBar / TaskLogPanel update (reused components)
   
7. Output file appears in configured output folder
   └─ Same behavior as FFmpeg tasks
```

**Command preview flow** (realtime, no task created):
```
useAutoEditor.ts → call('preview_auto_editor_command', params)
→ auto_editor_command_builder.build_command() → returns command string
→ CommandPreview.vue displays it (reused component)
```

---

## 5. Integration Points

### Settings Page
- Add "Auto-Editor Path" input field (same pattern as FFmpeg Setup)
- Validate binary on path change
- Store in settings model

### AppNavbar
- Add nav item for Auto Cut page between existing items
- Use appropriate icon (e.g., scissors/cut symbol)

### Router (`frontend/src/router.ts`)
- Add route: `{ path: '/auto-cut', component: () => import('./pages/AutoCutPage.vue') }`

### TaskQueue System
- Reuse existing `task_runner.py` thread pool
- Reuse `TaskQueue` state management
- Reuse `TaskProgressBar`, `TaskLogPanel` components
- New task type: `{ type: 'auto_editor', input_file, params }`

---

## 6. Dependencies

- auto-editor binary (user-provided, configured in Settings)
  - or design a new downloader（适应多平台）：下载二进制文件来源：https://github.com/WyattBlue/auto-editor/releases/tag/30.1.4

- No new npm packages required
- No new Python packages required (auto-editor is a separate binary)
- Reuses: pywebvue, task_queue, composables pattern

---

## 7. Out of Scope (Future Enhancements)

- URL download integration (yt-dlp)
- Timeline visualization of cuts
- Preview of edited output before saving
- Batch processing UI (multiple files with same settings)
- Auto-editor Python API integration (if available in future)
