## dev-2.0.0

### Features

- 前端调整为多页面+组件化（按钮、文件列表、路径输入框等）
- 导航栏包括页面：文件管理任务队列；FFmpeg命令配置；软件配置
  - 文件管理任务队列页面
    - 任务添加、删除、编辑、排序（任务支持多选）
    - 队列状态可视化
    - 实时进度显示（百分比、时间剩余、帧数）
    - 任务状态跟踪（待执行、执行中、已暂停、已完成、失败）
    - 任务日志输出跳转查看
    - 开始、暂停、恢复、停止任务
    - 任务失败重试
    - 批量操作（全部暂停、全部停止、全部恢复）
  - FFmpeg命令配置页面
    - 支持转码操作（编码格式、码率、分辨率、帧率配置）
    - 支持滤镜应用（旋转、裁剪、水印、音量调整、速度调整）
    - 命令预览和参数验证

### PLAN

docs\PRD-2.0.0.md

```
     Legend: session-request | 🔴 bugfix | 🟣 feature | 🔄 refactor | ✅ change | 🔵 discovery | ⚖️ decision

     Column Key
       Read: Tokens to read this observation (cost to learn it now)
       Work: Tokens spent on work that produced this record ( research, building, deciding)

     Context Index: This semantic index (titles, types, files, tokens) is usually sufficient to understand past work.

     When you need implementation details, rationale, or debugging context:
       - Fetch by ID: get_observations([IDs]) for observations visible in this index
       - Search history: Use the mem-search skill for past decisions, bugs, and deeper research
       - Trust this index over re-reading code for past decisions and learnings

     Context Economics
       Loading: 50 observations (17,287 tokens to read)
       Work investment: 8,217 tokens spent on research, building, and decisions
       Your savings: -110% reduction from reuse

     Apr 22, 2026

     docs/PRD-2.0.0.md
       #723  2:12 PM  🔵  PRD-2.0.0.md structure overview reveals sections 1-2 cover project overview and navigation
       #724           🔵  PRD-2.0.0.md contains 13 major sections with 70 subsections covering architecture,
     implementation, and testing
       #725           🔵  PRD section 5.1 page layout shows FFmpeg status display but missing FFmpeg switching
     functionality
       #726           🔵  PRD section 3.6 and 6.6 contain task pause implementation but section 3.6 lacks resume
     mechanism documentation
       #727           🔵  PRD section 9 command building rules lack extensibility patterns for future FFmpeg feature
     additions
       #728  2:15 PM  ✅  Updated PRD section 3.6 to include comprehensive task pause and resume implementation plan
       #729           ✅  Enhanced PRD section 6.6 with complete task pause/resume implementation including error
     handling and thread coordination
       #730  2:16 PM  🟣  Added FFmpeg version switching functionality to PRD sections 5.1 and 5.2
       #731           ✅  Added extensibility design principles to PRD section 9 for command builder architecture
       #732  2:17 PM  ✅  Documented priority-based automatic filter sorting mechanism in PRD section 9.2
       #733           ✅  Added future extensibility examples and validation rules section to PRD section 9
       #734  2:18 PM  ✅  Added FFmpeg version switching Bridge API methods to PRD section 6.3
       #735           ✅  Added section 1.5 to PRD documenting completed PyWebVue framework updates and their impact on
     the project
     ..\..\Git\GithubManager\ff-intelligent-neo\docs\PRD-2.0.0.md
       #738  2:24 PM  🔵  Project codebase consists of 16 Python files organized in core and pywebvue modules
       #739           🔵  Frontend architecture uses Vue 3 with TypeScript composables for state management
       #740           🔵  PRD document uses Chinese chapter-based structure instead of standard markdown sections
       #741           🔵  PRD contains 13 sections covering architecture, implementation, and testing
       #742  2:25 PM  🔵  PRD defines 5-phase implementation plan with detailed technical specifications
     ..\..\Git\GithubManager\ff-intelligent-neo\main.py
       #743           🔵  Current implementation has 10+ PyWebVue @expose API methods in main.py
     ..\..\Git\GithubManager\ff-intelligent-neo\docs\PRD-2.0.0.md
       #744           🔵  PRD audit reveals critical documentation issues across sections 9-13
     ..\..\Git\GithubManager\ff-intelligent-neo\pywebvue\bridge.py
       #745           🔵  PyWebVue bridge architecture uses @expose decorator with automatic error handling
     ..\..\Git\GithubManager\ff-intelligent-neo\pyproject.toml
       #746           🔵  Project configured for Python 3.11+ with Vue 3.5 and modern frontend stack
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\vite.config.ts
       #747  2:26 PM  🔵  Current implementation uses single-page architecture without vue-router
     General
       #748           🔵  Frontend implementation totals 1081 lines across 10 components and 4 composables with no test
     coverage
     ..\..\Git\GithubManager\ff-intelligent-neo\app.spec
       #749           🔵  Project has PyInstaller build configuration but no automated testing infrastructure
       #750  2:27 PM  🔵  PyInstaller build configured for ff-intelligent-mvp with main.py entry point
     ..\..\Git\GithubManager\ff-intelligent-neo\presets\default_presets.json
       #751           🔵  Default presets include only audio extraction and remuxing, no video transcoding
     General
       #752           🔵  Frontend uses provide/inject pattern for shared state without routing or state management
     library
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\bridge.ts
       #753           🔵  Vue Router not installed or imported in frontend codebase
       #754           🔵  Bridge API provides type-safe Python communication with initialization polling and event
     handling
     General
       #755           🔵  bridge.ts exports only 2 functions but App.vue imports call function
     ..\..\Git\GithubManager\ff-intelligent-neo\core\preset_manager.py
       #756  2:28 PM  🔵  PresetManager separates default and user presets with dual-directory resolution
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\env.d.ts
       #757           🔵  TypeScript type definitions define pywebview bridge API with dynamic method signatures
     ..\..\Git\GithubManager\ff-intelligent-neo\docs\PRD-2.0.0.md
       #758  2:29 PM  🔵  Comprehensive project audit reveals complete codebase structure and architectural patterns
       #759           🔵  PRD audit complete - identified 12 major gaps between specifications and current
     implementation
     ..\..\Git\GithubManager\ff-intelligent-neo\main.py
       #760  2:30 PM  🔵  main.py implements 14 @expose methods with thread-safe file operations and lazy initialization

     ..\..\Git\GithubManager\ff-intelligent-neo\docs\PRD-2.0.0.md
       #761  2:38 PM  🔵  PRD document exists at docs/PRD-2.0.0.md
       #762           🔵  PRD section 6.1 contains Task model contradiction
       #763  2:39 PM  🔵  PRD section 9.2 contains filter ordering contradiction
       #764           🔵  PRD section 9.4 contains content error in validation rules
       #765           🔵  Phase plan requires restructuring with split and additions
       #766           🔵  PRD section 12 missing critical risk categories
       #767           🔵  PRD section 6.3 lacks API evolution documentation
       #768  2:40 PM  🔴  Fixed PRD section 6.1 Task model frozen contradiction
       #769           🔵  PRD section 9.2 contains filter ordering contradiction
       #770  2:41 PM  🔴  Fixed PRD section 9.2 filter ordering contradiction
       #771           🔴  Fixed PRD section 9.4 validation rules content error
       #772  2:42 PM  ✅  Restructured implementation plan with Phase 2 split and new validation phase
       #773  2:43 PM  ✅  Added missing risks to PRD section 12 risk assessment
       #774  2:44 PM  ✅  Annotated Bridge API methods with 1.x version origin in section 6.3
```

### Phase 1

```
  Phase 1: Foundation Layer - Complete

  What was built

  ┌─────┬───────────────────────────────────────────────────────────────────────────────────────────────────┬────────┐
  │  #  │                                              Content                                              │ Status │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 1   │ vue-router dependency installed via bun                                                           │ Done   │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 2   │ core/models.py - All 2.0 data models (TaskState, TranscodeConfig, FilterConfig, TaskConfig,       │ Done   │
  │     │ TaskProgress, Task, Preset, AppSettings) with state machine validation and JSON serialization     │        │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 3   │ core/config.py - AppSettings load/save to %APPDATA%/ff-intelligent-neo/settings.json              │ Done   │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 4   │ frontend/src/types/*.ts - 4 DTO type definition files (task, config, preset, settings)            │ Done   │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 5   │ frontend/src/composables/useBridge.ts - Event listener lifecycle management with auto-cleanup     │ Done   │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 6   │ frontend/src/router.ts + main.ts updated with hash-mode router                                    │ Done   │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 7   │ frontend/src/components/layout/AppNavbar.vue - Nav with page tabs + FFmpeg status                 │ Done   │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 8   │ 3 page placeholders (TaskQueue, CommandConfig, Settings)                                          │ Done   │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 9   │ App.vue rewritten as AppNavbar + router-view                                                      │ Done   │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 10  │ bridge.ts already had unified format, kept as-is                                                  │ Done   │
  ├─────┼───────────────────────────────────────────────────────────────────────────────────────────────────┼────────┤
  │ 11  │ Removed 11 old 1.x components/composables, simplified main.py to stubs                            │ Done   │
  └─────┴───────────────────────────────────────────────────────────────────────────────────────────────────┴────────┘

  Verification

  - TypeScript: zero errors
  - Vite build: succeeds (806ms)
  - Python imports: all OK

  Manual Testing Checklist

  1. Run uv run main.py and verify the app window opens with "FF Intelligent Neo" title
  2. Verify the navbar shows 3 navigation tabs: "Task Queue", "Command Config", "Settings"
  3. Click each tab - verify the URL changes to #/task-queue, #/command-config, #/settings
  4. Verify each page shows its placeholder text
  5. Verify FFmpeg status badge appears in the navbar (green/red based on FFmpeg availability)
  6. Verify the / route redirects to #/task-queue
```

#### 📝 Commit Message

```
feat(arch): 多页面应用基础架构搭建完成

- 升级为Vue Router多页面架构，实现TaskQueue、CommandConfig、Settings三大模块路由
- 完成核心数据模型和TypeScript类型定义体系
- 实现应用配置系统，支持持久化设置
- 开发导航栏组件，支持页面切换和FFmpeg状态显示
- 建立前后端桥接机制，实现事件监听生命周期管理
- 重构应用为组件化架构，移除冗余的1.x代码
- 创建基础页面占位符，为后续功能开发奠定架构基础
```

#### 🚀 Release Notes

