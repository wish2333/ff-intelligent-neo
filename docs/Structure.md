# 系统架构

## 系统架构总览

```mermaid
graph TB
    subgraph "表示层 Presentation Layer"
        Vue[Vue 3 + TypeScript]
        DaisyUI[DaisyUI v5 + Tailwind CSS v4]
        Router[Vue Router 4 - Hash Mode]
        Composables[Composables 组合式函数]
    end

    subgraph "桥接层 Bridge Layer"
        Expose["@expose 装饰器"]
        Emit["_emit 事件发射"]
        WebView[pywebview 窗口]
    end

    subgraph "业务层 Business Layer"
        Main[main.py - FFmpegApi]
        TaskRunner[TaskRunner 任务执行器]
        TaskQueue[TaskQueue 任务队列]
        CmdBuilder[CommandBuilder 命令构建器]
        FFmpegRunner[FFmpegRunner 进程管理]
        ProcessCtrl[ProcessControl 进程控制]
        Config[Config 配置管理]
        PresetMgr[PresetManager 预设管理]
        FileInfo[FileInfo 文件探测]
        FFmpegSetup[FFmpegSetup 二进制管理]
    end

    subgraph "外部依赖 External"
        FFmpeg[FFmpeg 进程]
        FFprobe[FFprobe 进程]
        FileSystem[文件系统 JSON 持久化]
    end

    Vue --> Composables
    Composables --> Expose
    Expose --> Main
    Main --> TaskRunner
    Main --> TaskQueue
    Main --> Config
    Main --> PresetMgr
    Main --> FFmpegSetup
    Main --> CmdBuilder
    TaskRunner --> FFmpegRunner
    TaskRunner --> CmdBuilder
    TaskRunner --> TaskQueue
    FFmpegRunner --> ProcessCtrl
    FFmpegRunner --> FFmpeg
    FileInfo --> FFprobe
    TaskQueue --> FileSystem
    Config --> FileSystem
    PresetMgr --> FileSystem
    FFmpegSetup --> FileSystem

    Main --> Emit
    Emit --> WebView
    WebView --> Vue
```

## 模块依赖关系

```mermaid
graph LR
    main[main.py] --> pywebvue_app[pywebvue/app.py]
    main --> pywebvue_bridge[pywebvue/bridge.py]
    main --> task_runner[task_runner.py]
    main --> task_queue[task_queue.py]
    main --> config[config.py]
    main --> preset_mgr[preset_manager.py]
    main --> ffmpeg_setup[ffmpeg_setup.py]
    main --> file_info[file_info.py]
    main --> command_builder[command_builder.py]
    main --> logging[logging.py]

    task_runner --> ffmpeg_runner[ffmpeg_runner.py]
    task_runner --> command_builder
    task_runner --> task_queue
    task_runner --> ffmpeg_setup
    task_runner --> process_control[process_control.py]
    task_runner --> models

    task_queue --> models
    ffmpeg_runner --> process_control
    ffmpeg_runner --> models
    command_builder --> models
    file_info --> ffmpeg_setup
    config --> models
    preset_mgr --> models

    models[models.py] -.-> "数据定义" task_runner
    models -.-> "数据定义" task_queue
```

## 前端组件层级

```mermaid
graph TD
    App["App.vue<br/>根组件"]
    Navbar["AppNavbar.vue<br/>导航栏"]

    App --> Navbar

    subgraph "路由页面"
        TaskQueuePage["TaskQueuePage.vue<br/>任务队列页"]
        CommandConfigPage["CommandConfigPage.vue<br/>命令配置页"]
        SettingsPage["SettingsPage.vue<br/>设置页"]
    end

    App --> TaskQueuePage
    App --> CommandConfigPage
    App --> SettingsPage

    subgraph "任务队列组件"
        TaskToolbar["TaskToolbar.vue<br/>工具栏"]
        BatchControlBar["BatchControlBar.vue<br/>批量控制"]
        QueueSummary["QueueSummary.vue<br/>队列摘要"]
        TaskList["TaskList.vue<br/>任务列表"]
        TaskLogPanel["TaskLogPanel.vue<br/>日志面板"]
        TaskRow["TaskRow.vue<br/>任务行"]
        TaskProgressBar["TaskProgressBar.vue<br/>进度条"]
    end

    TaskQueuePage --> TaskToolbar
    TaskQueuePage --> BatchControlBar
    TaskQueuePage --> QueueSummary
    TaskQueuePage --> TaskList
    TaskQueuePage --> TaskLogPanel
    TaskList --> TaskRow
    TaskRow --> TaskProgressBar

    subgraph "命令配置组件"
        PresetSelector["PresetSelector.vue<br/>预设选择器"]
        TranscodeForm["TranscodeForm.vue<br/>转码参数表单"]
        FilterForm["FilterForm.vue<br/>滤镜参数表单"]
        CommandPreview["CommandPreview.vue<br/>命令预览"]
        PresetEditor["PresetEditor.vue<br/>预设编辑器"]
        ComboInput["ComboInput.vue<br/>组合输入框"]
    end

    CommandConfigPage --> PresetSelector
    CommandConfigPage --> TranscodeForm
    CommandConfigPage --> FilterForm
    CommandConfigPage --> CommandPreview
    CommandConfigPage --> PresetEditor
    TranscodeForm --> ComboInput
    FilterForm --> ComboInput

    subgraph "设置页组件"
        FFmpegSetup["FFmpegSetup.vue<br/>FFmpeg 配置"]
        OutputFolderInput["OutputFolderInput.vue<br/>输出目录"]
        ThreadCountInput["ThreadCountInput.vue<br/>线程数设置"]
        AppAbout["AppAbout.vue<br/>关于"]
    end

    SettingsPage --> FFmpegSetup
    SettingsPage --> OutputFolderInput
    SettingsPage --> ThreadCountInput
    SettingsPage --> AppAbout
```

