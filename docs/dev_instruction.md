# FF Intelligent Neo - Development Guide

> 本文档基于项目代码库全面审查生成，涵盖开发习惯、可复用模块、架构约定和开发流程规范。

---

## 1. Tech Stack Overview

| Layer | Technology | Version |
|-------|-----------|---------|
| Desktop Shell | pywebview | >=6.0 |
| Python Backend | Python + pywebvue bridge | 3.11+ |
| Frontend | Vue 3 (Composition API) | ^3.5.0 |
| UI Framework | Tailwind CSS v4 + DaisyUI v5 | ^4.1.0 / ^5.0.0 |
| Routing | Vue Router (hash mode) | 4 |
| i18n | vue-i18n | ^11.4.0 |
| TypeScript | Strict mode | ~5.7.0 |
| Build (frontend) | Vite + @tailwindcss/vite | ^6.0.0 |
| Build (backend) | uv + PyInstaller | >=6.19.0 |
| Package Manager (frontend) | bun | - |
| Package Manager (backend) | uv | - |
| Logging | loguru | >=0.7 |

---

## 2. Project Structure

```
ff-intelligent-neo/
  main.py                  # Entry point + FFmpegApi(Bridge) class
  dev.py                   # One-click dev startup (Vite + pywebview)
  build.py                 # PyInstaller build orchestrator
  app.spec                 # PyInstaller spec

  core/                    # Python backend (flat module architecture)
    models.py              # All data models (dataclass, frozen/immutable)
    config.py              # Settings load/save (atomic write)
    paths.py               # Centralized path resolution + migration
    command_builder.py     # FFmpeg command construction (plugin registry)
    task_queue.py          # Thread-safe task persistence
    task_runner.py         # ThreadPoolExecutor task execution
    ffmpeg_runner.py       # Single-file FFmpeg process wrapper
    ffmpeg_setup.py        # 6-tier FFmpeg binary discovery
    auto_editor_api.py     # Auto-editor API delegation
    auto_editor_runner.py  # Auto-editor command builder + progress parser
    process_control.py     # Cross-platform suspend/resume/kill
    logging.py             # Loguru configuration
    file_info.py           # ffprobe metadata extraction
    preset_manager.py      # Preset CRUD
    app_info.py            # App metadata + version detection
    batch_runner.py        # Legacy batch runner

  pywebvue/                # Custom Python-Vue bridge library
    __init__.py            # Package init
    bridge.py              # Bridge base + @expose decorator
    app.py                 # Window creation + lifecycle

  frontend/src/
    bridge.ts              # pywebview API communication layer
    router.ts              # Hash-based routing
    style.css              # Tailwind + DaisyUI theme config
    main.ts                # Vue app bootstrap
    components/            # UI components (by domain)
    composables/           # Reactive logic (use*.ts)
    pages/                 # Route pages (flat, lazy-loaded)
    types/                 # TypeScript interfaces (DTO suffix)
    data/                  # Static registries (encoders, file formats)
    utils/                 # Utility functions
    i18n/locales/          # zh-CN.ts, en.ts

  docs/                    # Design documentation
  docs/fields/             # CSV field definitions (source of truth)
  references/              # PRDs, design docs
  presets/                 # Default preset JSON files
  scripts/                 # Build/verification scripts
  test/                    # Backend tests
  data/                    # Runtime data (gitignored)
```

**Convention**: Backend uses flat module architecture -- no subpackages in `core/`. Each module is a single `.py` file with single responsibility.

---

## 3. Communication Architecture: PyWebVue Bridge

本项目是桌面应用，使用 pywebview 嵌入 Chromium 浏览器。前后端通过自定义 `pywebvue` 桥通信，**没有 HTTP/REST，没有 axios/fetch**。

### 3.1 Backend: Adding API Endpoints

所有 API 方法位于 `main.py` 的 `FFmpegApi(Bridge)` 类中：

```python
@expose
def my_new_endpoint(self, param: str) -> dict:
    try:
        result = do_something(param)
        return {"success": True, "data": result}
    except ValueError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("my_new_endpoint failed: {}", exc)
        return {"success": False, "error": str(exc)}
```