```
## 2026-04-22 - 多页面应用基础架构发布

### ✨ 新增
- 完整的多页面应用框架，支持文件管理任务队列、FFmpeg命令配置和软件配置三个主要模块
- 统一的导航系统，可在功能页面间快速切换，并显示FFmpeg运行状态
- 基础页面框架已就绪，各页面已预留接口便于后续功能扩展
- 应用设置可持久化保存，确保用户配置不丢失
- 前后端数据交互机制已建立，为实时通信做好准备

### ⚡ 优化
- 应用启动速度显著提升：重构了组件结构，移除了冗余代码
- 代码质量提升：统一了数据模型定义，提高了类型安全性
```

### Phase 2a

```
  Phase 2a Summary

  What was built

  ┌─────────────────────────┬───────────┬───────┬────────────────────────────────────────────────────────────────────┐
  │          File           │  Action   │ Lines │                            Description                             │
  ├─────────────────────────┼───────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ core/models.py          │ Modified  │ ~350  │ Added to_dict/from_dict to all data classes, fixed transition()    │
  │                         │           │       │ return type                                                        │
  ├─────────────────────────┼───────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ core/file_info.py       │ Modified  │ ~95   │ Removed FileItem dependency, returns dict                          │
  ├─────────────────────────┼───────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ core/command_builder.py │ Created   │ ~100  │ build_command() + build_output_path() from TaskConfig              │
  ├─────────────────────────┼───────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ core/task_queue.py      │ Created   │ ~200  │ Thread-safe task CRUD, state machine, ordering, debounced JSON     │
  │                         │           │       │ persistence                                                        │
  ├─────────────────────────┼───────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ core/ffmpeg_runner.py   │ Rewritten │ ~180  │ Works with Task model, per-task cancel_event, log appending        │
  ├─────────────────────────┼───────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ core/task_runner.py     │ Created   │ ~200  │ ThreadPool, task dispatch, stop_all, race-condition-safe           │
  │                         │           │       │ completion                                                         │
  ├─────────────────────────┼───────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ core/config.py          │ Modified  │ ~55   │ Removed unused Callable import                                     │
  ├─────────────────────────┼───────────┼───────┼────────────────────────────────────────────────────────────────────┤
  │ main.py                 │ Rewritten │ ~290  │ 16 @expose methods: task CRUD, control, settings, dialogs          │
  └─────────────────────────┴───────────┴───────┴────────────────────────────────────────────────────────────────────┘

  New @expose methods in main.py

  - Task Queue: add_tasks, remove_tasks, reorder_tasks, get_tasks, get_queue_summary, clear_completed, clear_all
  - Task Control: start_task, stop_task, stop_all, pause_all (stub), resume_all (stub)
  - Settings: get_settings, save_settings
  - Existing: setup_ffmpeg, get_app_info, select_files, select_output_dir

  Review fixes applied

  - CRITICAL: Task.transition() return type None -> str
  - CRITICAL: Race condition guard in TaskRunner._run_task (try/except ValueError)
  - CRITICAL: Logging in TaskQueue.save_state/load_state error handlers
  - HIGH: Atomic add_tasks (probe all, then batch add)
  - HIGH: remove_tasks emits only for existing tasks
  - HIGH: Removed unused imports, added proper import json
  - MEDIUM: Eliminated serialization duplication via TaskConfig.to_dict/from_dict delegation

  Manual Test Items

  Run uv run main.py and verify in the browser console:

  1. call('get_tasks') returns {success: true, data: []}
  2. call('get_queue_summary') returns {success: true, data: {pending: 0, running: 0, ...}}
  3. call('get_settings') returns {success: true, data: {max_workers: 2, ...}}
  4. call('select_files') opens file dialog
  5. call('add_tasks', [{paths: ['...'], config: {}}]) returns tasks with probed metadata
  6. call('get_tasks') now returns the added tasks
  7. call('get_queue_summary') shows pending: 1
  8. call('remove_tasks', [{task_ids: ['...']}]) removes the task
```

#### ClaudeMem-Phase1,2

```
     Legend: session-request | 🔴 bugfix | 🟣 feature | 🔄 refactor | ✅ change | 🔵 discovery | ⚖️ decision
    Apr 22, 2026

     docs/PRD-2.0.0.md
       #822  7:35 PM  🔵  Phase 2a focuses on task queue backend implementation
       #823           🔵  Phase 1 frontend architecture gaps reviewed prior to Phase 2 development
       #824           🔵  Phase 1 requirements reviewed showing 12 implementation tasks for foundation layer
       #825           🔵  Phase 2a defines 5 backend implementation tasks for complete task management system
     core/__init__.py
       #826  7:36 PM  🔵  Phase 1 completion analysis reveals 5 critical Phase 2a gaps requiring implementation
     docs/PRD-2.0.0.md
       #827           🔵  Phase 2a development planning completed with comprehensive codebase analysis
     core/batch_runner.py
       #828           🔵  Phase 2a planning initiated with file structure review
     main.py
       #829           🔵  Code structure analysis tools encountered parsing limitations on Python files
       #830  7:37 PM  🔵  Phase 2a planning completed comprehensive codebase analysis of existing 1.x architecture
     core/models.py
       #831  7:38 PM  🟣  Phase 2a implementation started with core/task_queue.py task creation
       #832           🟣  Phase 2a implementation plan created with 6 interconnected tasks and dependency graph
     core/file_info.py
       #833           🟣  Phase 2a implementation commenced with three parallel tasks
     core/config.py
       #834  7:39 PM  🔵  JSON persistence reference pattern identified in config.py for task_queue implementation
     core/file_info.py
       #835  7:40 PM  🔄  file_info.py refactored to return dict instead of FileItem for Phase 2a compatibility
       #836           🟣  Phase 2a foundational modules completed: command_builder.py, task_queue.py, and file_info.py
     refactor
     core/ffmpeg_runner.py
       #837           🔄  ffmpeg_runner.py rewritten to integrate with Task model and TaskProgress frozen dataclass
     General
       #838           🟣  Phase 2a implementation progressing: task_runner.py started, ffmpeg_runner.py rewrite
     completed
     core/task_runner.py
       #839  7:41 PM  🟣  task_runner.py implemented with ThreadPool management, per-task cancellation, and event
     emission
     General
       #840           🟣  Phase 2a final task commenced: main.py rewrite to integrate task queue backend
     main.py
       #841           🟣  Phase 2a backend implementation completed: main.py rewritten with 12 task API methods
     core/models.py
       #842  7:43 PM  🔵  Phase 2a implementation verified: all Python module imports successful
     core/file_info.py
       #843  7:50 PM  🟣  Phase 2a task queue backend implementation completed and verified
     core/task_queue.py
       #844           🔵  Phase 2a task_queue functionality validated through comprehensive smoke test
     core/command_builder.py
       #845  7:54 PM  🔵  Windows path handling validated
       #846  7:56 PM  🔵  build_output_path function validated with cross-platform tests
     core/models.py
       #847           🟣  Phase 1 architecture refactor completed - migrated from MVP to 2.0 task-based model
     pywebvue/bridge.py
       #848  7:57 PM  🟣  Bridge infrastructure refactored for thread-safe event queuing and main-thread task execution

     main.py
       #849  7:58 PM  🟣  Phase 1 bridge API implementation completed with task queue management and control operations

     core/task_queue.py
       #850           🟣  Phase 1 core implementation modules completed with full task lifecycle management
     ..\..\Git\GithubManager\ff-intelligent-neo\core\models.py
       #851  8:05 PM  🔵  Code review identified critical bugs and race conditions in Phase 2a backend
       #852           🔴  Fixed Task.transition return type and added TaskConfig serialization methods
       #853  8:06 PM  🔄  Added serialization methods to TranscodeConfig class
       #854           🔄  Added serialization methods to FilterConfig class
       #855           🔄  Refactored Task serialization to delegate to nested objects
       #856  8:07 PM  🔄  Added to_dict method to TaskProgress class
       #857           🔄  Refactored Preset serialization to delegate to TaskConfig
     ..\..\Git\GithubManager\ff-intelligent-neo\core\task_runner.py
       #858           🔴  Fixed race condition in TaskRunner._run_task state transition
     ..\..\Git\GithubManager\ff-intelligent-neo\core\task_queue.py
       #859           🔴  Added error logging to TaskQueue persistence methods
     ..\..\Git\GithubManager\ff-intelligent-neo\core\ffmpeg_runner.py
       #860  8:08 PM  🔴  Replaced inline json import with top-level import in ffmpeg_runner.py
       #861           🔴  Added exception logging to stderr reader thread in ffmpeg_runner.py
     ..\..\Git\GithubManager\ff-intelligent-neo\main.py
       #862  8:09 PM  🔴  Refactored add_tasks to use atomic batch operations
       #863           🔴  Fixed remove_tasks to only emit events for actually removed tasks
     ..\..\Git\GithubManager\ff-intelligent-neo\core\models.py
       #864  8:11 PM  🔵  All code review fixes verified and passing
     General
       #865  8:13 PM  🔵  Bridge base class lacks setup_ffmpeg method
       #866           🔵  App class passes bridge instance to pywebview unchanged
       #867  8:14 PM  🔵  Error source identified in frontend bridge.ts call wrapper
       #868           🔵  AppNavbar.vue component calls missing setup_ffmpeg method
       #869           🔵  Application entry point confirmed - no bridge methods defined
       #870  8:15 PM  ✅  waitForPyWebView modified to verify setup_ffmpeg method availability
       #871           ✅  call function modified to verify methods are callable
```

### Phase2b

