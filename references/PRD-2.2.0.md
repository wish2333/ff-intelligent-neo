# ff-intelligent-neo 2.2.0 - Auto-Editor Integration PRD

**Date:** 2026-04-26
**Branch:** dev-2.2.0
**Based on:** `references/2026-04-26-auto-editor-design.md` (v1.5)
**Target:** auto-editor v30.1.4

---

## 开发流程规范（重要）

> **本节为强制性规范，所有开发者必须遵守。**（继承自 PRD-2.1.0）

### 文档先行原则

2.1.1 版本的每个需求在进入开发阶段之前，**必须先更新 `docs/` 目录下的对应文档**。具体要求：

1. **定位关联文档**：每个需求明确关联需要修改的 `docs/` 文件
2. **标记变更行数**：在 `docs/` 文件中使用注释标记行号范围，格式为 `<!-- v2.1.1-CHANGE: 行N-行M -->`
3. **同步到 PRD**：将修改后的 `docs/` 内容段复制到本 PRD 的"文档变更追踪"附录中，以便开发时快速参照
4. **变更完成后开发**：文档变更经确认后，方可开始代码实现

### 文档与代码映射

| 需求类别            | 需关联的 docs 文件      | 说明                         |
| ------------------- | ----------------------- | ---------------------------- |
| 状态机/任务行为变更 | `docs/StateMachine.md`  | 状态转移、按钮映射、终态处理 |
| 业务规则变更        | `docs/BusinessRules.md` | 验证规则、约束条件、异常处理 |
| 流程变更            | `docs/Procedure.md`     | 操作流程、时序图             |
| 数据模型变更        | `docs/fields/*.csv`     | 字段新增/修改/删除           |
| 架构变更            | `docs/Structure.md`     | 模块关系、API 变更           |

## Overview