**Rules**:
- Must decorate with `@expose`
- Must return `{"success": True/False, "data": ..., "error": ...}` format
- Expected errors: catch `ValueError` specifically, return user-friendly message
- Unexpected errors: catch `Exception` with `logger.exception()`
- The `@expose` decorator itself has a global safety net (catches unhandled exceptions)

### 3.2 Lazy Initialization Pattern

Heavyweight dependencies use `@property` with lazy init to avoid startup cost:

```python
@property
def _queue(self):
    from core.task_queue import TaskQueue
    if not hasattr(self, "_queue_inst"):
        self._queue_inst = TaskQueue()
        self._queue_inst.load_state()
        self._queue_inst.set_on_change(self._on_queue_change)
    return self._queue_inst
```

### 3.3 Event System (Backend -> Frontend)

Push events from Python to Vue via `self._emit(event_name, data_dict)`:

```python
self._emit("queue_changed", {"pending": 3, "running": 1, ...})
self._emit("task_state_changed", {"task_id": "...", "old_state": "pending", "new_state": "running"})
self._emit("task_progress", {"task_id": "...", "progress": {...}})
self._emit("task_log", {"task_id": "...", "line": "..."})
```

### 3.4 Frontend: Calling Backend

```typescript
// bridge.ts - the only way to communicate with Python backend
import { call, waitForPyWebView } from "../bridge"

// In onMounted - always wait for pywebview ready
await waitForPyWebView()

// Call backend method (generic typed)
const res = await call<TaskDTO[]>("get_tasks")
if (res.success) {
  tasks.value = res.data!
}
```

### 3.5 Frontend: Listening to Events

```typescript
// In composable - auto-cleanup on unmount
import { useBridge } from "../composables/useBridge"
const { on } = useBridge()

on("queue_changed", (data) => { ... })

// In page - manual cleanup
import { onEvent } from "../bridge"
const cleanup = onEvent<QueueSummary>("queue_changed", (data) => { ... })
onUnmounted(cleanup)
```

### 3.6 Task Routing Pattern

When adding a new task type (like auto-editor), route in the dispatch methods:

```python
# In start_task / stop_task / retry_task:
task = self._queue.get_task(task_id)
if getattr(task, 'task_type', '') == 'my_new_type':
    return self._my_new_type_api.start_task(task_id)
# Default FFmpeg handling
ok = self._runner.start_task(task_id, config=config)
```

### 3.7 Delegation Pattern for New Integrations

pywebvue supports only one Bridge subclass. For new integrations, create a plain class and delegate from `FFmpegApi`:

```python
# core/my_new_api.py (plain class, NOT Bridge subclass)
class MyNewApi:
    def __init__(self, emit, queue, runner):
        self._emit = emit
        self._queue = queue
        self._runner = runner

    def do_something(self) -> dict:
        # ... implementation ...
        return {"success": True, "data": ...}

# In main.py FFmpegApi class:
@property
def _my_new(self):
    if not hasattr(self, "_my_new_inst"):
        from core.my_new_api import MyNewApi
        self._my_new_inst = MyNewApi(emit=self._emit, queue=self._queue, runner=self._runner)
    return self._my_new_inst

@expose
def my_new_method(self) -> dict:
    return self._my_new.do_something()
```

---

## 4. Reusable Frontend Components

### 4.1 Common Components

#### ComboInput.vue
带下拉建议的文本输入框。
- **Props**: `modelValue: string`, `suggestions: string[]`, `placeholder?`, `disabled?`
- **Emits**: `update:modelValue`
- **Usage**: 编码器预设、像素格式等需要建议但不限制输入的场景

```vue
<ComboInput v-model="config.preset" :suggestions="presetOptions" placeholder="选择预设" />
```

#### FileDropInput.vue
拖放 + 点击选择文件的输入组件。
- **Props**: `modelValue: string`, `accept?: string`, `placeholder?`, `fullscreenDrop?: boolean`, `multiple?: boolean`
- **Emits**: `update:modelValue`
- **Usage**: 单文件选择、多文件选择、拖放到页面任意位置