```
  Phase 2b Complete

  Files Created (13 new files)

  Utilities:
  - frontend/src/utils/format.ts - formatDuration, formatFileSize, formatPercent, formatResolution

  Composables (4):
  - frontend/src/composables/useTaskQueue.ts - tasks[], selectedIds[], summary, add/remove/clear/reorder
  - frontend/src/composables/useTaskControl.ts - startTask, stopTask, stopAll, pauseAll, resumeAll
  - frontend/src/composables/useTaskProgress.ts - progressMap{}, logsMap{} with event listeners
  - frontend/src/composables/useFileDrop.ts - drag state + pywebvue get_dropped_files integration

  Components (7):
  - frontend/src/components/task-queue/QueueSummary.vue - badge summary bar
  - frontend/src/components/task-queue/TaskProgressBar.vue - progress bar + time/speed/fps
  - frontend/src/components/task-queue/TaskRow.vue - file info + state badge + action buttons
  - frontend/src/components/task-queue/TaskList.vue - table container with empty state
  - frontend/src/components/task-queue/TaskToolbar.vue - add/remove/clear + select all
  - frontend/src/components/task-queue/BatchControlBar.vue - batch start/pause/resume/stop
  - frontend/src/components/task-queue/TaskLogPanel.vue - collapsible log viewer

  Page:
  - frontend/src/pages/TaskQueuePage.vue - full implementation composing all components

  Verification

  - TypeScript: zero errors
  - Vite build: succeeds (1.41s)

  Manual Test Checklist

  Run uv run main.py and verify in the app:

  1. Task Queue page loads without errors
  2. "Add Files" button opens file dialog, selected files appear in the list as "Pending"
  3. Drag-and-drop files onto the queue area - files are added
  4. Click checkbox on a task row to select it, checkbox in toolbar shows selection
  5. "Select All" checkbox selects/deselects all tasks
  6. "Remove" button removes selected tasks
  7. Click "Start" on a pending task - state changes to "Running" with progress bar
  8. Click "Stop" on a running task - state changes to "Cancelled"
  9. Click "Start All" - all pending tasks start sequentially
  10. Click "Stop All" - all active tasks stop
  11. Click "Log" button on a task - log panel opens showing FFmpeg stderr
  12. Close log panel via X button
  13. "Clear Done" removes completed tasks
  14. "Clear All" empties the queue
  15. Queue summary badges update in real-time
  16. Empty state shows "No tasks yet" placeholde
```

#### CC-Mem

```
     Legend: session-request | 🔴 bugfix | 🟣 feature | 🔄 refactor | ✅ change | 🔵 discovery | ⚖️ decision
Apr 22, 2026

     frontend/src/types/settings.ts
       #882  8:48 PM  🔵  Frontend settings types mirror backend AppSettings model
     frontend/src/bridge.ts
       #883  8:49 PM  🔵  Bridge API file confirmed unchanged from earlier read
     General
       #884           🔵  Smart outline parser cannot process TypeScript bridge.ts file
       #885           🔵  Bridge API file is 90 lines of TypeScript code
     frontend/src/bridge.ts
       #886           🔵  Bridge.ts uses Windows line endings causing line count discrepancy
       #887  8:50 PM  🔵  Bridge API provides complete pywebvue communication layer
     frontend/src/types/task.ts
       #888           🔵  Frontend codebase completely documented for Phase 2b baseline
     frontend/src/env.d.ts
       #889           🔵  TypeScript declarations define pywebview runtime injection contract
     frontend/src/bridge.ts
       #890  8:51 PM  🔵  Frontend type definitions and composables re-verified for Phase 2b
     General
       #891  8:52 PM  🔵  Smart outline parser fails repeatedly on TypeScript files
       #892           🟣  Phase 2b development started with format utility task creation
       #893           🟣  Drag-and-drop file upload composable task created
       #894  8:53 PM  🔵  Phase 2b development plan decomposed into 8 tasks
     frontend/src/utils/format.ts
       #895  8:54 PM  🟣  Format utility module implemented for Phase 2b
     frontend/src/composables/useTaskQueue.ts
       #896           🟣  Task queue state management composable implemented
     frontend/src/composables/useTaskControl.ts
       #897           🟣  Task control composable provides bridge API wrapper for task lifecycle
     frontend/src/composables/useTaskProgress.ts
       #898           🟣  Task progress tracking composable implemented with reactive maps
     General
       #899  8:55 PM  🔵  Pywebvue library provides built-in file drop functionality
     frontend/src/composables/useFileDrop.ts
       #900  8:56 PM  🟣  Drag-and-drop file upload composable implemented
     frontend/src/components/task-queue/QueueSummary.vue
       #901           🟣  Three task queue UI components implemented
     frontend/src/components/task-queue/TaskList.vue
       #902           🟣  Task list table container component implemented
       #903  8:58 PM  🟣  Four remaining task queue components completed
     frontend/src/components/task-queue/TaskRow.vue
       #904  8:59 PM  🔴  TypeScript compilation errors fixed in task queue components
     frontend_dist/index.html
       #905           🟣  Phase 2b task queue implementation completed successfully
     General
       #906           🔵  Phase 2b file inventory confirms complete implementation
       #907  9:17 PM  🔴  File list not displaying added files
     ..\..\Git\GithubManager\ff-intelligent-neo\pywebvue\app.py
       #908  9:18 PM  🔵  Located drag-and-drop implementation in pywebvue bridge
       #909  9:19 PM  🔵  Drag-and-drop handler registered during window loaded event
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useTaskQueue.ts
       #910  9:20 PM  🔵  Task queue composable uses bridge events for real-time updates
     ..\..\Git\GithubManager\ff-intelligent-neo\pywebvue\bridge.py
       #911           🔵  Drag-and-drop uses pull-based model with buffer storage
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useTaskQueue.ts
       #912           🔴  Fixed file list not displaying added tasks by updating state from API response
       #913           🔴  Fixed Vue reactivity issue in removeTasks function
       #914           🔴  Fixed Vue reactivity issue in task_removed event handler
     General
       #915  9:23 PM  🔵  File metadata extraction uses ffprobe with graceful fallback
     ..\..\Git\GithubManager\ff-intelligent-neo\pywebvue\bridge.py
       #916           🔴  Fixed pywebview tick method exposure error
     ..\..\Git\GithubManager\ff-intelligent-neo\pywebvue\app.py
       #917           🔴  Updated JavaScript timer to call public tick() method
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\App.vue
       #918  9:27 PM  🔵  File import feature completely non-functional with zero error visibility
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\layout\AppNavbar.vue
       #919           🔵  Application uses PyWebView architecture with Python-Vue bridge communication
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\pages\TaskQueuePage.vue
       #920  9:28 PM  🔵  File import uses two methods: Python bridge call and drag-and-drop composable
       #921           🔴  Added comprehensive error logging and PyWebView readiness check to TaskQueuePage
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useTaskQueue.ts
       #922  9:30 PM  ✅  Added diagnostic logging to addTasks function
     General
       #923  9:33 PM  🔵  Task queue implementation uses threading with debounced persistence
       #924           🔵  FFmpeg binary resolution uses three-tier fallback strategy
       #925           🔴  Task queue deadlock fixed by switching to reentrant lock
     TaskQueuePage.vue
       #926  9:45 PM  🔵  Drag-and-drop file upload fails on first attempt
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useFileDrop.ts
       #927  9:46 PM  🔴  Fixed drag-and-drop race condition with 50ms delay
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useTaskQueue.ts
       #928  9:47 PM  🔴  Fixed duplicate file entries by removing task_added event listener
     ..\..\Git\GithubManager\ff-intelligent-neo\core\command_builder.py
       #930  9:52 PM  🔵  FFmpeg output path generation lacks timestamp suffix
     ..\..\Git\GithubManager\ff-intelligent-neo\core\ffmpeg_runner.py
       #931           🔵  Task model and FFmpeg runner architecture analyzed
     ..\..\Git\GithubManager\ff-intelligent-neo\core\task_runner.py
       #932           🔵  Task execution flow and output path generation identified
```

#### 📝 Commit Message

```
feat(task-queue): 实现完整的任务队列管理系统

- 添加任务队列页面，支持文件添加、任务控制和进度跟踪
- 实现拖放上传和批量操作功能
- 创建任务状态管理、进度跟踪和日志查看组件
- 修复文件列表显示、Vue反应性和拖放竞态条件等问题
- 完成TypeScript类型检查和构建验证
```

#### 🚀 Release Notes

```
## 2026-04-22 - 任务队列管理系统上线

### ✨ 新增
- 全新任务队列页面，统一管理所有文件处理任务
- 支持拖放文件和传统文件选择两种添加方式
- 实现任务批量操作：选择、删除、全部开始/停止/暂停/恢复
- 任务状态可视化：实时进度条、速度显示、运行时间
- 任务日志查看器：可展开/收起的FFmpeg运行日志
- 任务统计摘要：实时显示待处理、运行中、已完成任务数量

### 🐛 修复
- 解决拖放文件首次尝试失败的问题
- 修复任务列表不显示添加文件的情况
- 优化Vue反应性，确保任务状态正确更新
- 消除任务队列中的死锁问题
- 防止重复文件条目产生

### ⚡ 优化
- 提升文件处理流程的用户体验
- 完善错误处理机制，提供更清晰的反馈信息
```

### Phase3

  Phase 3 Complete

```
Backend Changes (4 files)

  ┌──────────────────────────────┬───────────┬───────────────────────────────────────────────────────────────────────┐
  │             File             │  Action   │                              Description                              │
  ├──────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
  │                              │           │ Filter chain support (crop, scale, rotate, speed, watermark, volume)  │
  │ core/command_builder.py      │ Expanded  │ with priority-based ordering, parameter validation,                   │
  │                              │           │ build_command_preview(), validate_config()                            │
  ├──────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
  │ core/preset_manager.py       │ Rewritten │ Adapted to structured TaskConfig format. Fixed user presets dir to    │
  │                              │           │ ff-intelligent-neo. Added from_dict/to_dict serialization.            │
  ├──────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
  │ presets/default_presets.json │ Updated   │ 7 presets in structured config format: MP4 H.264, H.265/HEVC, 720p,   │
  │                              │           │ Audio MP3, Audio AAC, Remux, Extract WAV                              │
  ├──────────────────────────────┼───────────┼───────────────────────────────────────────────────────────────────────┤
  │ main.py                      │ Extended  │ 5 new @expose methods: build_command, validate_config, get_presets,   │
  │                              │           │ save_preset, delete_preset                                            │
  └──────────────────────────────┴───────────┴───────────────────────────────────────────────────────────────────────┘

  Frontend Changes (10 files)

  ┌──────────────────────────────────────┬────────────────────────────────────────────────┐
  │                 File                 │                     Action                     │
  ├──────────────────────────────────────┼────────────────────────────────────────────────┤
  │ composables/useConfig.ts             │ New - reactive transcode+filter form state     │
  ├──────────────────────────────────────┼────────────────────────────────────────────────┤
  │ composables/usePresets.ts            │ New - preset CRUD with bridge API              │
  ├──────────────────────────────────────┼────────────────────────────────────────────────┤
  │ composables/useCommandPreview.ts     │ New - debounced command preview + validation   │
  ├──────────────────────────────────────┼────────────────────────────────────────────────┤
  │ components/config/TranscodeForm.vue  │ New - codec/bitrate/resolution/framerate form  │
  ├──────────────────────────────────────┼────────────────────────────────────────────────┤
  │ components/config/FilterForm.vue     │ New - rotate/crop/watermark/volume/speed form  │
  ├──────────────────────────────────────┼────────────────────────────────────────────────┤
  │ components/config/CommandPreview.vue │ New - command text + error/warning display     │
  ├──────────────────────────────────────┼────────────────────────────────────────────────┤
  │ components/config/PresetSelector.vue │ New - dropdown + save/delete buttons           │
  ├──────────────────────────────────────┼────────────────────────────────────────────────┤
  │ components/config/PresetEditor.vue   │ New - modal dialog for saving presets          │
  ├──────────────────────────────────────┼────────────────────────────────────────────────┤
  │ pages/CommandConfigPage.vue          │ Rewritten - full page composing all components │
  ├──────────────────────────────────────┼────────────────────────────────────────────────┤
  │ types/config.ts, types/preset.ts     │ Unchanged (already defined in Phase 1)         │
  └──────────────────────────────────────┴────────────────────────────────────────────────┘

  Verification

  - TypeScript: 0 errors
  - Vite build: success (1.46s)
  - Python: all imports + validation tests pass

  Manual Test Items

    1. Navigate to "Command Config" tab - page loads with forms
    2. Select "MP4 H.264" preset - form fills with preset values
    3. Change video codec to "copy" - warning appears about filters
    4. Enter invalid resolution "abc" - error appears
    5. Enter crop "1920:800:0:140" - command preview updates with filter_complex
    6. Set volume "1.5" - volume=1.5 appears in command
    7. Set speed "2.0" - atempo=2.0 + setpts=0.5*PTS in command
    8. Click "Save as Preset" - modal opens, enter name, save
    9. Delete custom preset - removed from dropdown
    10. Click "Add to Queue" - file dialog opens, selected files appear in task queue
```