## 数据流架构

### 请求流（前端 -> 后端）

```mermaid
sequenceDiagram
    participant User as 用户
    participant Component as Vue 组件
    participant Composable as Composable
    participant Bridge as PyWebVue Bridge
    participant API as Python @expose
    participant Core as Core 模块

    User->>Component: 用户操作 (点击/输入)
    Component->>Composable: 调用方法
    Composable->>Bridge: window.pywebview.api.xxx()
    Bridge->>API: 调用暴露方法
    API->>Core: 执行业务逻辑
    Core-->>API: 返回结果
    API-->>Bridge: {success, data, error}
    Bridge-->>Composable: 响应数据
    Composable-->>Component: 更新响应式状态
    Component-->>User: UI 更新
```

### 事件流（后端 -> 前端）

```mermaid
sequenceDiagram
    participant Core as Core 模块
    participant Emit as _emit()
    participant WebView as pywebview
    participant Bridge as useBridge
    participant Composable as Composable
    participant Component as Vue 组件

    Core->>Emit: 事件发射 (task_progress)
    Emit->>WebView: JS 调用队列
    WebView->>Bridge: 定时刷新 (50ms tick)
    Bridge->>Composable: 事件回调触发
    Composable->>Composable: 更新响应式数据
    Composable-->>Component: 自动响应式更新
```

## 前端路由结构

| 路径 | 组件 | 说明 |
|------|------|-----|
| `/` | - | 重定向到 `/task-queue` |
| `/task-queue` | `TaskQueuePage.vue` | 任务队列管理 |
| `/command-config` | `CommandConfigPage.vue` | 命令配置 |
| `/settings` | `SettingsPage.vue` | 应用设置 |

使用 Hash 模式（`/#/task-queue`），兼容 pywebview 环境。

## Composable 职责分配

| Composable | 职责 | 管理的状态 |
|-----------|------|-----------|
| `useBridge` | 事件监听管理 | 事件监听器注册/注销 |
| `useSettings` | 应用设置读写 | max_workers, output_dir, ffmpeg_path, ffprobe_path |
| `useTaskQueue` | 任务队列操作 | tasks 列表, drag-drop 状态 |
| `useTaskControl` | 单任务/批量控制 | 无自有状态, 调用 API |
| `useTaskProgress` | 进度/日志追踪 | progress_map, logs_map |
| `useCommandPreview` | 命令预览生成 | command, validation errors/warnings |
| `usePresets` | 预设管理 | presets 列表, 当前预设 |
| `useGlobalConfig` | 全局配置状态 | 当前 TaskConfig |
| `useFileDrop` | 拖拽文件处理 | is_dragging 状态 |

## 文件结构说明

### 后端文件

```
core/
├── models.py            # 数据模型定义
│   ├── TaskState        # 任务状态类型 (Literal)
│   ├── VALID_TRANSITIONS # 合法状态转移映射
│   ├── TranscodeConfig   # 转码参数配置 (frozen dataclass)
│   ├── FilterConfig      # 滤镜参数配置 (frozen dataclass)
│   ├── TaskConfig        # 任务完整配置 (frozen dataclass)
│   ├── TaskProgress      # 任务进度快照 (frozen dataclass)
│   ├── Task              # 任务实体 (mutable class)
│   ├── Preset            # 预设配置 (frozen dataclass)
│   └── AppSettings       # 应用设置 (frozen dataclass)
│
├── task_queue.py        # 线程安全任务队列
│   ├── TaskQueue        # 队列管理器 (RLock, Timer)
│   ├── CRUD 操作        # add/remove/get/reorder
│   ├── 状态机           # transition_task()
│   ├── 持久化           # save_state()/load_state()
│   └── 防抖保存         # 0.5s debounce
│
├── task_runner.py       # 任务执行引擎
│   ├── TaskRunner       # 执行协调器
│   ├── ThreadPool       # 并发执行 (max_workers)
│   ├── 进程追踪         # _running_procs, _cancel_events
│   └── 批量控制         # stop_all/pause_all/resume_all
│
├── ffmpeg_runner.py     # FFmpeg 进程管理
│   ├── run_single()     # 执行单条命令
│   ├── 进度解析         # stderr 正则解析 (time/speed/fps)
│   └── 进度回调         # 0.5s 间隔进度更新
│
├── command_builder.py   # FFmpeg 命令构建
│   ├── build_command()  # 从 TaskConfig 构建 FFmpeg 命令
│   ├── build_output_path() # 生成输出文件路径
│   └── 滤镜链排序       # 按优先级自动排序
│
├── process_control.py   # 跨平台进程控制
│   ├── kill_process_tree() # 进程树终止
│   ├── suspend_process()   # 进程暂停 (Windows/Linux/macOS)
│   └── resume_process()    # 进程恢复
│
├── config.py            # 设置持久化
├── preset_manager.py    # 预设管理
├── ffmpeg_setup.py      # FFmpeg 二进制管理
├── file_info.py         # 文件探测 (ffprobe)
├── app_info.py          # 应用元信息
└── logging.py           # 日志配置 (loguru)

pywebvue/
├── app.py               # 窗口管理 + 事件系统
├── bridge.py            # @expose 装饰器 + Bridge 基类
└── __init__.py

main.py                  # 应用入口 + FFmpegApi (Bridge)
```