```vue
<!-- 单文件 -->
<FileDropInput v-model="filePath" accept=".mp4,.mkv" />

<!-- 全屏拖放 -->
<FileDropInput v-model="filePath" fullscreen-drop :multiple="true" />
```

#### SplitDropZone.vue
分屏双文件拖放区域（左右各一个 drop zone）。
- **Props**: `leftLabel?`, `rightLabel?`, `leftAccept?`, `rightAccept?`
- **Emits**: `drop-left: [path]`, `drop-right: [path]`
- **Usage**: 片头/片尾视频选择

### 4.2 Config Components

#### EncoderSelect.vue
分组编码器选择器（按 P0/P1/P2 优先级分组）。
- **Props**: `modelValue: string`, `category: "video" | "audio"`, `supportedEncoders?: string[]`, `platform?: string`
- **Emits**: `update:modelValue`, `qualityChange: [config | null]`
- **Features**: 自动隐藏不支持的平台编码器、支持自定义编码器名称

#### CommandPreview.vue
只读命令预览 + 验证结果显示。
- **Props**: `commandText`, `errors: ValidationItem[]`, `warnings: ValidationItem[]`, `validating: boolean`, `type?: "ffmpeg" | "auto-editor"`
- **Features**: 一键复制、错误/警告分行显示、始终占位防止布局跳动

### 4.3 Task Queue Components

| Component | Purpose |
|-----------|---------|
| TaskList.vue | 任务列表容器 |
| TaskRow.vue | 单行任务（状态+操作按钮） |
| TaskProgressBar.vue | 进度条（百分比/时间/速度/fps） |
| TaskLogPanel.vue | 可折叠日志面板 |
| TaskToolbar.vue | 添加/删除/清空工具栏 |
| BatchControlBar.vue | 全部开始/暂停/停止控制栏 |
| QueueSummary.vue | 状态统计徽章栏 |

### 4.4 Settings Components

| Component | Purpose |
|-----------|---------|
| FFmpegSetup.vue | FFmpeg 版本检测/切换/下载 |
| AutoEditorSetup.vue | Auto-editor 路径配置 |
| ThreadCountInput.vue | 并发数快速选择（1-4） |
| OutputFolderInput.vue | 输出目录选择 |
| AppAbout.vue | 应用信息展示 |

### 4.5 Layout Components

#### AppNavbar.vue
顶部导航栏，包含：
- 路由链接到所有页面
- 主题切换（light/dark/auto）
- 语言切换（zh-CN/en）
- FFmpeg 状态徽章
- Auto-editor 状态徽章

---

## 5. Reusable Composables

### 5.1 Module-Level Singleton (跨组件共享状态)

| Composable | Purpose | Key API |
|-----------|---------|---------|
| useGlobalConfig | 全局命令配置（transcode/filters/clip/merge/avsmix） | `configRef`, `toTaskConfig()`, `resetAll()` |
| useFileFormats | 文件格式注册表（懒加载） | `fileFormats` | 附带 `toWebViewFileTypes()` 模块级导出 |

**Pattern**: 状态定义在模块作用域（函数外部），所有导入者共享同一状态。

```typescript
// useFileFormats.ts
// toWebViewFileTypes() 是模块级独立导出，不从 useFileFormats() 返回：
import { fileFormats, toWebViewFileTypes } from "../composables/useFileFormats"
```
```typescript
// useGlobalConfig.ts
const transcode = reactive<TranscodeConfigDTO>({ ... })  // module scope
export function useGlobalConfig() {
  return { transcode, ... }
}
```

### 5.2 Per-Instance Composables (每次调用创建新实例)