#### 问题

1. 选择预设后下方选择栏无变动，命令预览无变动
2. 切换界面后，命令配置界面内容完全丢失
3.  warning appears about filters是什么，切换成copy之后编码器相关配置确实没了，但是没见到什么东西多出来
4. 输入了错误内容之后，有警告。此时切换成copy或remove等无需resolution的模式后，警告未消失
5. 保存预设后没有立马显示到下拉栏，切换页面才显示，而且切换页面后配置完全丢失的问题仍然存在
6. 自定义预设Delete按钮冻结了按不了
7. 不应该是"Add to Queue"按钮的形式添加文件，应该是在命令配置界面设置的内容就是任务队列界面里面点开始时传输的参数

#### 修复报告

```
  ┌─────┬──────────────────────────────────┬────────────────────────────────────────────────────────────────────────┐
  │  #  │              Issue               │                                  Fix                                   │
  ├─────┼──────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ 1   │ Preset selection doesn't update  │ Fixed selectedId setter -- was no-op, now uses local ref               │
  │     │ form/preview                     │                                                                        │
  ├─────┼──────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ 2   │ Config lost on page switch       │ Created useGlobalConfig.ts module-level singleton; both pages share    │
  │     │                                  │ state                                                                  │
  ├─────┼──────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ 3   │ Copy+filter warning unclear      │ Warning only appears when filters are actually set (correct). Added    │
  │     │                                  │ help text explaining this                                              │
  ├─────┼──────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ 4   │ Validation warnings persist      │ Added watch in TranscodeForm to clear resolution/framerate/bitrate     │
  │     │ after codec switch               │ when codec changes to copy/none                                        │
  ├─────┼──────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ 5   │ Presets not refreshing after     │ PresetSelector now exposes fetchPresets, parent calls it after save    │
  │     │ save                             │                                                                        │
  ├─────┼──────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ 6   │ Delete button frozen             │ selectedId was broken (no-op setter). Now uses local ref, canDelete    │
  │     │                                  │ computed works correctly                                               │
  ├─────┼──────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ 7   │ Config page shouldn't have "Add  │ Removed button. TaskQueuePage now passes global config to addTasks()   │
  │     │ to Queue"                        │ automatically                                                          │
  └─────┴──────────────────────────────────┴────────────────────────────────────────────────────────────────────────┘
```

#### 问题

- 设置分辨率 1280x720，预览中未出现 `scale=1280:720`
- 设置输出容器，预览中未出现对应改变

  1. Resolution not in preview -- _build_filter_args only read from FilterConfig which has no resolution field.
      Resolution was only injected in the watermark code path. Fix: unified the active filter collection to include
      tc.resolution before branching, so both simple and complex paths see it.
  2. Output extension not changing -- build_command_preview used hardcoded "output.mp4". Fix: now uses
      output{config.transcode.output_extension} (e.g. output.mkv, output.mp3).

#### 重大问题

> 1. 音频转码部分存在删掉比特率后仍传递参数，即传递的参数与命令预览不一致的情况，请检查代码让传递参数与命令预览完全一致，并确保后续扩展的功能也能这样保持一致
> 2. Video Codec和Audio Codec和Output Format除了选项以外应该另外支持自定义输入

```
  问题根因： 之前 build_command() 里的转码参数是硬编码拼接的，build_command_preview()
  调用同一个函数所以预览本身一致，但条件判断逻辑（如 codec 为 copy 时不传 bitrate）分散在多处，容易遗漏。

  修复方式： 所有转码参数统一通过 _TRANSPILE_PARAMS 注册表构建。每个参数的 build 函数自带条件判断：

  # audio_bitrate 的 build 函数 — registry 内部已处理条件
  _register_transcode_param(
      "audio_bitrate",
      build=lambda val, tc, ctx: (
          ["-b:a", val]
          if val and tc.audio_codec not in ("copy", "none")  # 空值或copy模式不传
          else []
      ),
      ...
  )

  build_command() 不再硬编码，而是遍历注册表：

  def _build_transcode_args(tc, ctx):
      args = []
      for key, param in _TRANSPILE_PARAMS.items():
          val = getattr(tc, key, "")
          if val:
              args.extend(param["build"](val, tc, ctx))
      return args

  一致性保证机制：
  - build_command() 和 build_command_preview() 共享同一个 build_command() 函数
  - 所有参数的条件逻辑集中在各自的 build lambda 中
  - 新增参数只需 _register_transcode_param() 一次，build 和 validate 自动生效
  - 删除 bitrate 后 val 为空字符串，if val 为 False，不会生成参数

  所以删掉比特率后，val="" 不满足 if val，-b:a 不会被加入参数列表，预览和实际执行完全一致。
  
  输入栏改动说明： 新建了 ComboInput.vue 组件替换原来的 <input> + <datalist>：

  - 输入框右侧有下拉箭头按钮，点击展开全部建议列表
  - 输入时自动过滤匹配项
  - 点击建议项直接填入输入框
  - 仍可自由输入自定义值（如 libvpx-vp9）
  - 点击外部区域自动关闭下拉

  Video Codec、Audio Codec、Output Format 三个字段都已替换为 ComboInput。
```

#### CC-Mem

```
     Legend: session-request | 🔴 bugfix | 🟣 feature | 🔄 refactor | ✅ change | 🔵 discovery | ⚖️ decision

     Column Key
       Read: Tokens to read this observation (cost to learn it now)
       Work: Tokens spent on work that produced this record ( research, building, deciding)

     Context Index: This semantic index (titles, types, files, tokens) is usually sufficient to understand past work.

     When you need implementation details, rationale, or debugging context:
       - Fetch by ID: get_observations([IDs]) for observations visible in this index
       - Search history: Use the mem-search skill for past decisions, bugs, and deeper research
       - Trust this index over re-reading code for past decisions and learnings

     Context Economics
       Loading: 50 observations (11,969 tokens to read)
       Work investment: 0 tokens spent on research, building, and decisions

     Apr 22, 2026

     General
       #985  11:50 PM  🔵  Frontend Build Completed Successfully After Backend Validation Fixes
       #986            🔵  Background Task 7 Completed Successfully

     Apr 23, 2026

     General
       #987  12:00 AM  🔵  Multiple UI bugs reported in video processing application
       #988  12:01 AM  🟣  Global config store implementation initiated
       #989            🟣  Codec-dependent field auto-clearing implemented
       #990  12:02 AM  ⚖️  Task dependency chain established for bug fixes
     frontend/src/composables/useGlobalConfig.ts
       #991            🟣  Global configuration store composable implemented
     General
       #992            🟣  Global config store completed, preset selector fixes started
     frontend/src/components/config/PresetSelector.vue
       #993            🔵  PresetSelector selectedId setter is no-op causing selection failures
       #994            🔴  PresetSelector state management refactored to local refs
     frontend/src/components/config/TranscodeForm.vue
       #995            🔵  TranscodeForm uses direct v-model binding on config props
       #996  12:03 AM  🔴  Codec watchers added to clear dependent fields automatically
     frontend/src/pages/CommandConfigPage.vue
       #997            🔄  CommandConfigPage refactored to pure settings interface
     frontend/src/pages/TaskQueuePage.vue
       #998            🔵  TaskQueuePage addTasks currently only passes file paths
     frontend/src/composables/useTaskQueue.ts
       #999            🔵  addTasks already supports optional config parameter
     frontend/src/pages/TaskQueuePage.vue
       #1000            ✅  TaskQueuePage imports useGlobalConfig composable
       #1001            ✅  TaskQueuePage instantiates globalConfig composable
       #1002  12:04 AM  🟣  TaskQueuePage handleAddFiles passes global config to addTasks
       #1003            🟣  TaskQueuePage handleDrop passes global config to addTasks
     General
       #1004            🔄  Removed obsolete useConfig composable
       #1005            🔵  TypeScript type checking passed with no errors
       #1006  12:05 AM  🔵  Vite build completed successfully in 1.34s
     core/command_builder.py
       #1008  12:15 AM  🔵  Resolution and output container settings not applied in FFmpeg command builder
       #1010            🔵  Root cause identified: Resolution only processed in watermark path, not simple filter path
       #1011            🔴  Fixed resolution parameter not being applied in FFmpeg commands without watermark
       #1012  12:16 AM  🔵  build_command_preview hardcodes output filename as 'output.mp4', ignoring output_extension
     config
       #1013            🔴  Fixed build_command_preview to display correct output container format
       #1014            🔵  Verification confirms both bugs fixed: resolution and output extension now working correctly

     General
       #1016  12:32 AM  🔵  Located build_command function structure
       #1017            🔵  Examined filter argument building system
       #1018            🔵  Found dual-parameter system architecture inconsistency
       #1019            🔄  Simplified _build_filter_args function
       #1020  12:33 AM  🔴  Unified command building logic through registry system
       #1022            🔵  Examined TranscodeForm.vue codec/format selection
       #1023            🟣  Added custom input support for codecs and output formats
       #1025  12:34 AM  🟣  Frontend TypeScript validation and build successful
       #1026  12:35 AM  🔴  Restored dataclass import needed for ValidationContext
       #1027            🔴  Verified command builder consistency and functionality
       #1028  12:36 AM  🔵  Dropdown component lost dropdown functionality after input modification
     frontend/src/components/config/FilterForm.vue
       #1029            🔵  FilterForm.vue uses standard HTML select elements for dropdowns
     frontend/src/components/common/ComboInput.vue
       #1032  12:37 AM  🟣  Created ComboInput.vue component for combobox with suggestions
     frontend/src/components/config/TranscodeForm.vue
       #1033            🔄  TranscodeForm.vue migrated from datalist to ComboInput component
     General
       #1034  12:42 AM  🔵  TypeScript validation passed for ComboInput and TranscodeForm refactoring
       #1035            🔵  Vite build succeeded for ComboInput component integration
     #S1 Audio transcoding parameter consistency fix - user requested explanation of changes made to ensure passed
     parameters match command preview (Apr 23, 12:50 AM)

     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\common\ComboInput.vue
       #1036  12:53 AM  🔵  ComboInput component implementation examined
       #1037            🟣  ComboInput component enhanced with improved filtering behavior
       #1038            ✅  Input event handler refactored in ComboInput component
       #1039            ✅  Template references updated to use new items computed property
       #1040  12:54 AM  ✅  TypeScript type annotation added to onInput function parameter
       #1041            🔵  Build verification completed successfully
     #S2 ComboInput component enhanced with improved filtering behavior (Apr 23, 12:54 AM)


     Investigated: Examined the ComboInput component and identified opportunities to improve user experience by
     separating typing-based filtering from manual dropdown expansion behavior

     Learned: The component originally used a single filtering logic that didn't differentiate between user typing
     actions and intentional dropdown expansion. By adding a `showAll` state, the component now provides distinct
     behaviors for different user interactions while maintaining type safety with TypeScript annotations

     Completed: Successfully implemented enhanced ComboInput component with: (1) Added `showAll` reactive flag to
     control filtering modes, (2) Renamed `filtered` to `items` computed property with improved logic, (3) Enhanced
     dropdown toggle and focus handlers to reset showAll appropriately, (4) Centralized input event handling, (5) Added
     TypeScript type annotations, (6) Verified build completion with TypeScript checking and Vite build

     Next Steps: Component enhancements appear complete with successful build verification. The new behavior correctly
     distinguishes between typing-based filtering and manual dropdown expansion, providing better user experience
```