Integrate [auto-editor](https://github.com/WyattBlue/auto-editor) (v30.1.4) as a new "Auto Cut" feature, enabling automatic silence/motion detection and cutting. Follows the same architecture as the existing FFmpeg integration: independent API class, dedicated runner, shared task queue.

---

## Implementation Phases

### Phase 1: Backend Foundation

> Goal: Core backend modules that can be tested independently without frontend.

#### 1.1 AppSettings - auto_editor_path field

**File:** `core/models.py`

- Add `auto_editor_path: str = ""` to `AppSettings` dataclass
- Update `to_dict()` / `from_dict()` to include the new field
- Existing `load_settings()` / `save_settings()` in `core/config.py` handle persistence automatically (JSON)

**Acceptance criteria:**
- `AppSettings().auto_editor_path == ""`
- `AppSettings.from_dict({"auto_editor_path": "/usr/bin/auto-editor"}).auto_editor_path` works
- Round-trip: save then load preserves the value

---

#### 1.2 auto_editor_runner.py - Input validation & command builder

**New file:** `core/auto_editor_runner.py`

Implements two modules in one file (split later if >400 lines):

1. **`validate_local_input(input_file: str) -> Path`**
   - Reject URL inputs (http/https/ftp scheme)
   - Validate file exists, resolve path
   - Validate extension: `.mp4`, `.mov`, `.mkv`, `.m4v`, `.mp3`, `.wav`, `.m4a`, `.aac`
   - Raise `ValueError` with clear message on failure

2. **`build_command(input_file: str, params: dict, auto_editor_path: str, output_path: str | None = None) -> list[str]`**
   - Map UI params to CLI args (dash-form only, no underscores)
   - Add `--progress machine` automatically
   - Generate `--output` path when not in preview mode
   - Handle Basic tab params: `--edit`, `--margin`, `--smooth`, `--when-silent`, `--when-normal`
   - Handle Advanced tab params: `--cut-out`, `--add-in`, `--set-action`, `--frame-rate`, `--sample-rate`, `--resolution`, `-vn`/`-an`/`-sn`/`-dn`, `--video-codec`, `--audio-codec`, `-b:v`, `-b:a`, `-crf`, `--audio-layout`, `--audio-normalize`, `--no-cache`, `--open`, `--faststart`/`--no-faststart`, `--fragmented`/`--no-fragmented`
   - Multi-range flags: repeat per range (e.g., `--cut-out 0,10 --cut-out 15,20`)
   - When `_preview_mode` in params: use placeholder output path

3. **`generate_output_path(input_file: str, output_dir: str, task_id: str, extension: str) -> Path`**
   - Atomic validation: output_dir exists/writable, path traversal prevention
   - Unique filename: `{stem}_{task_id[:8]}.{extension}`

**Acceptance criteria:**
- `validate_local_input("https://...")` raises `ValueError("URL input is not supported")`
- `validate_local_input("/nonexistent.mp4")` raises `ValueError`
- `build_command` produces valid CLI with `--progress machine`
- Multi-range: 2 cut-out ranges produce 2 `--cut-out` flags
- Preview mode: output path is placeholder, no real file created
- Output path: within output_dir (path traversal blocked)

---

#### 1.3 auto_editor_runner.py - Stream parser

**File:** `core/auto_editor_runner.py` (continued)

1. **`parse_auto_editor_segment(segment: str) -> dict | None`**
   - Parse `title~current~total~eta_seconds` format
   - Handle trailing `\r`/`\n`
   - Float progress, float eta_seconds
   - Handle title containing `~` (last 3 fields are numeric)
   - Non-machine format returns `{'type': 'log', 'message': segment}`

2. **`read_auto_editor_output(proc)` generator**
   - Read byte-by-byte, split on `\r`
   - Yield parsed segments

**Acceptance criteria:**
- `"Video~123~1000~45.2\r"` -> `{title: "Video", progress: 12.3, eta_seconds: 45.2}`
- `"foo~bar~2~10~8\r"` -> `{title: "foo~bar", progress: 20.0, eta_seconds: 8.0}`
- Empty/non-machine segments return log entries
- Buffer handles incomplete segments across reads

---

#### 1.4 task_runner.py - Auto-editor task type support

**File:** `core/task_runner.py`

- Add `auto_editor` to recognized task types
- Dispatch to `read_auto_editor_output` for auto-editor tasks
- Use `NO_COLOR=1` env var for auto-editor processes
- Build command once at execution time (not in API layer)
- Store `proc` and `output_path` in task metadata for cancel support

**Acceptance criteria:**
- `task_type='auto_editor'` routes to `\r`-based parser (not `\n`)
- `NO_COLOR=1` set in subprocess env
- Command built at execution, not at enqueue time

---

#### 1.5 AutoEditorApi class

**New file:** `core/auto_editor_api.py` (or inline in `main.py`)

API methods (all return `{'success': bool, 'data': ..., 'error': ...}`):

| Method | Description |
|--------|-------------|
| `set_auto_editor_path(path)` | Validate binary via `--version`, save to settings |
| `get_auto_editor_status()` | Check path, version, compatibility (>=30.1.0, <31.0.0) |
| `get_auto_editor_encoders(output_format)` | Query `auto-editor info -encoders <fmt>` (single dash), parse structured output |
| `add_auto_editor_task(input_file, params)` | Validate input + params, enqueue task (NO command building) |
| `preview_auto_editor_command(params)` | Build preview command, return `{argv, display}` |
| `cancel_auto_editor_task(task_id)` | Terminate process, cleanup partial output |

**Key details:**
- `get_auto_editor_encoders`: parse `v: / a: / s: / other:` prefixes from stdout
- `add_auto_editor_task`: validate audio-only + motion edit incompatibility, single file
- `preview_auto_editor_command`: requires `input_file` key (no `input` alias)
- `cancel_auto_editor_task`: terminate -> wait(5s) -> kill -> cleanup output file
- All subprocess calls: `shell=False`

**Register in main.py:**
- Create `AutoEditorApi` instance alongside `FFmpegApi`
- Register with pywebvue `App`

**Acceptance criteria:**
- All methods return `ApiResult` format
- Path validation runs `--version` with timeout
- Version parsing: "auto-editor 30.1.4" -> `[30, 1, 4]`
- Encoder query: `mp4` format returns `{video: [...], audio: [...], ...}`
- Cancel: process terminated, partial output cleaned

---

#### 1.6 Main.py integration

**File:** `main.py`

- Import and instantiate `AutoEditorApi`
- Register with pywebvue App (second Bridge class)
- Pass `settings` reference to `AutoEditorApi.__init__`

**Acceptance criteria:**
- App starts with both FFmpegApi and AutoEditorApi registered
- Frontend can call auto-editor API methods via bridge

---

### Phase 2: Frontend - Page Shell & Routing

> Goal: Navigateable page with file input, basic layout, and composable skeleton.

#### 2.1 Router & Navigation

**Files:** `frontend/src/router.ts`, `frontend/src/components/layout/AppNavbar.vue`, `frontend/src/i18n/locales/en.ts`, `frontend/src/i18n/locales/zh-CN.ts`

- Add route: `{ path: '/auto-cut', name: 'AutoCut', component: () => import('./pages/AutoCutPage.vue') }`
- Add nav item in `AppNavbar.vue` between AudioSubtitle and Merge
- Add i18n key: `nav.autoCut` = "Auto Cut" / "自动剪辑"

**Acceptance criteria:**
- `/auto-cut` route loads AutoCutPage
- Navbar shows new item with correct label
- Language switch shows correct translation

---

#### 2.2 AutoCutPage.vue - Page shell

**New file:** `frontend/src/pages/AutoCutPage.vue`

Layout:
```
AutoCutPage.vue
├── Status bar (auto-editor availability: path set? version compatible?)
├── FileDropInput (single file only, reject URLs and multiple files)
├── Tab container (BasicTab | AdvancedTab)
├── CommandPreview (type='auto-editor')
└── Action button: "Add to Queue"
```

Status bar states:
- Not configured: "Set auto-editor path in Settings"
- Version incompatible: "Version X not supported (need 30.1.x)"
- Ready: hidden (or green indicator)

**Acceptance criteria:**
- Page renders with all sections
- Status bar shows correct message based on auto-editor availability
- "Add to Queue" button disabled when not configured

---

#### 2.3 useAutoEditor.ts composable

**New file:** `frontend/src/composables/useAutoEditor.ts`

State:
- `editMethod: Ref<'audio' | 'motion'>` (subtitle hidden in v1)
- `audioThreshold: Ref<number>` (default 0.04, range 0.01-0.20)
- `motionThreshold: Ref<number>` (default 0.02, range 0.01-0.20)
- `whenSilentAction: Ref<string>` (default 'cut')
- `whenNormalAction: Ref<string>` (default 'nil', supports 'cut')
- `margin: Ref<string>` (default '0.2s')
- `smooth: Ref<string>` (default '0.2s,0.1s')
- `advancedOptions: Reactive<AdvancedOptions>` (all advanced params)
- `commandPreview: Ref<string>` (computed via backend call, debounced)
- `autoEditorStatus: Ref<{available, compatible, version, path}>`
- `selectedFile: Ref<string | null>`

Methods:
- `fetchStatus()` - call `get_auto_editor_status`
- `setPath(path)` - call `set_auto_editor_path`
- `fetchEncoders(format)` - call `get_auto_editor_encoders`
- `updatePreview()` - call `preview_auto_editor_command`, debounced
- `addToQueue()` - call `add_auto_editor_task`

**Acceptance criteria:**
- Status fetched on composable init
- Preview updates when any param changes (debounced 300ms)
- Thresholds split by edit method (audio threshold for audio, motion threshold for motion)

---

#### 2.4 CommandPreview.vue - auto-editor type support

**File:** `frontend/src/components/config/CommandPreview.vue`

- Add `type` prop: `{ type: String, default: 'ffmpeg', validator: v => ['ffmpeg', 'auto-editor'].includes(v) }`
- When `type='auto-editor'`: disable ffmpeg-specific highlighting, plain text display
- Display user file paths as plain text (no `v-html`, XSS prevention)

**Acceptance criteria:**
- `type='auto-editor'` renders command as plain text
- No HTML injection from file paths
- Existing ffmpeg preview behavior unchanged

---

### Phase 3: Frontend - Basic Tab

> Goal: Complete Basic tab UI with all options.

#### 3.1 BasicTab.vue

**New file:** `frontend/src/components/auto-cut/BasicTab.vue`

Controls:
| Control | Type | Default | Notes |
|---------|------|---------|-------|
| Edit method | Radio/Select | audio | audio, motion (subtitle hidden) |
| Threshold | Slider | 0.04 (audio) / 0.02 (motion) | Range 0.01-0.20, step 0.01 |
| When-silent action | Select | cut | cut, speed:X, volume:X, nil |
| When-normal action | Select | nil | nil, cut, speed:X, volume:X |
| Speed value | Input | 4 | Shown when speed action selected |
| Volume value | Input | 0.5 | Shown when volume action selected |
| Margin | Input | 0.2s | |
| Smooth mincut | Input | 0.2s | |
| Smooth minclip | Input | 0.1s | |

Action value inputs show/hide based on selected action type.

**Acceptance criteria:**
- Switching edit method swaps threshold value and range
- Action value inputs appear/disappear dynamically
- All values bound to useAutoEditor composable
- Threshold slider shows numeric value

---

### Phase 4: Frontend - Advanced Tab

> Goal: Complete Advanced tab with all options organized by section.

#### 4.1 AdvancedTab.vue

**New file:** `frontend/src/components/auto-cut/AdvancedTab.vue`

Sections:
1. **Actions**: Cut-out ranges, Add-in ranges, Set-action ranges (dynamic list, add/remove)
2. **Timeline**: Frame rate, Sample rate, Resolution inputs
3. **Container**: Toggle switches for `-vn`/`-an`/`-sn`/`-dn`, Faststart (default ON, flag only when OFF), Fragmented (default OFF, flag only when ON)
4. **Video**: Codec select (populated from encoder query), Bitrate input, CRF input
5. **Audio**: Codec select (populated from encoder query), Bitrate input, Layout input, Normalize select (none/peak/ebu)
6. **Misc**: No-cache toggle, Open toggle (with queue warning), Output extension select (mp4/mkv/mov)

**Acceptance criteria:**
- Codec dropdowns populated dynamically from `get_auto_editor_encoders(format)`
- Output extension change triggers re-query of encoders
- Range lists support add/remove with validation
- Container toggles follow design: faststart ON = no flag, OFF = `--no-faststart`

---

### Phase 5: Frontend - Settings & Polish

> Goal: Settings page integration and UX polish.

#### 5.1 Settings - Auto-Editor Path

**Files:** `frontend/src/pages/SettingsPage.vue`, `frontend/src/components/settings/` (new component optional)

- Add "Auto-Editor Path" section (mirrors FFmpeg Setup pattern)
- File picker + manual path input
- Validate on change: show version + compatibility status
- Save to settings on successful validation

**New component (optional):** `frontend/src/components/settings/AutoEditorSetup.vue`

**Acceptance criteria:**
- Path input with browse button
- Version displayed after validation
- Incompatible version shows warning
- Invalid path shows error
- Saved to AppSettings via `save_settings`

---

#### 5.2 FileDropInput - Single file constraint

**File:** `frontend/src/components/common/FileDropInput.vue`

- Add `multiple` prop (default true for backward compat)
- When `multiple=false`: reject multiple files with error "Please select only one file"
- AutoCutPage uses `:multiple="false"`

**Acceptance criteria:**
- Existing pages with multiple file support unchanged
- AutoCutPage rejects multiple files
- Error message displayed when multiple files dropped

---

#### 5.3 Task Queue Integration

**Files:** `frontend/src/pages/TaskQueuePage.vue`, `frontend/src/composables/useTaskProgress.ts`

- Auto-editor tasks appear in task queue like FFmpeg tasks
- Progress bar shows percentage from `\r`-parsed progress
- Task type icon/label distinguishes auto-editor from ffmpeg tasks
- Cancel button works for auto-editor tasks

**Acceptance criteria:**
- Auto-editor task shows in queue with correct type label
- Progress updates in real-time
- Cancel terminates process and shows cancelled status

---

### Phase 6: Integration & Testing

> Goal: End-to-end functionality verification.

#### 6.1 Manual Test Guide

Phase 1 specific manual tests (backend-only, no frontend needed):

1. **AppSettings round-trip**: Create AppSettings with auto_editor_path="/test/path", call to_dict(), create from_dict(), verify path preserved
2. **validate_local_input**: Pass a URL (https://...) - expect ValueError "URL input is not supported". Pass a non-existent file - expect ValueError "File not found". Pass a .txt file - expect ValueError "Unsupported file format". Pass a valid .mp4 file - expect Path returned
3. **build_command**: Build with edit=audio, margin=0.2s - verify --progress machine, --edit audio, --margin 0.2s present. Build with cut_out_ranges=["0,10","15,20"] - verify 2x --cut-out. Build with _preview_mode=True - verify _preview_output.mp4 in output
4. **parse_auto_editor_segment**: "Video~500~1000~30.0" -> progress 50.0. "foo~bar~200~1000~8" -> title "foo~bar", progress 20.0. Empty string -> None. "random text" -> {type: "log", message: "random text"}
5. **generate_output_path**: Valid temp dir + task_id -> filename {stem}_{task_id[:8]}.mp4 inside dir. Extension without dot ("mp4") -> auto-normalized to ".mp4"
6. **AutoEditorApi.get_auto_editor_status**: No path set -> {available: false, compatible: false}
7. **AutoEditorApi.get_auto_editor_encoders**: Format "flv" -> {success: false, error about unsupported format}. Format "mp4" (no path) -> {success: false, error about path not configured}
8. **AutoEditorApi.set_auto_editor_path**: Non-existent path -> {success: false, error "File not found"}

#### 6.2 Unit Test Items

**File:** `tests/test_auto_editor_runner.py` (new)

Test cases:
- `validate_local_input`: URL rejection, missing file, invalid extension, valid file
- `build_command`: basic params, advanced params, multi-range flags, preview mode, output extension, motion edit (no --my-thresh)
- `parse_auto_editor_segment`: standard format, title with `~`, empty segment, non-machine format, trailing `\r`
- `generate_output_path`: valid path, path traversal blocked, task_id uniqueness, extension normalization

**File:** `tests/test_auto_editor_api.py` (new)

Test cases (with mocked subprocess):
- `set_auto_editor_path`: valid path, invalid path, subprocess error
- `get_auto_editor_status`: not configured, valid version, incompatible version, parse error
- `get_auto_editor_encoders`: valid output parsing, invalid format, empty result
- `add_auto_editor_task`: valid params, URL rejection, audio+motion incompatibility, single file
- `preview_auto_editor_command`: valid params, missing input_file, returns argv+display

---

## File Change Summary

### New files (8)

| File | Phase | Lines (est.) |
|------|-------|-------------|
| `core/auto_editor_runner.py` | 1.2, 1.3 | ~250 |
| `core/auto_editor_api.py` | 1.5 | ~200 |
| `frontend/src/pages/AutoCutPage.vue` | 2.2 | ~150 |
| `frontend/src/composables/useAutoEditor.ts` | 2.3 | ~180 |
| `frontend/src/components/auto-cut/BasicTab.vue` | 3.1 | ~200 |
| `frontend/src/components/auto-cut/AdvancedTab.vue` | 4.1 | ~300 |
| `frontend/src/components/settings/AutoEditorSetup.vue` | 5.1 | ~120 |
| `tests/test_auto_editor_runner.py` | 6.2 | ~200 |

### Modified files (9)

| File | Phase | Change |
|------|-------|--------|
| `core/models.py` | 1.1 | Add `auto_editor_path` field |
| `core/task_runner.py` | 1.4 | Add auto_editor task type dispatch |
| `main.py` | 1.5, 1.6 | Register AutoEditorApi |
| `frontend/src/router.ts` | 2.1 | Add /auto-cut route |
| `frontend/src/components/layout/AppNavbar.vue` | 2.1 | Add nav item |
| `frontend/src/i18n/locales/en.ts` | 2.1 | Add nav.autoCut key |
| `frontend/src/i18n/locales/zh-CN.ts` | 2.1 | Add nav.autoCut key |
| `frontend/src/components/config/CommandPreview.vue` | 2.4 | Add type prop |
| `frontend/src/components/common/FileDropInput.vue` | 5.2 | Add multiple prop |

---

## Dependency Order

```
Phase 1 (Backend)
  1.1 AppSettings ─────────────────────────────┐
  1.2 Runner (validate + build) ──── 1.3 Parser ──┤
  1.4 task_runner dispatch ─────────────────────┤
  1.5 AutoEditorApi (needs 1.2, 1.3) ──────────┤
  1.6 main.py registration (needs 1.5) ─────────┘

Phase 2 (Frontend Shell)
  2.1 Router + Nav + i18n ─── 2.2 Page shell ─── 2.3 Composable ─── 2.4 CommandPreview

Phase 3 (Basic Tab)
  3.1 BasicTab.vue (needs 2.3)

Phase 4 (Advanced Tab)
  4.1 AdvancedTab.vue (needs 2.3)

Phase 5 (Settings & Polish)
  5.1 AutoEditorSetup (needs 1.5)
  5.2 FileDropInput multiple prop
  5.3 Task queue integration (needs 1.4)

Phase 6 (Testing)
  6.1 Manual test guide
  6.2 Unit tests
```

Phases 3, 4, 5 can be partially parallelized after Phase 2 is complete.

---

## Out of Scope (v1)

- URL download integration (yt-dlp)
- Subtitle edit method (needs pattern parameter UI)
- Timeline visualization of cuts
- Preview of edited output before saving
- Batch processing (multiple files)
- Binary auto-downloader
- Audio-only output formats (.mp3/.wav/.m4a)
- "Run Now" button (queue-only in v1)

## 开发流程规范（重要）

> **本节为强制性规范，所有开发者必须遵守。**（继承自 PRD-2.1.0）

### 文档先行原则

2.1.1 版本的每个需求在进入开发阶段之前，**必须先更新 `docs/` 目录下的对应文档**。具体要求：

1. **定位关联文档**：每个需求明确关联需要修改的 `docs/` 文件
2. **标记变更行数**：在 `docs/` 文件中使用注释标记行号范围，格式为 `<!-- v2.1.1-CHANGE: 行N-行M -->`
3. **同步到 PRD**：将修改后的 `docs/` 内容段复制到本 PRD 的"文档变更追踪"附录中，以便开发时快速参照
4. **变更完成后开发**：文档变更经确认后，方可开始代码实现

### 文档与代码映射

| 需求类别            | 需关联的 docs 文件      | 说明                         |
| ------------------- | ----------------------- | ---------------------------- |
| 状态机/任务行为变更 | `docs/StateMachine.md`  | 状态转移、按钮映射、终态处理 |
| 业务规则变更        | `docs/BusinessRules.md` | 验证规则、约束条件、异常处理 |
| 流程变更            | `docs/Procedure.md`     | 操作流程、时序图             |
| 数据模型变更        | `docs/fields/*.csv`     | 字段新增/修改/删除           |
| 架构变更            | `docs/Structure.md`     | 模块关系、API 变更           |

# 附录A 文档变更追踪

## Phase 1 文档变更

### docs/fields/AppSettings.csv

<!-- v2.2.0-CHANGE: 新增 auto_editor_path 字段 -->

新增行:
```
auto_editor_path,str,"",No,Custom auto-editor binary path,"If empty, auto-cut feature disabled; set via Settings page; validated via --version check (>=30.1.0, <31.0.0); persisted to settings.json via save_settings API"
```

### docs/Structure.md

<!-- v2.2.0-CHANGE: 版本索引新增 v2.2.0 条目，目录树新增 auto_editor 模块，Bridge API 新增 AutoEditorApi 文档 -->

1. 版本变更索引新增:
   - `| v2.2.0 / Phase 1 | auto-editor 后端基础 | 新增 auto_editor_runner.py、auto_editor_api.py，AppSettings 扩展，task_runner 自动剪辑调度 |`
   - `| v2.2.0 / Phase 1 | 数据模型扩展 | AppSettings 新增 auto_editor_path 字段 |`

2. 整体结构目录树新增:
   - `core/auto_editor_runner.py`
   - `core/auto_editor_api.py`

3. Bridge API 章节新增 `AutoEditorApi Bridge（v2.2.0）` 完整文档（事件、API 方法、runner 模块、task_runner 扩展）

### docs/BusinessRules.md

<!-- v2.2.0-CHANGE: 新增 Auto-Editor 业务规则章节 -->

新增 `Auto-Editor 业务规则（v2.2.0）` 章节，包含:
- 输入验证规则（URL 拒绝、单文件限制、扩展名白名单、audio+motion 互斥）
- 版本兼容性规则（>=30.1.0, <31.0.0）
- 命令构建规则（--progress machine、预览模式、多范围参数、容器 flag 逻辑、NO_COLOR）
- 输出路径规则（路径遍历防护、唯一命名、目录校验）
- 取消任务规则（终止顺序、输出清理、进程树）

### docs/Procedure.md

<!-- v2.2.0-CHANGE: 新增 4 个 auto-editor 流程 -->

1. 版本变更索引新增 4 条 v2.2.0 流程条目
2. 新增 `Auto-Editor 流程（v2.2.0）` 章节，包含:
   - Auto-Editor 路径设置流程（mermaid 时序图）
   - Auto-Editor 任务添加流程（mermaid 时序图）
   - Auto-Editor 任务执行流程（mermaid 时序图）
   - Auto-Editor 编码器查询流程（mermaid 时序图）

### docs/StateMachine.md

<!-- v2.2.0-CHANGE: 无需修改 -->
- 通用状态机已覆盖 auto-editor 任务，无需额外变更
## Phase 2 文档变更

### docs/Structure.md

<!-- v2.2.0-CHANGE: 版本索引新增 Phase 2 条目，目录树新增前端文件，新增组件/composable/路由文档 -->

1. 版本变更索引新增 6 条 Phase 2 条目:
   - `| v2.2.0 / Phase 2 | 前端页面与路由 | 新增 /auto-cut 路由、AutoCutPage.vue、useAutoEditor.ts composable |`
   - `| v2.2.0 / Phase 2 | 导航栏扩展 | AppNavbar.vue 新增 AutoCut 导航项 + auto-editor 状态徽标 |`
   - `| v2.2.0 / Phase 2 | CommandPreview 扩展 | CommandPreview.vue 新增 type prop 支持 auto-editor 命令预览 |`
   - `| v2.2.0 / Phase 2 | 国际化扩展 | en.ts / zh-CN.ts 新增 nav.autoCut 及 auto-cut 相关翻译键 |`
   - `| v2.2.0 / Phase 2 | FileDropInput 扩展 | 新增 multiple prop 支持单文件约束模式 |`

2. 整体结构目录树新增:
   - `frontend/src/composables/useAutoEditor.ts`
   - `frontend/src/pages/AutoCutPage.vue`
   - `frontend/src/components/auto-cut/BasicTab.vue`

3. 新增 Composable 文档章节 `useAutoEditor.ts`（状态、方法、行为）
4. 新增页面组件文档 `AutoCutPage.vue`（布局、状态栏、行为）
5. 新增配置组件文档 `CommandPreview.vue`（新增 type prop）
6. 更新 `AppNavbar.vue` 文档（新增 AutoCut 导航项 + auto-editor 状态徽标）
7. 路由表新增 `/auto-cut` 路由条目

### docs/BusinessRules.md

<!-- v2.2.0-CHANGE: 新增 Auto-Editor 前端页面规则章节，页面布局规则新增 AutoCut 导航 -->

1. Phase 3.5 页面布局规则表新增 AutoCut 导航项
2. Auto-Editor 业务规则章节新增 `前端页面规则（v2.2.0 Phase 2）` 子章节，包含:
   - 页面布局规则（状态栏、单文件输入、选项卡、命令预览、按钮禁用、任务添加）
   - 命令预览规则（debounce、参数构建、阈值切换、状态监听）
   - 导航与国际化规则（导航项位置、i18n key、状态徽标）

### docs/Procedure.md

<!-- v2.2.0-CHANGE: 版本索引新增 Phase 2 条目，新增 2 个前端流程 -->

1. 版本变更索引新增 2 条 Phase 2 流程条目
2. 新增 `Auto-Editor 页面初始化流程`（状态检查 + composable 初始化）
3. 新增 `Auto-Editor 命令预览流程`（debounced 预览 + 与 FFmpeg 对比表）

### docs/StateMachine.md

<!-- v2.2.0-CHANGE: 无需修改 -->
- Phase 2 无状态机变更，通用状态机已覆盖 auto-editor 任务

## Phase 3 文档变更

### docs/Structure.md

<!-- v2.2.0-CHANGE: 版本索引新增 Phase 3 条目，新增 BasicTab.vue 组件文档 -->

1. 版本变更索引新增 3 条 Phase 3 条目:
   - `| v2.2.0 / Phase 3 | BasicTab 组件 | 新建 BasicTab.vue，包含编辑方法/阈值/动作值/动态显隐，从 AutoCutPage 提取 |`
   - `| v2.2.0 / Phase 3 | useAutoEditor 扩展 | 新增 speedValue/volumeValue ref，更新 buildParams |`
   - `| v2.2.0 / Phase 3 | i18n 扩展 | en.ts/zh-CN.ts 新增 speed/volume 翻译键 |`

2. 新增 `BasicTab.vue` 配置组件文档（控件表 + 动态行为说明）

### docs/BusinessRules.md

<!-- v2.2.0-CHANGE: auto-editor 前端页面规则新增 action 值输入规则 -->

1. 命令预览规则表新增:
   - action 值输入: speed:X / volume:X 时显示对应值输入框

### docs/Procedure.md

<!-- v2.2.0-CHANGE: 版本索引新增 Phase 3 条目，新增 action 值动态更新流程 -->

1. 版本变更索引新增 1 条 Phase 3 流程条目
2. 新增 `Auto-Editor Action 值动态更新流程`（speed/volume 动态显隐 + 参数构建）

### docs/StateMachine.md

<!-- v2.2.0-CHANGE: 无需修改 -->
- Phase 3 无状态机变更

## Phase 4 文档变更

### docs/Structure.md

<!-- v2.2.0-CHANGE: 版本索引新增 Phase 4 条目，目录树新增 AdvancedTab.vue，新增 AdvancedTab 组件文档 -->

1. 版本变更索引新增 3 条 Phase 4 条目:
   - `| v2.2.0 / Phase 4 | AdvancedTab 组件 | 新建 AdvancedTab.vue，6 个功能分区，编码器动态查询，范围列表动态增删 |`
   - `| v2.2.0 / Phase 4 | useAutoEditor 扩展 | 新增 encoderLists ref、编码器查询逻辑 |`
   - `| v2.2.0 / Phase 4 | i18n 扩展 | en.ts/zh-CN.ts 新增 AdvancedTab 翻译键 |`

2. 整体结构目录树新增:
   - `frontend/src/components/auto-cut/AdvancedTab.vue`

3. 新增 `AdvancedTab.vue` 配置组件文档（Props/Events/6 分区控件表/动态行为说明）

### docs/BusinessRules.md

<!-- v2.2.0-CHANGE: 新增 AdvancedTab 业务规则章节 -->

1. 新增 `前端页面规则（v2.2.0 Phase 4 — Advanced Tab）` 子章节，包含:
   - 编码器查询规则（触发时机、结果缓存、空结果处理）
   - 范围列表规则（格式、增删、空行过滤）
   - Container Toggles 规则（faststart/fragmented 默认值与 flag 逻辑）

### docs/Procedure.md

<!-- v2.2.0-CHANGE: 版本索引新增 Phase 4 条目，新增编码器查询与范围列表流程 -->

1. 版本变更索引新增 1 条 Phase 4 流程条目
2. 新增 `Auto-Editor 编码器查询流程`（触发时机、后端解析、前端填充、extension 变更重查）
3. 新增范围列表管理流程（增删/填写/删除/buildParams 构建）

### docs/StateMachine.md

<!-- v2.2.0-CHANGE: 无需修改 -->
- Phase 4 无状态机变更
## Phase 5 文档变更

### docs/Structure.md

<!-- v2.2.0-CHANGE: 版本索引新增 Phase 5 条目，目录树新增 AutoEditorSetup.vue，新增组件文档，TaskRow 扩展 -->

1. 版本变更索引新增 4 条 Phase 5 条目:
   - `| v2.2.0 / Phase 5 | AutoEditorSetup 组件 | 新建 AutoEditorSetup.vue，auto-editor 路径设置与版本检测，集成到 SettingsPage |`
   - `| v2.2.0 / Phase 5 | FileDropInput 扩展 | 新增 multiple prop，支持单文件约束模式 |`
   - `| v2.2.0 / Phase 5 | TaskDTO 扩展 | 新增 task_type 字段，TaskRow 区分 auto_editor / ffmpeg 任务类型 |`
   - `| v2.2.0 / Phase 5 | i18n 扩展 | en.ts/zh-CN.ts 新增 settings.autoEditor、任务类型标签翻译键 |`

2. 整体结构目录树新增:
   - `frontend/src/components/settings/AutoEditorSetup.vue`

3. FileDropInput.vue Props 表新增 `multiple` prop 文档

4. 新增 `AutoEditorSetup.vue` 配置组件文档（Props/Events/布局/行为）

5. FFmpegSetup.vue 文档后新增 AutoEditorSetup.vue 设置组件引用文档

6. TaskRow.vue 文档新增 task_type badge 标识说明

### docs/BusinessRules.md

<!-- v2.2.0-CHANGE: 新增 Phase 5 业务规则章节 -->

1. 新增 `前端页面规则（v2.2.0 Phase 5 — Settings & Polish）` 子章节，包含:
   - Auto-Editor Settings 规则（组件位置、路径选择、版本检测、事件监听、风格一致）
   - FileDropInput 单文件约束规则（multiple prop、多文件拒绝、错误提示、使用场景）
   - 任务队列集成规则（task_type 字段、类型标识、进度显示、取消支持、i18n 标签）

### docs/Procedure.md

<!-- v2.2.0-CHANGE: 版本索引新增 Phase 5 条目，新增 2 个 Phase 5 流程 -->

1. 版本变更索引新增 2 条 Phase 5 流程条目
2. 新增 `Auto-Editor 路径设置流程（Settings 页面）`（mermaid 时序图）
3. 新增 `Auto-Editor 任务队列集成流程`（文本流程描述）

### docs/StateMachine.md

<!-- v2.2.0-CHANGE: 无需修改 -->
- Phase 5 无状态机变更，通用状态机已覆盖 auto-editor 任务
## Phase 6 文档变更

### docs/Structure.md

<!-- v2.2.0-CHANGE: 版本索引新增 Phase 6 条目，目录树新增测试指南文件 -->

1. 版本变更索引新增 1 条 Phase 6 条目:
   - `| v2.2.0 / Phase 6 | 集成测试指南 | 新建 test-guide-2.2.0.md，覆盖后端与前端全阶段手动测试项 |`

2. 整体结构目录树新增:
   - `references/test-guide-2.2.0.md`

### docs/BusinessRules.md

<!-- v2.2.0-CHANGE: 无需修改 -->
- Phase 6 无业务规则变更，仅新增测试指南

### docs/Procedure.md

<!-- v2.2.0-CHANGE: 无需修改 -->
- Phase 6 无新流程变更，仅新增测试指南

### docs/StateMachine.md

<!-- v2.2.0-CHANGE: 无需修改 -->
- Phase 6 无状态机变更