| Composable | Purpose | Key State | Key API |
|-----------|---------|-----------|---------|
| useBridge | 事件监听生命周期管理 | - | `on(event, cb)`, `cleanup()` |
| useSettings | 应用设置 + FFmpeg 版本管理 | `settings`, `ffmpegVersions`, `ffmpegStatus` | `fetchSettings()`, `saveSettings()`, `switchFfmpeg()` |
| useTaskQueue | 任务列表 + 选择 + 队列统计 | `tasks`, `selectedIds`, `summary` | `fetchTasks()`, `addTasks()`, `removeTasks()` |
| useTaskControl | 任务生命周期操作 | - | `startTask()`, `stopTask()`, `pauseTask()`, `retryTask()` |
| useTaskProgress | 实时进度 + 日志跟踪 | `progressMap`, `logsMap` | `getProgress(id)`, `getLogs(id)` |
| useCommandPreview | 防抖命令预览 + 验证 | `commandText`, `errors`, `warnings` | `updatePreview()` |
| useAutoEditor | Auto-editor 参数管理 | 13+ reactive refs | `fetchStatus()`, `updatePreview()`, `addToQueue()` |
| usePresets | 预设 CRUD | `presets` | `fetchPresets()`, `savePreset()`, `deletePreset()` |
| useFileDrop | 文件拖放状态 | `isDragging` | `onDragEnter()`, `onDrop()`, `reset()` |
| useLocale | 语言切换 | `currentLocale` | `setLocale()`, `toggleLocale()` |
| useTheme | 主题切换 | `currentTheme` | `setTheme()`, `toggleTheme()` |

### 5.3 Composable Patterns

**Bridge call pattern**:
```typescript
async function fetchSomething(): Promise<void> {
  const res = await call<DataType>("backend_method")
  if (res.success) {
    state.value = res.data!
  }
}
```

**Debounce + race condition protection pattern**:
```typescript
let requestId = 0
let inFlight = false

function updatePreview() {
  clearTimeout(timer)
  timer = setTimeout(async () => {
    const myId = ++requestId
    if (inFlight) return
    inFlight = true
    const res = await call(...)
    if (myId !== requestId) return  // discard stale
    inFlight = false
    // use result
  }, 500)
}
```

**Event listener auto-cleanup pattern** (in composable):
```typescript
export function useSomething() {
  const { on } = useBridge()

  on("some_event", handler)  // auto-cleans on unmount
}
```

---

## 6. Frontend Conventions

### 6.1 Component Style

Always use `<script setup lang="ts">`:

```vue
<script setup lang="ts">
import { ref, onMounted } from "vue"
import type { SomeDTO } from "../types/something"

const props = defineProps<{
  items: SomeDTO[]
  disabled?: boolean
}>()

const emit = defineEmits<{
  select: [item: SomeDTO]
  change: [value: string]
}>()
</script>
```

### 6.2 Type Definitions

- All DTO types use `interface` with `DTO` suffix: `TaskDTO`, `TranscodeConfigDTO`
- Exception: some lightweight types omit the suffix (`QueueSummary`, `FfmpegInstallInfo`, `AeStatus`, `AdvancedOptions`, `EncoderLists`)
- Union types use `type`: `TaskState = "pending" | "running" | ...`
- Always use `import type` for type-only imports
- Types defined in composables alongside the composable: `FfmpegVersionDTO`, `AppInfoDTO` in `useSettings.ts`

### 6.3 Styling Conventions

Tailwind utility classes only, DaisyUI components, **no scoped CSS**:

```
Card:    card bg-base-200 shadow-sm border border-base-300 card-body p-4
Input:   input input-bordered input-sm
Button:  btn btn-sm btn-primary | btn-ghost | btn-error | btn-warning
Badge:   badge badge-sm badge-success | badge-warning | badge-error | badge-info
Alert:   alert alert-error | alert-warning py-1 px-3 text-xs
Label:   label py-1 label-text text-xs
Modal:   <dialog class="modal"> + modal-box + modal-action + modal-backdrop
Grid:    grid grid-cols-1 lg:grid-cols-3 gap-x-6 gap-y-2
Opacity: opacity-40 | opacity-50 | opacity-60
Font:    text-xs | text-sm, font-mono (command display), tabular-nums (numbers)
```

### 6.4 i18n

All user-facing strings must be in both locale files:

```typescript
const { t } = useI18n()
// In template: {{ t("config.transcode.videoCodec") }}
// With interpolation: t("common.unsupportedFileType", { accept: ".mp4" })
```

Namespace structure:
- `common.*` -- Shared actions (cancel, save, delete, confirm)
- `nav.*` -- Navigation
- `config.*` -- Config page
- `taskQueue.*` -- Task queue
- `autoCut.*` -- Auto-cut
- `settings.*` -- Settings
- `ffmpeg.*` -- FFmpeg setup
- `avMix.*` -- AV-mix page
- `mergePage.*` -- Merge page
- `custom.*` -- Custom command page
- `encoderDescriptions.*` -- Encoder descriptions

### 6.5 Routing

Hash mode (required for pywebview), all pages lazy-loaded:

```typescript
// router.ts
const routes = [
  { path: "/task-queue", name: "TaskQueue", component: () => import("../pages/TaskQueuePage.vue") },
  // ...
]
```

### 6.6 File Dialog Pattern

```typescript
// Multi-file open
const res = await call<string[]>("select_files")
// Single-file with filter
const res = await call<string[]>("select_file_filtered", "Video Files (*.mp4;*.mkv)\0*.mp4;*.mkv\0")
// Folder picker
const res = await call<string[]>("select_output_dir")
// Drag-drop (after 80ms delay)
const res = await call<string[]>("get_dropped_files")
```

---

## 7. Backend Conventions

### 7.1 Data Models

All models in `core/models.py` use `@dataclass`:

```python
# Config/DTO types: frozen (immutable)
@dataclass(frozen=True)
class TranscodeConfig:
    video_codec: str = "libx264"
    audio_codec: str = "aac"

    def to_dict(self) -> dict:
        return {"video_codec": self.video_codec, "audio_codec": self.audio_codec}

    @classmethod
    def from_dict(cls, data: dict) -> TranscodeConfig:
        return cls(video_codec=data.get("video_codec", "libx264"), ...)
```

**Rules**:
- `frozen=True` for config/DTO types
- Mutable `@dataclass` only for runtime entities (`Task`)
- Always implement `to_dict()` / `from_dict()` with `.get(key, default)` for forward compatibility
- Use `Literal` for enum-like fields

### 7.2 Settings Management

`AppSettings` is frozen, so updates require constructing a new instance preserving all fields:

```python
current = load_settings()
new_settings = AppSettings(
    max_workers=current.max_workers,
    ffmpeg_path=new_path,          # changed
    ffprobe_path=ffprobe_path or current.ffprobe_path,
    auto_editor_path=current.auto_editor_path,
    # ... preserve ALL other fields
)
save_settings(new_settings)
```

Persistence:
- Location: `<app_dir>/data/settings.json`
- Atomic write via temp file + `os.replace()`
- Corrupt/missing file falls back to default `AppSettings()`

### 7.3 FFmpeg Command Builder (Plugin Registry)

<!-- v2.2.3-CHANGE: Added _INPUT_OPTIONS auto-split and clip merge notes -->

Transcode params and filters use the plugin registry pattern in `command_builder.py`:

```python
_register_transcode_param(
    "my_param",
    build=lambda val, tc, ctx: ["-my_flag", val],
    validate=lambda val, tc, ctx: (
        [{"level": "error", "message": f"Invalid: {val}"}]
        if val and val not in VALID_OPTIONS
        else []
    ),
)

_register_filter(
    "my_filter",
    priority=5,
    build_vf=lambda val, fc, ctx: [f"myfilter={val}"],
    build_af=lambda val, fc, ctx: [],
    validate=lambda val, fc, ctx: [...],
    needs_complex=False,
)
```

**v2.2.3 Custom command input/output split**: `_split_input_output_args()` uses `_INPUT_OPTIONS` whitelist to automatically place input-side options (`-ss`, `-accurate_seek`, etc.) before `-i` and output-side options after.

**v2.2.3 Clip merge**: When `use_copy_codec=false`, clip time args are injected into the main command chain via `_build_clip_time_args()` instead of dispatching to a standalone `build_clip_command()`.