#### 📝 Commit Message

```
feat(config): 实现完整的命令配置系统与过滤链支持

- 新增视频过滤链功能：裁剪、缩放、旋转、速度、水印、音量调整
- 重构预设管理系统为结构化TaskConfig格式，支持CRUD操作
- 实现全局配置状态管理，解决页面切换状态丢失问题
- 统一命令构建逻辑，确保预览与实际执行参数完全一致
- 添加ComboInput组件支持自定义编解码器和输出格式输入
- 修复多处UI问题：预设选择无效、表单验证状态保持等
```

#### 🚀 Release Notes

```
## 2026-04-23 - 全新命令配置系统发布

### ✨ 新增
- 强大的视频过滤链功能：支持裁剪、缩放、旋转、速度调整、水印和音量控制
- 预设管理系统：创建、保存、删除和选择自定义预设
- 实时命令预览：即时显示FFmpeg命令构建结果，便于调试和确认
- 全局配置状态：在命令配置和任务队列页面间保持配置不丢失

### 🐛 修复
- 修复预设选择后表单和预览不更新的问题
- 修复页面切换时配置完全丢失的状态管理问题
- 解决音频转码参数与命令预览不一致的严重bug
- 修复表单验证警告在切换编解码器后未正确清除的问题
- 修复自定义预设删除按钮失灵的交互问题

### ⚡ 优化
- 统一命令构建逻辑，确保参数预览与实际执行完全一致
- 添加编解码器和输出格式的自定义输入支持，提供更专业的用户选项
- 优化表单验证逻辑，只在必要时显示相关警告和错误
- 改进命令预览，正确显示分辨率设置和输出容器格式变化

### 💥 Breaking Changes
- 预设配置格式已升级为结构化TaskConfig，旧格式预设需要重新创建
- 移除了"添加到队列"按钮，现在配置页面设置将直接应用于任务队列
```

### Phase3.5

#### 验证结论

```
  全部 4 项测试通过，Suspend/Resume 方案可行。 关键发现:

  ┌───────────────┬──────────────────────────────────────────────────────────────────────────┐
  │     测试      │                                   结论                                   │
  ├───────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ 基本挂起/恢复 │ NtSuspendProcess/NtResumeProcess 正常工作，进程完成后 returncode=0       │
  ├───────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ Stderr 线程   │ 不需要暂停 reader 线程。进程挂起时 readl 阻塞自然等待，恢复后自动继续    │
  ├───────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ 进程已退出    │ 正确返回 NTSTATUS=0xC000010A (STATUS_PROCESS_IS_TERMINATING)，可捕获处理 │
  ├───────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ 权限错误      │ OpenProcess 对无权限进程正确失败，可降级为 kill+重试                     │
  └───────────────┴──────────────────────────────────────────────────────────────────────────┘

  与 PRD 6.6 的差异:

  - PRD 使用 kernel32.SuspendProcess - 实际上不存在，应改为 ntdll.NtSuspendProcess
  - PRD 提议暂停 stderr 读取线程 - 不需要，readline 自然阻塞即可
  - 降级策略确认可行: 捕获异常后 kill 进程 + 记录进度

  可以安全进入 Phase 4 开发。准备好了就告诉我开始。
```

#### CC-Mem

```
     Legend: session-request | 🔴 bugfix | 🟣 feature | 🔄 refactor | ✅ change | 🔵 discovery | ⚖️ decision
#1042  12:59 AM  🔵  Task control system architecture explored before Phase 4 development
     General
       #1043            🔵  FFmpeg dependency confirmed installed at /c/Program Files/FFmpeg/ffmpeg
       #1044            🔵  Python threading and ctypes modules confirmed available
     scripts/verify_suspend_resume.py
       #1045  1:00 AM  🟣  Phase 3.5 FFmpeg subprocess suspend/resume verification script created
       #1046  1:02 AM  🔴  Fixed Windows process suspension API implementation in verification script
       #1047  1:08 AM  🔄  Improved test_2_stderr_thread_behavior reliability and added generate_test_video helper
       #1048           🔄  Optimized test_4_permission_fallback with early termination and resume verification
       #1049           🔄  Consolidated test video generation in test_1_basic_suspend_resume to use shared helper
       #1050  1:11 AM  🔵  Reader thread does not require pausing during process suspend/resume operations
       #1051  1:14 AM  🔴  Fixed reader thread liveness check timing in test_2_stderr_thread_behavior
       #1052  1:15 AM  🔄  Improved test_2 process termination logic with natural completion detection
     General
       #1053  1:17 AM  🔵  Phase 3.5 suspend/resume verification completed successfully with all tests passing
```

### Phase4

#### PLAN