### 前端文件

```
frontend/src/
├── main.ts              # Vue 应用入口
├── App.vue              # 根组件 (Navbar + router-view)
├── bridge.ts            # 后端通信封装
├── router.ts            # 路由配置 (Hash 模式)
├── style.css            # 全局样式 (Tailwind)
│
├── pages/               # 页面组件
│   ├── TaskQueuePage.vue
│   ├── CommandConfigPage.vue
│   └── SettingsPage.vue
│
├── components/          # 子组件
│   ├── layout/AppNavbar.vue
│   ├── common/ComboInput.vue
│   ├── config/          # 配置相关组件
│   ├── settings/        # 设置相关组件
│   └── task-queue/      # 队列相关组件
│
├── composables/         # 组合式函数
│   ├── useBridge.ts
│   ├── useSettings.ts
│   ├── useTaskQueue.ts
│   ├── useTaskControl.ts
│   ├── useTaskProgress.ts
│   ├── useCommandPreview.ts
│   ├── usePresets.ts
│   ├── useGlobalConfig.ts
│   └── useFileDrop.ts
│
├── types/               # TypeScript 类型定义
│   ├── task.ts
│   ├── config.ts
│   ├── preset.ts
│   └── settings.ts
│
└── utils/
    └── format.ts        # 格式化工具函数
```

## Bridge API 接口清单

### 任务管理

| 方法 | 说明 |
|------|-----|
| `select_files()` | 打开文件选择对话框 |
| `select_output_dir()` | 打开目录选择对话框 |
| `add_tasks(paths, config?)` | 添加任务到队列 |
| `remove_tasks(task_ids)` | 删除任务 |
| `reorder_tasks(task_ids)` | 重排任务顺序 |
| `get_tasks()` | 获取所有任务 |
| `get_queue_summary()` | 获取队列统计 |
| `clear_completed()` | 清除已完成任务 |
| `clear_all()` | 清除所有任务 |

### 任务控制

| 方法 | 说明 |
|------|-----|
| `start_task(task_id)` | 开始任务 |
| `stop_task(task_id)` | 停止任务 |
| `pause_task(task_id)` | 暂停任务 |
| `resume_task(task_id)` | 恢复任务 |
| `retry_task(task_id)` | 重试失败任务 |
| `stop_all()` | 停止所有任务 |
| `pause_all()` | 暂停所有运行中任务 |
| `resume_all()` | 恢复所有暂停任务 |

### 设置与配置

| 方法 | 说明 |
|------|-----|
| `get_settings()` | 获取应用设置 |
| `save_settings(settings)` | 保存应用设置 |
| `build_command(config)` | 构建 FFmpeg 命令 |
| `validate_config(config)` | 验证配置 |

### FFmpeg 管理

| 方法 | 说明 |
|------|-----|
| `setup_ffmpeg()` | 确保 FFmpeg 可用 |
| `get_ffmpeg_versions()` | 获取 FFmpeg 版本信息 |
| `switch_ffmpeg(path)` | 切换 FFmpeg 二进制路径 |
| `select_ffmpeg_binary()` | 选择 FFmpeg 文件 |
| `download_ffmpeg()` | 下载 FFmpeg |

### 预设管理

| 方法 | 说明 |
|------|-----|
| `get_presets()` | 获取所有预设 |
| `save_preset(preset)` | 保存预设 |
| `delete_preset(preset_id)` | 删除预设 |

### 后端事件

| 事件名 | 触发时机 |
|-------|---------|
| `task_added` | 任务添加到队列 |
| `task_state_changed` | 任务状态变更 |
| `task_progress` | 任务进度更新 |
| `task_log` | 任务日志输出 |
| `queue_changed` | 队列内容变更 |
| `batch_complete` | 批量处理完成 |