```python
_register_transcode_param(
    "my_param",
    build=lambda val, tc, ctx: ["-my_flag", val],
    validate=lambda val, tc, ctx: (
        [{"level": "error", "message": f"Invalid: {val}"}]
        if val and val not in VALID_OPTIONS
        else []
    ),
)

_register_filter(
    "my_filter",
    priority=5,
    build_vf=lambda val, fc, ctx: [f"myfilter={val}"],
    build_af=lambda val, fc, ctx: [],
    validate=lambda val, fc, ctx: [...],
    needs_complex=False,
)
```

### 7.4 Process Execution

```python
# Windows flags (always use these)
subprocess.Popen(
    cmd,
    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
    stderr=subprocess.PIPE,
)

# Unix
subprocess.Popen(cmd, start_new_session=True, stderr=subprocess.PIPE)
```

### 7.5 Logging

```python
from core.logging import get_logger

logger = get_logger()
logger.info("message: {}", value)         # standard
logger.warning("warning: {}", value)      # auto-forwards to frontend
logger.exception("error: {}", value)      # with stack trace
```

WARNING+ logs automatically forwarded to frontend via `_emit("log_line", ...)`.

### 7.6 Thread Safety

- `task_queue.py`: Uses `threading.RLock` for all mutations
- `_emit()`: Already thread-safe (event queue pattern)
- Process tracking: Uses `threading.Lock` for `_running_procs` dict

---

## 8. Task State Machine

Six states defined in `core/models.py` via `TaskState` literal:

| State | Description |
|-------|-------------|
| `pending` | Waiting in queue |
| `running` | Actively executing |
| `paused` | Suspended (resumable) |
| `completed` | Finished successfully |
| `failed` | Finished with error |
| `cancelled` | User-cancelled |

### Valid Transitions

```
                    start
  pending ──────────────────────> running
     ^                             |   |   \
     |                             |   |    \
     |                             |   |     \ cancel
     |                             |   |      \
     |                     pause   |   |       \
     |                        ┌────┘   |        \
     |                        v        |         \
     |                      paused ────┘          \
     |                        |   \                \
     |                        |    \ cancel         \
     |                        |     \                \
     |                resume  |      v       complete \
     |                   ┌────┘   cancelled <───┐   failed
     |                   |        |              |     |
     |                   |        |              v     v
     |                   |        |          completed  failed
     |                   |        |              |     |
     +───────────────────+────────+──────────────+─────+
                      reset/retry
```

Transition validation in `core/models.py` via `VALID_TRANSITIONS` dict:
- `task.transition(new_state)` -- validates and raises `ValueError` on invalid transitions
- `task.can_transition(new_state)` -- returns `bool` without raising

Behavior:
- `retry`: preserves logs, returns task to `pending`
- `reset`: clears logs, returns task to `pending`

---

## 9. Development Workflow

### 9.1 Environment Setup

```bash
# Install dependencies
uv sync
cd frontend && bun install

# Start dev mode (Vite + pywebview)
uv run dev.py

# Build frontend check
cd frontend && bun run build 2>&1 | head -20
```

### 9.2 Documentation-First Development (Mandatory)

Every feature must follow this sequence:

1. **Update `docs/` files** before writing any code
2. Use HTML comments to mark changed line ranges: `<!-- v2.x.x-CHANGE: lineN-lineM -->`
3. Only then begin coding

| Requirement Type | Target Doc |
|-----------------|------------|
| State machine / task behavior | `docs/StateMachine.md` |
| Business rules | `docs/BusinessRules.md` |
| Process flows | `docs/Procedure.md` |
| Data model changes | `docs/fields/*.csv` |
| Architecture changes | `docs/Structure.md` |

### 9.3 Git Commit Convention