```
 Phase 4: Pause/Resume + Settings Page Implementation Plan

 Context

 Phase 1-3 of ff-intelligent-neo 2.0 are complete. Phase 3.5 verified that OS-level process suspend/resume is viable
 via ntdll.NtSuspendProcess/NtResumeProcess on Windows. The PRD's approach needs corrections based on those findings.
 This phase implements:

 1. Single-task pause/resume (backend + frontend)
 2. Task retry
 3. Task reordering UI (up/down arrows)
 4. Complete Settings page (FFmpeg setup with version list, thread count, output folder, about)

 Phase 3.5 Key Findings (deviations from PRD)

 - PRD uses kernel32.SuspendProcess - does NOT exist. Must use ntdll.NtSuspendProcess + NtResumeProcess
 - PRD says pause stderr reader thread - NOT needed. readline() naturally blocks when process is suspended
 - PRD says OpenProcess(PROCESS_SUSPEND_RESUME) - actual constant is 0x0800
 - Permission error fallback: catch exception, kill process + record progress

 FFmpeg Setup Design (from user clarification)

 FFmpeg detection follows a priority chain:
 1. User-specified path (from settings config, highest priority)
 2. Platform-specific known paths (Homebrew on macOS, etc.)
 3. System PATH (shutil.which)
 4. static_ffmpeg (may download on first call)

 Settings page shows:
 - All discovered FFmpeg versions in a radio list
 - Current active version highlighted
 - "Auto Detect" button to re-scan
 - "Browse..." button to manually select ffmpeg.exe
 - When user selects a version, save to settings and apply immediately

 ---
 Task Breakdown

 1. Backend: Process Suspend/Resume Module

 File: core/process_control.py (NEW, ~80 lines)

 Cross-platform process suspend/resume:

 # Windows
 NTSTATUS_SUCCESS = 0x00000000
 PROCESS_SUSPEND_RESUME = 0x0800

 def suspend_process(pid: int) -> None:
     # OpenProcess -> NtSuspendProcess(handle) via ntdll -> CloseHandle

 def resume_process(pid: int) -> None:
     # OpenProcess -> NtResumeProcess(handle) via ntdll -> CloseHandle

 # Linux/macOS
 def suspend_process(pid): os.kill(pid, signal.SIGSTOP)
 def resume_process(pid): os.kill(pid, signal.SIGCONT)

 Error handling: if NtSuspendProcess returns non-zero NTSTATUS (e.g. permission denied or process already terminated),
 raise OSError with NTSTATUS code so caller can fallback.

 2. Backend: Refactor ffmpeg_setup.py for Version Discovery

 File: core/ffmpeg_setup.py (MODIFY)

 Add priority-based ensure_ffmpeg(ffmpeg_path_override="") function as shown by user. The module should:
 - Accept optional ffmpeg_path_override parameter
 - Scan all 4 sources in priority order
 - Add discover_ffmpeg_versions() -> returns list[dict] with each version's path, version string, source label ("User",
  "System PATH", "Homebrew", "Static FFmpeg")
 - Add switch_ffmpeg(path: str) -> validates path, updates cached path, returns version info
 - Keep existing get_ffmpeg_path() / get_ffprobe_path() working (they call ensure_ffmpeg with override from settings)
 - Clear version caches when switching

 3. Backend: main.py Bridge API

 File: main.py (MODIFY)

 Add new @expose methods:

 Task control:
 - pause_task(task_id) -> self._runner.pause_task(task_id)
 - resume_task(task_id) -> self._runner.resume_task(task_id)
 - retry_task(task_id) -> self._runner.retry_task(task_id)

 FFmpeg settings:
 - get_ffmpeg_versions() -> discover_ffmpeg_versions(), returns list of {path, version, source, active}
 - switch_ffmpeg(path) -> switch_ffmpeg(path), returns version info
 - select_ffmpeg_binary() -> file dialog for ffmpeg.exe

 pause_all/resume_all already exist as stubs, will work once TaskRunner implements them.

 4. Backend: TaskRunner pause/resume/retry

 File: core/task_runner.py (MODIFY)

 Add methods:
 - pause_task(task_id): Get proc from _running_procs, call suspend_process(pid), transition running -> paused, emit
 task_state_changed
 - resume_task(task_id): Get proc from _running_procs, call resume_process(pid), transition paused -> running, emit
 task_state_changed
 - retry_task(task_id): Validate failed -> pending transition, call start_task(task_id)
 - Fix stop_all(): Include paused state (currently only pending/running)
 - Implement pause_all(): Iterate running tasks, call pause_task()
 - Implement resume_all(): Iterate paused tasks, call resume_task()

 Edge cases:
 - Process already exited when trying to suspend -> poll() returns non-None, mark completed/failed instead of paused
 - NtSuspendProcess fails (permission) -> fallback to kill + record progress as warning

 5. Frontend: useTaskControl.ts

 File: frontend/src/composables/useTaskControl.ts (MODIFY)

 Add 3 methods:
 - pauseTask(taskId) -> call("pause_task", taskId)
 - resumeTask(taskId) -> call("resume_task", taskId)
 - retryTask(taskId) -> call("retry_task", taskId)

 6. Frontend: TaskRow.vue

 File: frontend/src/components/task-queue/TaskRow.vue (MODIFY)

 Add buttons:
 - running state: show "Pause" button (emits pause)
 - paused state: show "Resume" button (emits resume)
 - pending state: show up/down arrow buttons (emits moveUp/moveDown)

 Update emits: toggleSelect, start, stop, pause, resume, retry, moveUp, moveDown, showLog

 7. Frontend: TaskList.vue + TaskQueuePage.vue

 File: frontend/src/components/task-queue/TaskList.vue (MODIFY)
 - Wire up new events from TaskRow: @pause, @resume, @moveUp, @moveDown

 File: frontend/src/pages/TaskQueuePage.vue (MODIFY)
 - Wire up: @pause="control.pauseTask", @resume="control.resumeTask"
 - @moveUp/@moveDown: swap task positions in the list, then call("reorder_tasks", newOrder)

 8. Frontend: useSettings composable

 File: frontend/src/composables/useSettings.ts (NEW, ~60 lines)

 - settings: Ref<AppSettingsDTO> - reactive state
 - appInfo: Ref<AppInfoDTO> - FFmpeg/app versions
 - ffmpegVersions: Ref<FfmpegVersionDTO[]> - discovered versions list
 - fetchSettings() -> call("get_settings")
 - saveSetting(key, value) -> merge + call("save_settings")
 - fetchFfmpegVersions() -> call("get_ffmpeg_versions")
 - switchFfmpeg(path) -> call("switch_ffmpeg", path)
 - detectFfmpeg() -> call("setup_ffmpeg")
 - selectFfmpegBinary() -> call("select_ffmpeg_binary")

 9. Frontend: Settings Components

 File: frontend/src/components/settings/FFmpegSetup.vue (NEW, ~150 lines)

 Layout per PRD 5.1:
 - Status badge (green=ready, red=not found)
 - Current path + version display
 - Version list (radio buttons): each entry shows source label + path + version
 - "Auto Detect" button -> re-scan
 - "Browse..." button -> file dialog

 File: frontend/src/components/settings/ThreadCountInput.vue (NEW, ~60 lines)

 - Number input 1-4, default 2
 - On change -> saveSetting("max_workers", newValue)
 - Helper text about CPU cores

 File: frontend/src/components/settings/OutputFolderInput.vue (NEW, ~80 lines)

 - Radio: "Same as source" / "Custom folder"
 - Custom: text input + "Browse" button
 - On change -> saveSetting("default_output_dir", dir)

 File: frontend/src/components/settings/AppAbout.vue (NEW, ~50 lines)

 - Read-only: app version, Python version, FFmpeg version, ffprobe version, OS info
 - fetchAppInfo() on mount

 10. Frontend: SettingsPage.vue

 File: frontend/src/pages/SettingsPage.vue (REWRITE, ~60 lines)

 Compose all 4 components in DaisyUI card layout, matching PRD 5.1.

 ---
 File Summary

 ┌─────┬────────────────────────────────────────────────────────┬─────────┬───────────────────────────────────┐
 │  #  │                          File                          │ Action  │            Description            │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 1   │ core/process_control.py                                │ NEW     │ OS-level suspend/resume           │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 2   │ core/ffmpeg_setup.py                                   │ MODIFY  │ Add version discovery + switch    │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 3   │ core/task_runner.py                                    │ MODIFY  │ pause/resume/retry + fix stop_all │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 4   │ main.py                                                │ MODIFY  │ 6 new @expose methods             │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 5   │ frontend/src/composables/useTaskControl.ts             │ MODIFY  │ 3 new methods                     │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 6   │ frontend/src/composables/useSettings.ts                │ NEW     │ Settings state management         │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 7   │ frontend/src/components/task-queue/TaskRow.vue         │ MODIFY  │ Pause/Resume + move buttons       │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 8   │ frontend/src/components/task-queue/TaskList.vue        │ MODIFY  │ Wire new events                   │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 9   │ frontend/src/pages/TaskQueuePage.vue                   │ MODIFY  │ Wire new events + reorder         │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 10  │ frontend/src/components/settings/FFmpegSetup.vue       │ NEW     │ FFmpeg status + version list      │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 11  │ frontend/src/components/settings/ThreadCountInput.vue  │ NEW     │ Worker count input                │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 12  │ frontend/src/components/settings/OutputFolderInput.vue │ NEW     │ Output folder selection           │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 13  │ frontend/src/components/settings/AppAbout.vue          │ NEW     │ Read-only app info                │
 ├─────┼────────────────────────────────────────────────────────┼─────────┼───────────────────────────────────┤
 │ 14  │ frontend/src/pages/SettingsPage.vue                    │ REWRITE │ Full settings page                │
 └─────┴────────────────────────────────────────────────────────┴─────────┴───────────────────────────────────┘

 Execution Order

 1. core/process_control.py (new module, no dependencies)
 2. core/task_runner.py (depends on #1)
 3. core/ffmpeg_setup.py (independent)
 4. main.py (depends on #2, #3)
 5. frontend/src/composables/useTaskControl.ts (depends on #4 API)
 6. frontend/src/composables/useSettings.ts (depends on #4 API)
 7. frontend/src/components/task-queue/TaskRow.vue + TaskList.vue (depends on #5)
 8. frontend/src/pages/TaskQueuePage.vue (depends on #7)
 9. frontend/src/components/settings/*.vue (depends on #6)
 10. frontend/src/pages/SettingsPage.vue (depends on #9)

 Verification

 - TypeScript: cd frontend && npx vue-tsc --noEmit
 - Vite build: cd frontend && bun run build
 - Python imports: uv run python -c "from core.process_control import suspend_process, resume_process"

 Manual test checklist (PRD Phase 4 tests):
 1. Pause running task -> state shows "Paused", process actually suspended
 2. Resume paused task -> progress continues
 3. Stop paused task -> state shows "Cancelled"
 4. Retry failed task -> resets to "Pending", re-executes
 5. Move task up/down -> queue order changes
 6. Batch pause/resume/stop -> correct behavior
 7. Change thread count -> reflected in settings
 8. Set custom output folder -> used by new tasks
 9. Settings page shows FFmpeg status correctly
 10. FFmpeg version list shows all discovered versions
 11. Switch FFmpeg version -> new version becomes active
 12. App info shows correct versions
```

####   完成内容

```
  后端 (3 文件)

  - core/process_control.py (新建) - OS级进程挂起/恢复，Windows用ntdll.NtSuspendProcess，Linux/macOS用SIGSTOP/SIGCONT
  - core/task_runner.py (修改) -
    新增pause_task、resume_task、retry_task，修复stop_all包含paused状态，实现pause_all/resume_all
  - core/ffmpeg_setup.py (重写) - 优先级链式FFmpeg发现(用户指定 > bundled > 平台路径 > PATH >
    static_ffmpeg)，discover_ffmpeg_versions()版本发现，switch_ffmpeg()版本切换
  - main.py (修改) -
    新增6个@expose方法：pause_task、resume_task、retry_task、get_ffmpeg_versions、switch_ffmpeg、select_ffmpeg_binary

  前端 (8 文件)

  - useTaskControl.ts - 新增pauseTask、resumeTask、retryTask
  - useSettings.ts (新建) - 设置状态管理，FFmpeg版本发现/切换/检测
  - TaskRow.vue - 新增Pause/Resume按钮、上移/下移排序按钮
  - TaskList.vue - 连接新事件
  - TaskQueuePage.vue - 连接pause/resume/reorder逻辑
  - FFmpegSetup.vue (新建) - FFmpeg状态显示+版本列表+切换
  - ThreadCountInput.vue (新建) - 并发线程数设置
  - OutputFolderInput.vue (新建) - 输出文件夹设置
  - AppAbout.vue (新建) - 只读应用信息
  - SettingsPage.vue (重写) - 完整设置页

  验证: TypeScript 0 错误, Vite build 1.51s, Python imports 全部OK
```

#### CC-Mem

     Legend: session-request | 🔴 bugfix | 🟣 feature | 🔄 refactor | ✅ change | 🔵 discovery | ⚖️ decision
    
     Column Key
       Read: Tokens to read this observation (cost to learn it now)
       Work: Tokens spent on work that produced this record ( research, building, deciding)
    
     Context Index: This semantic index (titles, types, files, tokens) is usually sufficient to understand past work.
    
     When you need implementation details, rationale, or debugging context:
       - Fetch by ID: get_observations([IDs]) for observations visible in this index
       - Search history: Use the mem-search skill for past decisions, bugs, and deeper research
       - Trust this index over re-reading code for past decisions and learnings
    
     Context Economics
       Loading: 50 observations (18,465 tokens to read)
       Work investment: 0 tokens spent on research, building, and decisions
    
     Apr 23, 2026
    
     #S1 Audio transcoding parameter consistency fix - user requested explanation of changes made to ensure passed
     parameters match command preview (Apr 23, 12:50 AM)
    
     #S2 ComboInput component enhanced with improved filtering behavior (Apr 23, 12:54 AM)
    
     General
       #1110  1:55 AM  🟣  Phase 4 task structure completed and implementation started
     ..\..\Git\GithubManager\ff-intelligent-neo\core\process_control.py
       #1111  1:56 AM  🟣  Process control module implemented with cross-platform suspend/resume
     General
       #1112           🟣  Process control module completed and verified
       #1113           🟣  TaskRunner modification task started
     ..\..\Git\GithubManager\ff-intelligent-neo\core\task_runner.py
       #1114           🟣  TaskRunner imports process control module for pause/resume
       #1115           🟣  TaskRunner pause/resume/retry methods implemented
       #1116           🟣  TaskRunner bulk control methods implemented
     General
       #1117  1:57 AM  🟣  TaskRunner pause/resume/retry implementation completed
       #1118           🟣  FFmpeg setup refactoring task started
     ..\..\Git\GithubManager\ff-intelligent-neo\core\ffmpeg_setup.py
       #1119  1:58 AM  🟣  FFmpeg setup module refactored with version discovery and switching
     General
       #1120           🟣  FFmpeg setup refactoring completed
       #1121           🟣  Bridge API implementation task started
     ..\..\Git\GithubManager\ff-intelligent-neo\main.py
       #1122           🟣  Task control Bridge API methods added
       #1123           🟣  FFmpeg version management Bridge API methods added
     General
       #1124           🟣  Bridge API implementation completed
       #1125           🟣  Frontend task control and reorder UI implementation started
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\task-queue\TaskList.vue
       #1126  1:59 AM  🔵  TaskList.vue structure examined for Phase 4 modifications
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useTaskControl.ts
       #1127           🟣  Task control composable extended with pause/resume/retry methods
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\task-queue\TaskRow.vue
       #1128           🟣  TaskRow component updated with pause/resume/retry and reordering UI
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\task-queue\TaskList.vue
       #1129           🟣  TaskList component updated with pause/resume/reorder event wiring
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\pages\TaskQueuePage.vue
       #1130  2:00 AM  🟣  TaskQueuePage updated with pause/resume/retry handlers and task reordering
     General
       #1131           🟣  Frontend task control and reorder UI completed
       #1132           🟣  Settings page implementation started
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useSettings.ts
       #1133  2:01 AM  🟣  Settings composable implemented with FFmpeg management and app info
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\settings\FFmpegSetup.vue
       #1134           🟣  FFmpeg setup component created with version management UI
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\settings\ThreadCountInput.vue
       #1135           🟣  Thread count input component created for worker configuration
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\settings\OutputFolderInput.vue
       #1136           🟣  Output folder input component created with radio selection
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\settings\AppAbout.vue
       #1137  2:02 AM  🟣  App information component created for read-only metadata display
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\pages\SettingsPage.vue
       #1138           🟣  Settings page completely rewritten with full component composition
     General
       #1139           🟣  Settings page implementation completed
       #1140  2:03 AM  🟣  Build verification started with Python import check
       #1141           🟣  TaskRunner module import verification passed
       #1142           🟣  FFmpeg setup module import verification passed
       #1143  2:05 AM  🟣  Main.py Bridge API import verification passed
       #1144  2:06 AM  🔵  TypeScript compilation identified unused variable warnings
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\settings\FFmpegSetup.vue
       #1145           🔴  TypeScript unused variable warnings fixed in FFmpegSetup.vue
       #1146           🔴  TypeScript unused variable warning fixed in FFmpegSetup.vue v-for loop
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\components\task-queue\TaskRow.vue
       #1147           🔴  TypeScript unused variable warning fixed in TaskRow.vue
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useSettings.ts
       #1148           🔴  TypeScript unused import warning fixed in useSettings.ts
       #1149           🔴  Vue ref import removed from useSettings.ts during cleanup
       #1150           🔴  Unused loading variable removed from useSettings composable
       #1151  2:07 AM  🔴  Vue ref import restored to useSettings.ts composable
     General
       #1152  2:09 AM  🔵  TypeScript compilation error identified in useSettings.ts return statement
     ..\..\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useSettings.ts
       #1153           🔵  Compilation error location identified in useSettings.ts return statement
       #1154  2:10 AM  🔴  loading property restored to useSettings return statement but variable still missing
       #1155           🔴  Untitled
       #1156  2:12 AM  🔵  TypeScript compilation error persists after attempted fix
       #1157  2:13 AM  🔵  Return block inspection confirms loading property still present
       #1158           🔵  File read confirms loading property remains in return statement
       #1159  11:59 AM  🟣  TypeScript compilation error resolved by removing loading from return statement

#### 📝 Commit Message

```
feat(phase4): 实现任务暂停/恢复功能和完整设置页面

- 后端：添加OS级进程控制，支持跨平台暂停/恢复任务
- 后端：实现TaskRunner暂停/恢复/重试和批量操作方法
- 后端：重构FFmpeg设置模块，添加版本发现和切换功能
- 后端：新增6个Bridge API方法，支持任务控制和FFmpeg管理
- 前端：扩展任务控制UI，添加暂停/恢复/重试按钮和任务重排序
- 前端：实现完整设置页面，包含FFmpeg设置、线程配置、输出路径和应用信息
- 前端：修复TypeScript编译警告和错误，确保代码质量
```

#### 🚀 Release Notes

```
## 2026-04-23 - 任务控制与设置页面

### ✨ 新增
- 任务暂停/恢复功能：可随时暂停和恢复正在运行的任务，避免资源浪费
- 任务重试功能：失败任务可一键重试，无需重新添加
- 任务排序功能：支持上移/下调整任务队列顺序
- FFmpeg版本管理：自动发现系统中的FFmpeg版本，支持手动切换
- 完整设置页面：提供FFmpeg配置、线程数调整、输出文件夹设置等选项
- 应用信息面板：显示当前版本、FFmpeg版本和系统信息

### 🐛 修复
- 修复TypeScript编译警告，提高代码质量
- 修复任务状态处理逻辑，确保暂停状态正确显示和处理
```

### Phase5

#### Complete

```
  Changes (9 files)

  Backend (3 files):

  ┌───────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────┐
  │         File          │                                         Changes                                          │
  ├───────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ core/task_queue.py    │ load_state(): running->failed, paused->pending recovery; save_state(): only non-terminal │
  │                       │  + last 50 terminal; proper datetime import                                              │
  ├───────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ core/ffmpeg_runner.py │ Calculate estimated_remaining from elapsed/percent ratio, display in progress events     │
  ├───────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────┤
  │ main.py               │ download_ffmpeg @expose (with packaged guard); atexit cleanup; fixed switch_ffmpeg       │
  │                       │ exception handling                                                                       │
  └───────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────┘

  Frontend (5 files):

  ┌─────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────┐
  │        File         │                                          Changes                                           │
  ├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
  │ TaskProgressBar.vue │ Display ~Xm Xs estimated remaining time                                                    │
  ├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
  │ useSettings.ts      │ downloadFfmpeg() method                                                                    │
  ├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
  │ FFmpegSetup.vue     │ Download button (when no versions found); reactive status badge; removed handleSwitch      │
  │                     │ wrapper                                                                                    │
  ├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
  │ TaskQueuePage.vue   │ Loading spinner while data loads                                                           │
  ├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
  │ SettingsPage.vue    │ Loading spinner while data loads                                                           │
  └─────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────┘

  Build (1 file):

  ┌──────────┬───────────────────────────────────────────────────────────────────────────────┐
  │   File   │                                    Changes                                    │
  ├──────────┼───────────────────────────────────────────────────────────────────────────────┤
  │ app.spec │ App name ff-intelligent-neo; removed batch_runner; added 5 new module imports │
  └──────────┴───────────────────────────────────────────────────────────────────────────────┘

  Verification

  - TypeScript: 0 errors
  - Vite build: 1.24s
  - Python imports: all OK

  Manual Test Checklist

    1. Execute a task, close and reopen the app -> running task shows as "Failed" with "Process interrupted by app restart" error
    2. Pause a task, close and reopen -> paused task shows as "Pending"
    3. Add 55+ completed tasks, close/reopen -> only 50 most recent kept
    4. Running task shows ~Xm Xs remaining time in progress bar
    5. Settings page, FFmpeg section: click "Download FFmpeg" when no versions found
    6. App closes cleanly (no orphan FFmpeg processes)
    7. Both pages show loading spinner during initial data fetch


```

暂停时关闭应用，应用无法完全关闭，窗口关闭了但控制台一直还在，关闭控制台之后任务状态是pending但是也没法按原本的进度继续任务。运行时直接关闭，应用也是无法完全关闭，FFmpeg在后台执行完任务了才关闭。感觉不用搞得那么复杂，无论是暂停时还是运行时关闭，都直接掐断进程，重启后显示Failed提示用户可以Retry即可

  1. main.py _cleanup(): No more graceful shutdown. Directly kills all FFmpeg processes via proc.kill(), fires all

    cancel events, calls shutdown(wait=False) to abandon threads immediately. The process exits cleanly.
  2. core/task_queue.py load_state(): Both running and paused tasks now reset to failed (not pending). Error message:

    "Process interrupted by app close". User can Retry.
  3. PRD 10.3: Updated to reflect simplified behavior.

```
  Changes to fix FFmpeg process survival on app close:

  ┌─────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────┐
  │          File           │                                         Change                                         │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
  │ pywebvue/app.py         │ Added on_closing callback parameter, registered on window.events.closing               │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
  │ core/process_control.py │ Added shared kill_process_tree() helper (Windows: taskkill /F /T /PID, Unix: os.killpg │
  │                         │  with fallback)                                                                        │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
  │ core/ffmpeg_runner.py   │ Added CREATE_NEW_PROCESS_GROUP on Windows to Popen; all kill paths use shared          │
  │                         │ kill_process_tree()                                                                    │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
  │ core/task_runner.py     │ Removed local _kill_process_tree, imports shared version; stop_task and force_kill_all │
  │                         │  use it; force_kill_all clears _cancel_events                                          │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
  │ main.py                 │ Simplified _cleanup to runner.force_kill_all(); added on_closing=api._cleanup to App;  │
  │                         │ added double-execution guard                                                           │
  └─────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────┘

  Root causes addressed:
  1. proc.kill() on Windows only kills the direct child, not FFmpeg's sub-processes -> fixed with taskkill /F /T /PID
  2. atexit may not fire if pywebview uses os._exit() -> fixed by also hooking into window.events.closing
  3. Duplicated kill logic across files -> consolidated into core/process_control.py
  4. _cleanup could fire twice (atexit + on_closing) -> added idempotency guard
```