```
<type>(<scope>): <Chinese description>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

Examples:
```
feat(auto-editor): 新增自动剪辑多文件支持
fix(ui): 修正编码选项显示闪烁问题
refactor(config): 重构设置持久化逻辑
```

### 9.4 Adding a New Feature Page

1. Create page component in `frontend/src/pages/NewPage.vue`
2. Add route in `frontend/src/router.ts` (lazy-loaded)
3. Add nav link in `frontend/src/components/layout/AppNavbar.vue`
4. Add i18n keys in both `en.ts` and `zh-CN.ts`
5. Create composables in `frontend/src/composables/useNewFeature.ts`
6. Add types in `frontend/src/types/newFeature.ts`
7. Add API methods in `main.py` `FFmpegApi` class (if needed)
8. Update docs per documentation-first workflow

---

## 10. Reusable Patterns Summary

### 10.1 When to Use What

| Scenario | Reuse Target |
|----------|-------------|
| New file input | `FileDropInput.vue` + `useFileDrop()` |
| Text input with suggestions | `ComboInput.vue` |
| Dual file drop (intro/outro) | `SplitDropZone.vue` |
| Encoder selection | `EncoderSelect.vue` |
| Command display + validation | `CommandPreview.vue` |
| Shared config state | `useGlobalConfig()` |
| Task queue management | `useTaskQueue()` + `useTaskControl()` |
| Real-time progress | `useTaskProgress()` |
| Debounced command preview | `useCommandPreview()` |
| Settings persistence | `useSettings()` |
| Event subscription | `useBridge().on()` |

### 10.2 Anti-Patterns to Avoid

- Don't use Pinia/Vuex -- use composables for state management
- Don't use HTTP/fetch/axios for backend calls -- use `call()` bridge
- Don't use scoped `<style>` blocks -- use Tailwind utilities only
- Don't use Options API -- use `<script setup lang="ts">`
- Don't use `python3` -- use `uv run` or `python`
- Don't use `npm` -- use `bun`
- Don't hardcode string colors -- use DaisyUI semantic classes
- Don't throw errors in composables -- catch, set error refs, log
- Don't put mutable state in frozen dataclasses -- create new instances
- Don't forget `waitForPyWebView()` in page `onMounted`

### 10.3 Cross-Platform Process Control

```python
from core.process_control import suspend_process, resume_process, kill_process_tree

# Windows: uses NtSuspendProcess/NtResumeProcess (ntdll ctypes)
# Unix: uses SIGSTOP/SIGCONT
suspend_process(pid)
resume_process(pid)
kill_process_tree(pid)  # taskkill /F /T on Windows, os.killpg on Unix
```

---

## 11. Key File References

| File | Purpose | Lines (approx) |
|------|---------|----------------|
| `main.py` | API class, app entry | 850 |
| `core/models.py` | All data models | 530 |
| `core/command_builder.py` | FFmpeg command plugin registry + clip merge + custom cmd split | 1340 |
| `core/task_runner.py` | Task execution engine (passes file_duration to build_command) | 730 |
| `core/auto_editor_api.py` | Auto-editor API delegation | 520 |
| `core/ffmpeg_setup.py` | 6-tier binary discovery | 480 |
| `core/task_queue.py` | Task persistence + state machine | 280 |
| `core/auto_editor_runner.py` | Auto-editor command builder | 380 |
| `core/ffmpeg_runner.py` | Process execution + progress parsing | 230 |
| `core/config.py` | Settings persistence | 50 |
| `core/process_control.py` | OS process control | 150 |
| `core/paths.py` | Path resolution | 100 |
| `frontend/src/bridge.ts` | Frontend-backend bridge | 90 |
| `frontend/src/composables/useGlobalConfig.ts` | Shared config state | 220 |
| `frontend/src/composables/useTaskQueue.ts` | Task list management | 220 |
| `frontend/src/composables/useCommandPreview.ts` | Debounced preview | 100 |

---

## 12. Data Directory

Runtime data stored in `<app_dir>/data/`:

```
data/
  settings.json    # AppSettings (atomic write)
  queue_state.json # Task queue persistence
  presets/         # User presets (individual JSON files)
  logs/            # Daily rotating log files (10MB, 7-day retention)
```

Path resolution in `core/paths.py` handles PyInstaller frozen mode, dev mode, and legacy APPDATA migration.