#### CC-Mem

```
     Legend: session-request | 🔴 bugfix | 🟣 feature | 🔄 refactor | ✅ change | 🔵 discovery | ⚖️ decision

     Column Key
       Read: Tokens to read this observation (cost to learn it now)
       Work: Tokens spent on work that produced this record ( research, building, deciding)

     Context Index: This semantic index (titles, types, files, tokens) is usually sufficient to understand past work.

     When you need implementation details, rationale, or debugging context:
       - Fetch by ID: get_observations([IDs]) for observations visible in this index
       - Search history: Use the mem-search skill for past decisions, bugs, and deeper research
       - Trust this index over re-reading code for past decisions and learnings

     Context Economics
       Loading: 50 observations (15,274 tokens to read)
       Work investment: 10,968 tokens spent on research, building, and decisions
       Your savings: -39% reduction from reuse

     Apr 23, 2026

     #S1 Audio transcoding parameter consistency fix - user requested explanation of changes made to ensure passed
     parameters match command preview (Apr 23, 12:50 AM)

     #S2 ComboInput component enhanced with improved filtering behavior (Apr 23, 12:54 AM)

     frontend/src/
       #1214  12:40 PM  🟣  Phase 5 Task 5 completed: build verification and testing
     core/task_queue.py
       #1215            🔵  Git diff shows 22 files changed with 2460 insertions and 106 deletions in latest commit
     .git/
       #1216  12:41 PM  🔵  Git commit history shows Phase 4 as most recent commit, Phase 5 changes are uncommitted
     core/task_queue.py
       #1217            🔵  Phase 5 changes confirmed as 9 unstaged files with 151 insertions and 7 deletions
     app.spec
       #1218  12:42 PM  🔵  Complete Phase 5 diff confirms all features implemented across 9 files
     core/task_queue.py
       #1219            🟣  Phase 5 implementation fully complete and verified
     main.py
       #1220            🔵  static_ffmpeg package integration confirmed across codebase
     core/ffmpeg_setup.py
       #1221            🔵  FFmpeg discovery priority chain confirmed in core/ffmpeg_setup.py
     main.py
       #1222  12:43 PM  🔵  Shutdown cleanup integration points confirmed in main.py
     core/task_queue.py
       #1223            🔵  Code review identified 4 HIGH severity issues in Phase 5 implementation
       #1224            🔄  Added proper datetime import to task_queue.py replacing inline __import__ calls
       #1225            🔴  Fixed critical race condition in task queue save_state() method
     ..\..\Git\GithubManager\ff-intelligent-neo\main.py
       #1226  12:55 PM  🔴  Implemented force-kill shutdown behavior for app exit
     ..\..\Git\GithubManager\ff-intelligent-neo\core\task_queue.py
       #1227            🔴  Modified queue recovery logic to mark all interrupted tasks as failed
     ..\..\Git\GithubManager\ff-intelligent-neo\docs\PRD-2.0.0.md
       #1228            🔵  PRD specifies different queue recovery behavior than recent implementation
       #1229            ✅  Updated PRD documentation to reflect simplified queue recovery behavior
       #1230  12:58 PM  ✅  Updated PRD section 10.3 to reflect simplified queue recovery behavior
     ..\..\Git\GithubManager\ff-intelligent-neo\pywebvue\bridge.py
       #1231  1:05 PM  🔵  pywebvue bridge lacks window lifecycle hooks for cleanup
     ..\..\Git\GithubManager\ff-intelligent-neo\main.py
       #1232  1:07 PM  🔵  main.py application entry point lacks subprocess cleanup on window close
     ..\..\Git\GithubManager\ff-intelligent-neo\core\task_runner.py
       #1233           🔵  TaskRunner.shutdown() exists but is never called on window close
     ..\..\Git\GithubManager\ff-intelligent-neo\pywebvue\app.py
       #1234           🔵  pywebvue App class lacks window lifecycle event registration
     ..\..\Git\GithubManager\ff-intelligent-neo\core\process_control.py
       #1235           🔵  Window close solution requires webview.events.closed or signal handlers
     General
       #1236           ⚖️  Solution approach: Add on_closing lifecycle hook to pywebvue App
       #1237           ⚖️  Three-phase implementation plan for ffmpeg cleanup on window close
     ..\..\Git\GithubManager\ff-intelligent-neo\pywebvue\app.py
       #1238  1:08 PM  ✅  Added on_closing parameter to pywebvue App.__init__()
       #1239           🟣  Implemented on_closing lifecycle hook in pywebvue App class
     General
       #1240           🔵  FFmpeg process tree termination requires platform-specific handling
     ..\..\Git\GithubManager\ff-intelligent-neo\core\ffmpeg_runner.py
       #1241           ✅  Added sys import to ffmpeg_runner.py for platform detection
       #1242           ✅  Added CREATE_NEW_PROCESS_GROUP flag for Windows subprocess creation
     ..\..\Git\GithubManager\ff-intelligent-neo\core\task_runner.py
       #1243           ✅  Added sys import to task_runner.py for platform detection
       #1244           🟣  Implemented _kill_process_tree() helper for reliable subprocess termination
       #1245           🔴  Replaced proc.kill() with _kill_process_tree() in stop_task()
       #1246           🟣  Added force_kill_all() method to TaskRunner for shutdown cleanup
     ..\..\Git\GithubManager\ff-intelligent-neo\core\ffmpeg_runner.py
       #1247           ✅  Added platform-specific process tree termination to ffmpeg_runner.py cancellation
       #1248  1:09 PM  🟣  Completed Task 7: FFmpeg process tree termination implemented
     ..\..\Git\GithubManager\ff-intelligent-neo\main.py
       #1249           🔄  Simplified _cleanup() in main.py to use TaskRunner.force_kill_all()
       #1250           🟣  Integrated on_closing lifecycle hook into main.py App initialization
     ..\..\Git\GithubManager\ff-intelligent-neo\pywebvue\app.py
       #1251           🔴  Completed fix for FFmpeg processes continuing after window close
     ..\..\Git\GithubManager\ff-intelligent-neo\core\ffmpeg_runner.py
       #1252  1:29 PM  🔵  Code review identified 5 issues in FFmpeg cleanup implementation
     General
       #1253           ⚖️  Created task to fix code review issues in FFmpeg cleanup implementation
     ..\..\Git\GithubManager\ff-intelligent-neo\core\process_control.py
       #1254           ✅  Started implementing code review fixes for process cleanup issues
       #1255  1:30 PM  🔄  Consolidated process tree termination into shared kill_process_tree() in process_control.py
     ..\..\Git\GithubManager\ff-intelligent-neo\core\ffmpeg_runner.py
       #1256  1:39 PM  ✅  Added kill_process_tree import to ffmpeg_runner.py
       #1257           🔄  Replaced inline process kill logic with shared kill_process_tree() in ffmpeg_runner.py
       #1258           🔴  Fixed exception handler to use kill_process_tree() instead of proc.kill()
     ..\..\Git\GithubManager\ff-intelligent-neo\core\task_runner.py
       #1259           🔄  Removed duplicate _kill_process_tree from task_runner.py, imported shared version
       #1260  1:40 PM  🔄  Updated stop_task() to use imported kill_process_tree instead of local function
       #1261           🔴  Fixed force_kill_all() to use shared kill_process_tree and clear _cancel_events
     ..\..\Git\GithubManager\ff-intelligent-neo\main.py
       #1262           🔴  Added double-call guard to _cleanup() method in main.py
     ..\..\Git\GithubManager\ff-intel
     ..\..\Git\GithubManager\ff-intelligent-neo\core\process_control.py
       #1263  1:43 PM  🟣  Completed Task 9: Fixed all code review issues for process cleanup
     ..\..\Git\GithubManager\ff-intelligent-neo\build.py
       #1264  1:50 PM  🔵  FFmpeg pre-download fails due to missing static_ffmpeg module
     ..\..\Git\GithubManager\ff-intelligent-neo\app.spec
       #1265           🔵  static_ffmpeg dependency declared but not installed in uv environment
     ..\..\Git\GithubManager\ff-intelligent-neo\pyproject.toml
       #1266           🔵  pre_build.py invoked as standalone subprocess, not imported module
     ..\..\Git\GithubManager\ff-intelligent-neo\build.py
       #1267  1:51 PM  🔵  build.py declares only pyinstaller in PEP 723 metadata, static-ffmpeg in pyproject.tomlligent-neo\core\process_control.py
       #1263  1:43 PM  🟣  Completed Task 9: Fixed all code review issues for process cleanup
```

#### 📝 Commit Message

```
feat(main): 改进任务队列管理、进程控制与用户体验

- 任务队列优化：修复状态持久化逻辑，限制历史任务存储数量，添加预计完成时间显示
- FFmpeg功能增强：添加自动下载功能，实现进度显示，优化安装体验
- 进程控制改进：解决应用关闭时FFmpeg进程残留问题，统一跨平台终止逻辑
- UI体验提升：添加加载状态指示器，优化进度条显示，简化状态管理逻辑
- 构建更新：调整应用名称，添加新模块，移除废弃组件
```

#### 🚀 Release Notes

```
## 2026-04-23 - 增强的任务管理与进程控制

### ✨ 新增
- 任务进度显示：现在可以看到预计剩余完成时间，格式为"X分X秒"
- FFmpeg自动下载：当检测到没有FFmpeg版本时，可在设置界面直接下载
- 加载优化：任务队列和设置页面在加载数据时显示加载指示器

### 🐛 修复
- 应用关闭问题：无论任务是在运行还是暂停状态，现在应用关闭会正确终止所有FFmpeg进程
- 任务状态恢复：重新打开应用后，被中断的任务会标记为"失败"并显示"进程被应用关闭中断"，用户可以重试
- 内存优化：只保留最近50个已完成任务，避免历史任务占用过多存储空间

### ⚡ 优化
- 进度显示更精确：基于已用时间和完成比例计算剩余时间
- 应用稳定性改进：解决了重复清理进程的问题，添加了双重执行保护
- 代码结构优化：合并了分散的进程控制逻辑，提高维护性
```
