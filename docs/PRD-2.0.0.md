# ff-intelligent-neo 2.0.0 - 产品需求文档

> 版本: 2.0.0
> 日期: 2026-04-22
> 状态: Draft

---

## 1. 项目概述

### 1.1 项目背景

ff-intelligent-neo 是一款基于 PyWebVue 的桌面端 FFmpeg 批量处理工具。1.x 版本为单页面应用，功能集中在文件选择、预设选择和批量转码。2.0.0 版本将进行架构级重构，引入多页面导航、组件化设计、精细任务控制和结构化配置系统。

### 1.2 版本目标

- 前端从单页改为多页面+组件化架构
- 任务系统从"一次性批量"升级为可独立控制的任务队列
- FFmpeg 配置从模板字符串升级为结构化参数
- 新增软件配置页面（线程数、输出目录、FFmpeg管理）
- 支持任务状态持久化，重启后恢复

### 1.3 技术栈（不变）

| 层级 | 技术 |
|------|------|
| 桌面容器 | pywebview |
| 前端框架 | Vue 3 + TypeScript |
| 构建工具 | Vite 6 |
| UI框架 | DaisyUI v5 + Tailwind CSS v4 |
| 路由 | vue-router (hash模式) |
| 后端语言 | Python 3.11+ |
| 桥接通信 | PyWebVue (Bridge + @expose + _emit) |
| 打包 | PyInstaller |

### 1.4 不兼容说明

2.0.0 为全新架构，不兼容 1.x 的预设文件和配置数据。用户需重新配置。

### 1.5 PyWebVue 框架更新

在开发 2.0.0 之前，需要先更新 PyWebVue 框架（已完成）。以下更新对本项目有直接影响：

| 更新 | 对本项目的影响 |
|------|---------------|
| **线程安全 `_emit`** | 核心修复。任务进度从工作线程发送，旧的直接调用 `evaluate_js` 会在 Windows 上触发 COM 违规导致崩溃。新版改为队列模式，由主线程定时器统一刷新，最大延迟 50ms（可配置） |
| **`get_dropped_files` 添加 `@expose`** | Bug 修复。拖拽文件功能之前缺少错误包装，异常时会崩溃而非返回错误信息 |
| **`register_handler` + `run_on_main_thread`** | 预留能力。当前任务场景中暂不需要，但如果未来需要从后台线程操作 pywebview API（如弹出对话框），可直接使用 |
| **`tick_interval` 参数** | 可配置事件刷新频率。默认 50ms，对本项目进度上报足够 |
| **`on_start` 回调** | 预创建钩子。当前不需要，但为未来 DLL 预加载等场景预留 |

**已更新的框架文件：**
- `pywebvue/bridge.py` -- 线程安全 `_emit`、handler 注册、`run_on_main_thread`、`@expose` 修复
- `pywebvue/app.py` -- `tick_interval`、`on_start`、单定时器 `_tick`、`_setup_bridge`

---

## 2. 页面结构与导航

### 2.1 导航栏

应用顶部固定导航栏，包含以下元素：

| 位置 | 元素 | 说明 |
|------|------|------|
| 左侧 | 应用名称 + Logo | "FF Intelligent Neo" |
| 中间 | 页面导航标签 | 任务队列 / 命令配置 / 软件配置 |
| 右侧 | FFmpeg 状态指示器 | 显示当前 FFmpeg 版本和可用状态 |

### 2.2 页面路由

```
/              -> 重定向到 /task-queue
/task-queue    -> 任务队列页面
/command-config -> 命令配置页面
/settings      -> 软件配置页面
```

路由使用 hash 模式（`#/task-queue`），兼容 pywebview 的 file:// 和 dev server。

---

## 3. 页面一：任务队列

### 3.1 页面布局

```
+------------------------------------------------------------------+
| TaskToolbar                                                       |
| [添加文件] [移除选中] [清空已完成] [清空全部]                        |
| [批量: 全部暂停 | 全部恢复 | 全部停止]                              |
+------------------------------------------------------------------+
| QueueSummary                                                      |
| 待执行: 3 | 执行中: 1 | 已暂停: 0 | 已完成: 5 | 失败: 1           |
+------------------------------------------------------------------+
| TaskList (可滚动)                                                  |
| +--------------------------------------------------------------+ |
| | [x] TaskRow: video1.mp4 | 1920x1080 | 待执行   | [开始]       | |
| | [x] TaskRow: video2.mp4 | 1280x720  | 执行中   | [暂停][停止] | |
| |     progress: 38%  00:12/01:05  speed=2.5x  fps=30          | |
| | [ ] TaskRow: video3.mp4 | 3840x2160 | 已暂停   | [恢复][停止] | |
| | [ ] TaskRow: video4.mp4 | 1920x1080 | 已完成   | output.mp4  | |
| | [ ] TaskRow: video5.mp4 | 1920x1080 | 失败     | [重试] 错误..| |
| +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
| TaskLogPanel (展开/收起，显示选中任务的日志)                          |
+------------------------------------------------------------------+
```

### 3.2 任务添加

- 点击"添加文件"打开系统文件选择对话框，支持多选
- 支持拖拽文件到任务列表区域
- 支持的媒体格式由后端 `file_info.py` 的 ffprobe 检测决定（不硬编码扩展名列表）
- 添加文件时使用当前 FFmpeg 配置页的转码+滤镜设置作为任务配置
- 添加后自动探测文件元信息（时长、分辨率、编码格式等），显示在任务行中

### 3.3 任务列表

每行任务 (TaskRow) 显示以下信息：

| 列 | 内容 |
|----|------|
| 多选框 | checkbox，支持全选 |
| 文件名 | 带图标的文件名 |
| 元信息 | 分辨率、时长、大小 |
| 状态徽章 | 彩色标签标识当前状态 |
| 进度条 | 执行中时显示进度百分比 |
| 详细进度 | 当前时间/总时长、速度、帧率 |
| 操作按钮 | 根据状态显示不同按钮 |

### 3.4 任务状态

任务具有以下状态，状态转换规则如下：

```
pending  -> running    (开始执行)
pending  -> cancelled  (停止)
running  -> paused     (暂停)
running  -> completed  (正常完成)
running  -> failed     (执行出错)
running  -> cancelled  (停止)
paused   -> running    (恢复)
paused   -> cancelled  (停止)
failed   -> pending    (重试)
completed -> (终态，不可转换)
cancelled -> (终态，不可转换)
```

### 3.5 任务控制

#### 单任务操作

| 操作 | 条件 | 行为 |
|------|------|------|
| 开始 | 状态为 pending | 将任务提交到线程池执行 |
| 暂停 | 状态为 running | 挂起任务对应的线程/进程 |
| 恢复 | 状态为 paused | 恢复挂起的线程/进程继续执行 |
| 停止 | 状态为 pending/running/paused | 终止任务，状态设为 cancelled |
| 重试 | 状态为 failed | 重置任务状态为 pending，重新排队 |

#### 批量操作

| 操作 | 行为 |
|------|------|
| 全部暂停 | 暂停所有 running 状态的任务 |
| 全部恢复 | 恢复所有 paused 状态的任务 |
| 全部停止 | 停止所有 pending/running/paused 状态的任务 |

### 3.6 任务暂停/恢复实现方案

采用操作系统级进程挂起方式，直接挂起 FFmpeg 子进程（Python 线程挂起不会影响独立子进程）。

#### 暂停 (suspend_process)

- **Windows**: 通过 `ctypes` 调用 `kernel32.SuspendProcess(handle)`
- **Linux/macOS**: 通过 `os.kill(pid, signal.SIGSTOP)`

暂停流程：
1. 调用 `suspend_process(pid)` 挂起 FFmpeg 子进程
2. 暂停该任务的 stderr 读取线程（避免管道缓冲区堆积）
3. 记录暂停时刻的进度快照
4. 更新任务状态: running -> paused
5. 持久化队列状态

#### 恢复 (resume_process)

- **Windows**: 通过 `ctypes` 调用 `kernel32.ResumeProcess(handle)`
- **Linux/macOS**: 通过 `os.kill(pid, signal.SIGCONT)`

恢复流程：
1. 调用 `resume_process(pid)` 恢复 FFmpeg 子进程
2. 恢复该任务的 stderr 读取线程
3. 更新任务状态: paused -> running
4. 持久化队列状态
5. 后续进度事件自然继续上报（由 stderr 解析驱动）

#### 边界处理

| 场景 | 处理 |
|------|------|
| 进程在暂停前已自行结束 | 捕获异常，标记为 completed/failed 而非 paused |
| 暂停状态下关闭应用 | 退出时终止所有运行中和已暂停的子进程 |
| 暂停时 stderr 管道缓冲区满 | 暂停时同步暂停读取线程，恢复后继续读取 |
| SuspendProcess 权限不足 | 降级为 kill 进程 + 记录进度，恢复时重新启动（从记录的进度点） |

### 3.7 实时进度

执行中的任务实时上报以下信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| percent | float | 转码进度百分比 0-100 |
| current_seconds | float | 当前已处理时长（秒） |
| total_seconds | float | 文件总时长（秒） |
| speed | string | 转码速度倍率，如 "2.5x" |
| fps | string | 当前帧率，如 "30.0" |
| frame | int | 已处理帧数 |
| estimated_remaining | float | 预计剩余时间（秒） |

进度更新频率：由 `ffmpeg_runner.py` 节流控制，最多每 0.5 秒上报一次。

### 3.8 任务日志

- 每个任务独立记录 FFmpeg 的 stderr 输出日志
- 点击任务行展开 TaskLogPanel 查看该任务的日志
- 日志为追加式，实时滚动到最新行
- 日志条目上限：每任务保留最近 500 行（防止内存占用过大）
- 日志随任务状态持久化到 JSON 文件

### 3.9 队列摘要 (QueueSummary)

在任务列表上方显示队列整体状态：

| 指标 | 说明 |
|------|------|
| 待执行 (pending) | 等待执行的任务数 |
| 执行中 (running) | 正在执行的任务数 |
| 已暂停 (paused) | 被暂停的任务数 |
| 已完成 (completed) | 已完成的任务数 |
| 失败 (failed) | 失败的任务数 |

### 3.10 任务排序

- 支持上下移动调整任务顺序
- 使用上/下箭头按钮（非拖拽），简单可靠
- 仅 pending 状态的任务可调整顺序
- 排序后持久化新顺序

---

## 4. 页面二：FFmpeg 命令配置

### 4.1 页面布局

```
+------------------------------------------------------------------+
| PresetSelector                                                     |
| [预设下拉选择 v] [保存为预设] [删除预设]                             |
+------------------------------------------------------------------+
| TranscodeForm          | FilterForm                               |
| 编码配置               | 滤镜配置                                  |
|                        |                                          |
| 视频编码器: [libx264v] | 旋转: [无旋转 v]                          |
| 音频编码器: [aac    v] | 裁剪: 宽[ ] 高[ ] X[ ] Y[ ]              |
| 视频码率: [5M     ]   | 水印: [选择文件路径...]                    |
| 音频码率: [192k   ]   | 水印位置: [左上v]                          |
| 分辨率:   [       ]   | 音量: [1.0  ]                              |
| 帧率:     [       ]   | 速度: [1.0  ]                              |
| 输出格式: [.mp4   v]  |                                          |
+------------------------------------------------------------------+
| CommandPreview                                                     |
| ffmpeg -i input.mp4 -c:v libx264 -b:v 5M -c:a aac ...            |
| 验证结果: [2 警告, 0 错误]                                         |
+------------------------------------------------------------------+
| [添加到队列] (使用当前配置添加文件到任务队列)                          |
+------------------------------------------------------------------+
```

### 4.2 转码配置 (TranscodeConfig)

| 参数 | 字段名 | 类型 | 默认值 | 可选值 |
|------|--------|------|--------|--------|
| 视频编码器 | video_codec | select | libx264 | libx264, libx265, copy, none |
| 音频编码器 | audio_codec | select | aac | aac, libmp3lame, copy, none |
| 视频码率 | video_bitrate | text | "" (自动) | 如 "5M", "10M", "8000k" |
| 音频码率 | audio_bitrate | text | 192k | 如 "128k", "256k", "320k" |
| 分辨率 | resolution | text | "" (原始) | 如 "1920x1080", "1280x720" |
| 帧率 | framerate | text | "" (原始) | 如 "30", "60" |
| 输出格式 | output_extension | select | .mp4 | .mp4, .mkv, .avi, .mov, .mp3, .aac, .flac, .wav |

**说明：**
- 视频编码器选 "copy" 时跳过视频重编码，码率/分辨率/帧率配置无效
- 音频编码器选 "copy" 时跳过音频重编码，音频码率配置无效
- 视频编码器选 "none" 时移除视频流
- 音频编码器选 "none" 时移除音频流

### 4.3 滤镜配置 (FilterConfig)

| 参数 | 字段名 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| 旋转 | rotate | select | 无旋转 | 无旋转, 顺时针90, 顺时针180, 顺时针270 |
| 裁剪 | crop | text | "" (不裁剪) | 格式: W:H:X:Y，如 "1920:800:0:140" |
| 水印路径 | watermark_path | text | "" (无水印) | 水印图片的绝对路径 |
| 水印位置 | watermark_position | select | 右下角 | 左上角, 右上角, 左下角, 右下角 |
| 水印边距 | watermark_margin | number | 10 | 水印距边缘像素数 |
| 音量 | volume | text | "" (原始) | 如 "1.5" (增大), "0.5" (减小) |
| 速度 | speed | text | "" (原始) | 如 "2.0" (加速), "0.5" (减速) |

**说明：**
- 所有滤镜字段为空时等同于不应用滤镜
- 滤镜可组合使用，后端自动构建正确的 `-filter_complex` 链
- 滤镜链内部排序: crop -> scale -> rotate -> overlay(watermark) -> speed

### 4.4 命令预览

- 实时根据当前转码+滤镜配置生成完整的 FFmpeg 命令行
- 命令显示在只读文本框中，可复制
- 不需要提供实际输入文件即可预览（使用占位符 `input.mp4`）
- 每次配置变更时自动更新预览

### 4.5 参数验证

实时验证当前配置，在命令预览下方显示结果：

| 级别 | 触发条件 |
|------|----------|
| 警告 | 视频编码器为 copy 但设置了滤镜（滤镜需要重编码） |
| 警告 | 速度调整大于 4.0 或小于 0.25（可能导致音画不同步） |
| 错误 | 分辨率格式不正确（非 WxH 格式） |
| 错误 | 裁剪区域超出视频尺寸（如果有文件信息） |
| 错误 | 水印文件路径不存在或不是图片 |

### 4.6 预设管理

| 操作 | 说明 |
|------|------|
| 保存预设 | 将当前转码+滤镜配置保存为命名预设，输入名称和描述 |
| 加载预设 | 从下拉列表选择预设，自动填充表单 |
| 删除预设 | 删除用户创建的预设（内置预设不可删除） |
| 内置预设 | 提供常用配置作为起点，如"MP4转码(H.264)"、"音频提取"等 |

预设存储方式：
- 内置预设: 项目 `presets/` 目录下的 JSON 文件（只读）
- 用户预设: APPDATA 目录下的 JSON 文件（可读写）
- 预设结构包含完整的 `TranscodeConfig` + `FilterConfig`

### 4.7 添加到队列

页面底部的"添加到队列"按钮：
1. 打开文件选择对话框
2. 用户选择一个或多个媒体文件
3. 使用当前页面的配置创建任务
4. 自动跳转到任务队列页面，显示新添加的任务

---

## 5. 页面三：软件配置

### 5.1 页面布局

```
+------------------------------------------------------------------+
| FFmpegSetup                                                        |
| 当前状态: [已就绪] 版本: FFmpeg 6.0 / ffprobe 6.0                  |
| 当前路径: C:\path\to\ffmpeg.exe                                    |
| [自动检测] [下载FFmpeg] [手动选择...]                               |
|                                                                    |
| 已知版本列表:                                                       |
|   (*) FFmpeg 6.0 (内置)   C:\...\ffmpeg.exe                       |
|   ( ) FFmpeg 7.0 (系统)   C:\Program Files\...\ffmpeg.exe          |
|   ( ) 自定义路径           (浏览选择 ffmpeg.exe)                    |
+------------------------------------------------------------------+
| ThreadCountInput                                                   |
| 最大并发线程数: (2) [1] [2] [3] [4]                                 |
| 说明: 同时执行的最大任务数，建议不超过CPU核心数                       |
+------------------------------------------------------------------+
| OutputFolderInput                                                  |
| 默认输出位置:                                                       |
|   (o) 与源文件同目录                                                |
|   ( ) 指定文件夹: [________________] [浏览...]                      |
+------------------------------------------------------------------+
| About                                                              |
| 应用版本: 2.0.0                                                    |
| Python版本: 3.11.x                                                |
| FFmpeg版本: 6.x                                                   |
+------------------------------------------------------------------+
```

### 5.2 FFmpeg 设置

#### 自动检测与下载

| 功能 | 说明 |
|------|------|
| 自动检测 | 在系统 PATH 和捆绑目录中查找 FFmpeg 二进制 |
| 下载 FFmpeg | 下载预编译的 FFmpeg 静态二进制文件 |
| 手动选择 | 打开文件选择对话框，让用户手动指定 ffmpeg.exe 路径 |
| 版本显示 | 显示检测到的 FFmpeg 和 ffprobe 版本号 |
| 路径显示 | 显示当前使用的 FFmpeg 可执行文件路径 |
| 状态指示 | 绿色=可用，红色=未找到，黄色=检测中 |

#### FFmpeg 版本切换

系统维护一个已知的 FFmpeg 可执行文件列表，用户可在列表中选择要使用的版本：

| 功能 | 说明 |
|------|------|
| 版本列表 | 显示所有已检测到的 FFmpeg 版本（内置、系统PATH、用户手动添加） |
| 自动发现 | 启动时自动扫描系统 PATH 和内置目录，构建版本列表 |
| 手动添加 | 用户可通过"手动选择"浏览添加自定义 ffmpeg.exe 路径 |
| 切换 | 点击列表中的版本项即切换，自动检测 ffprobe（同目录下） |
| 标记活跃 | 当前使用的版本在列表中高亮标记 |
| 持久化 | 用户选择的版本路径保存到 settings.json，下次启动自动使用 |

Bridge API:

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `setup_ffmpeg` | - | info: dict | 自动检测并初始化 FFmpeg（启动时调用） |
| `switch_ffmpeg` | path: str | info: dict | 切换到指定路径的 FFmpeg，返回版本信息 |
| `select_ffmpeg_binary` | - | path: str | 打开文件对话框选择 ffmpeg.exe |
| `get_ffmpeg_versions` | - | versions: list | 返回所有已知版本列表 |
| `download_ffmpeg` | - | path: str | 下载预编译 FFmpeg，返回安装路径 |

### 5.3 线程数设置

| 参数 | 说明 |
|------|------|
| 字段名 | max_workers |
| 范围 | 1-4 |
| 默认值 | 2 |
| 说明 | 同时执行的最大任务数，建议不超过 CPU 逻辑核心数 |
| 生效时机 | 立即生效，新的任务调度使用新值 |

### 5.4 默认输出文件夹

| 选项 | 说明 |
|------|------|
| 与源文件同目录 | 转码后的文件放在源视频所在目录（默认选项） |
| 指定文件夹 | 用户选择一个目录，所有输出文件放入该目录 |
| 浏览按钮 | 打开系统文件夹选择对话框 |

### 5.5 应用信息

显示只读的运行环境信息：
- 应用版本号 (从 pyproject.toml 读取)
- Python 版本
- FFmpeg 版本
- ffprobe 版本
- 操作系统信息

---

## 6. 后端架构

### 6.1 数据模型 (core/models.py)

配置类使用 `@dataclass(frozen=True)` 不可变数据类。`Task` 使用可变 dataclass，因为 `state`、`progress`、`log_lines` 等字段在运行时高频更新，频繁创建副本会带来不必要的性能开销。

```
TaskState = Literal["pending", "running", "paused", "completed", "failed", "cancelled"]

TranscodeConfig         # 转码参数 (frozen)
  video_codec, audio_codec, video_bitrate, audio_bitrate,
  resolution, framerate, output_extension

FilterConfig            # 滤镜参数 (frozen)
  rotate, crop, watermark_path, watermark_position, watermark_margin,
  volume, speed

TaskConfig              # 单个任务的完整配置 (frozen)
  transcode: TranscodeConfig
  filters: FilterConfig
  output_dir: str

TaskProgress            # 任务进度（实时更新, frozen）
  percent, current_seconds, total_seconds, speed, fps, frame,
  estimated_remaining

Task                    # 任务实体 (可变)
  id (UUID), file_path, file_name, file_size_bytes, duration_seconds,
  config: TaskConfig, state: TaskState, progress: TaskProgress,
  output_path, error, log_lines: list[str], created_at, started_at, completed_at

Preset                  # 预设 (frozen)
  id, name, description, config: TaskConfig, is_default

AppSettings             # 应用设置 (frozen)
  max_workers, default_output_dir, ffmpeg_path, ffprobe_path
```

### 6.2 模块职责

| 模块 | 职责 | 预估行数 |
|------|------|----------|
| `core/models.py` | 不可变数据模型定义 | ~200 |
| `core/task_queue.py` | 任务CRUD、状态机转换、队列排序、JSON持久化 | ~300 |
| `core/task_runner.py` | 线程池管理、任务分发、单任务控制（暂停/恢复/停止/重试） | ~350 |
| `core/ffmpeg_runner.py` | 单个FFmpeg子进程执行、stderr解析、进度上报（从1.x重构） | ~250 |
| `core/command_builder.py` | 从 TaskConfig 构建 FFmpeg 命令行参数 + 参数验证 | ~250 |
| `core/preset_manager.py` | 预设CRUD，内置+用户双层存储（重写） | ~200 |
| `core/config.py` | AppSettings 加载/保存 | ~100 |
| `core/file_info.py` | ffprobe 元信息探测（保留1.x） | - |
| `core/ffmpeg_setup.py` | FFmpeg 二进制检测/下载/版本管理（扩展1.x） | ~200 |
| `core/app_info.py` | 版本检测（保留1.x） | - |
| `core/logging.py` | Loguru 前端日志 sink（保留1.x） | - |

### 6.3 Bridge API (main.py @expose 方法)

所有方法返回统一格式: `{"success": bool, "data": ..., "error": ...}`

> **与 1.x 的对应关系**:
> - [保留] = 1.x 已有，2.0 保留（可能调整参数或返回值）
> - [新增] = 2.0 新增方法
> - [重构] = 1.x 有类似方法，但接口或行为大幅变化

#### 任务队列操作

| 方法 | 参数 | 返回 | 说明 | 来源 |
|------|------|------|------|------|
| `add_tasks` | paths: list[str], config: dict | tasks: list[Task] | 探测文件并添加到队列 | [重构] 原 `add_files` |
| `remove_tasks` | task_ids: list[str] | None | 删除指定任务 | [重构] 原 `remove_files` |
| `reorder_tasks` | task_ids: list[str] | None | 按给定ID顺序重排队列 | [新增] |
| `get_tasks` | - | tasks: list[Task] | 获取所有任务（队列顺序） | [重构] 原 `get_files` |
| `get_queue_summary` | - | summary: dict | 获取各状态任务计数 | [新增] |
| `clear_completed` | - | removed_count: int | 清除已完成任务 | [新增] |
| `clear_all` | - | None | 清空所有任务 | [重构] 原 `clear_files` |

#### 任务控制操作

| 方法 | 参数 | 返回 | 说明 | 来源 |
|------|------|------|------|------|
| `start_task` | task_id: str | None | 开始执行单个任务 | [重构] 原 `start_batch` 粒度细化 |
| `pause_task` | task_id: str | None | 暂停单个任务 | [新增] |
| `resume_task` | task_id: str | None | 恢复单个任务 | [新增] |
| `stop_task` | task_id: str | None | 停止单个任务 | [重构] 原 `cancel_batch` 粒度细化 |
| `retry_task` | task_id: str | None | 重试失败任务 | [新增] |
| `pause_all` | - | None | 暂停所有运行中任务 | [新增] |
| `stop_all` | - | None | 停止所有非终态任务 | [新增] |
| `resume_all` | - | None | 恢复所有已暂停任务 | [新增] |

#### 配置与预设操作

| 方法 | 参数 | 返回 | 说明 | 来源 |
|------|------|------|------|------|
| `build_command` | config: dict | command: str | 预览FFmpeg命令 | [新增] |
| `validate_config` | config: dict | errors: list, warnings: list | 验证配置参数 | [新增] |
| `get_presets` | - | presets: list[Preset] | 获取所有预设 | [保留] 参数不变，返回结构变化 |
| `save_preset` | preset: dict | preset: Preset | 保存预设 | [重构] preset 结构从 command_template 变为 config |
| `delete_preset` | preset_id: str | None | 删除预设 | [保留] |

#### 设置与系统操作

| 方法 | 参数 | 返回 | 说明 | 来源 |
|------|------|------|------|------|
| `get_settings` | - | settings: AppSettings | 获取应用设置 | [新增] |
| `save_settings` | settings: dict | None | 保存应用设置 | [新增] |
| `setup_ffmpeg` | - | info: dict | 自动检测并初始化FFmpeg | [保留] 返回信息增加版本详情 |
| `switch_ffmpeg` | path: str | info: dict | 切换到指定路径的FFmpeg | [新增] |
| `select_ffmpeg_binary` | - | path: str | 打开文件对话框选择ffmpeg.exe | [新增] |
| `get_ffmpeg_versions` | - | versions: list | 返回所有已知FFmpeg版本列表 | [新增] |
| `download_ffmpeg` | - | path: str | 下载预编译FFmpeg | [新增] |
| `get_app_info` | - | info: dict | 获取应用和FFmpeg版本信息 | [保留] |
| `select_files` | - | paths: list[str] | 打开文件选择对话框 | [保留] |
| `select_output_dir` | - | dir: str | 打开文件夹选择对话框 | [保留] |

### 6.4 事件协议 (Python -> Frontend)

| 事件名 | 数据 | 触发时机 |
|--------|------|----------|
| `task_added` | { task } | 新任务创建后 |
| `task_removed` | { task_id } | 任务被删除后 |
| `task_state_changed` | { task_id, old_state, new_state } | 任务状态变更时 |
| `task_progress` | { task_id, progress } | 进度更新时（0.5s节流） |
| `task_log` | { task_id, line } | 任务日志新增一行 |
| `queue_changed` | { summary } | 队列摘要变化时 |
| `log_line` | { line } | 全局日志输出 |

### 6.5 任务队列持久化

- 存储位置: APPDATA 目录 (`%APPDATA%/ff-intelligent-neo/queue_state.json`)
- 保存时机: 每次任务状态变更时自动保存（防抖 500ms）
- 保存内容: 所有非终态任务的完整状态 + 最近50条已完成/失败任务
- 启动恢复: 应用启动时加载持久化的队列状态
- 日志截断: 每任务最多持久化最近 100 行日志

### 6.6 任务暂停/恢复详细实现

```python
import ctypes
import os
import signal
import sys
import threading

# Windows 实现
def suspend_process(pid: int) -> None:
    PROCESS_SUSPEND_RESUME = 0x0800
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
    if not handle:
        raise OSError(f"Cannot open process {pid}")
    kernel32.SuspendProcess(handle)
    kernel32.CloseHandle(handle)

def resume_process(pid: int) -> None:
    PROCESS_SUSPEND_RESUME = 0x0800
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
    if not handle:
        raise OSError(f"Cannot open process {pid}")
    kernel32.ResumeProcess(handle)
    kernel32.CloseHandle(handle)

# Linux/macOS 实现
def suspend_process(pid: int) -> None:
    os.kill(pid, signal.SIGSTOP)

def resume_process(pid: int) -> None:
    os.kill(pid, signal.SIGCONT)

# 跨平台选择
if sys.platform == "win32":
    _suspend = suspend_process  # Windows ctypes 版本
    _resume = resume_process
else:
    _suspend = lambda pid: os.kill(pid, signal.SIGSTOP)
    _resume = lambda pid: os.kill(pid, signal.SIGCONT)
```

#### TaskRunner 中的暂停/恢复集成

```python
class TaskRunner:
    def __init__(self, emit):
        self._procs: dict[str, subprocess.Popen] = {}
        self._readers: dict[str, threading.Event] = {}  # 读取线程暂停信号
        self._lock = threading.Lock()

    def pause_task(self, task_id: str) -> None:
        with self._lock:
            proc = self._procs.get(task_id)
            if proc and proc.poll() is None:
                _suspend(proc.pid)
                # 暂停 stderr 读取线程
                reader_event = self._readers.get(task_id)
                if reader_event:
                    reader_event.set()  # 通知读取线程暂停

    def resume_task(self, task_id: str) -> None:
        with self._lock:
            proc = self._procs.get(task_id)
            if proc and proc.poll() is None:
                _resume(proc.pid)
                # 恢复 stderr 读取线程
                reader_event = self._readers.get(task_id)
                if reader_event:
                    reader_event.clear()
```

---

## 7. 前端架构

### 7.1 目录结构

```
frontend/src/
  main.ts                       # 应用入口，挂载 router
  App.vue                       # 根布局: Navbar + router-view
  router.ts                     # vue-router 配置
  bridge.ts                     # call() + onEvent() 桥接工具（保留1.x）
  style.css                     # Tailwind + DaisyUI 导入
  env.d.ts                      # pywebview 类型声明

  types/
    task.ts                     # TaskDTO, TaskState, TaskProgressDTO
    config.ts                   # TranscodeConfigDTO, FilterConfigDTO, TaskConfigDTO
    preset.ts                   # PresetDTO
    settings.ts                 # AppSettingsDTO

  composables/
    useBridge.ts                # 事件监听生命周期管理（自动清理）
    useTaskQueue.ts             # 任务列表CRUD、选中状态、排序
    useTaskControl.ts           # 单任务/批量 控制操作（调用bridge）
    useTaskProgress.ts          # 实时进度订阅、日志订阅
    usePresets.ts               # 预设CRUD（从1.x扩展）
    useConfig.ts                # 转码+滤镜表单状态管理
    useCommandPreview.ts        # FFmpeg命令预览生成、验证结果
    useSettings.ts              # 应用设置加载/保存
    useFileDrop.ts              # 拖拽文件处理（保留1.x）

  pages/
    TaskQueuePage.vue           # 页面一: 任务队列
    CommandConfigPage.vue       # 页面二: 命令配置
    SettingsPage.vue            # 页面三: 软件配置

  components/
    layout/
      AppNavbar.vue             # 顶部导航栏

    task-queue/
      TaskToolbar.vue           # 添加/移除/清空/批量操作工具栏
      TaskList.vue              # 可滚动的任务列表容器
      TaskRow.vue               # 单行任务（多选框+信息+操作按钮）
      TaskProgressBar.vue       # 单任务进度条（百分比+时间+速度）
      QueueSummary.vue          # 队列状态统计摘要
      TaskLogPanel.vue          # 可展开的任务日志查看器
      BatchControlBar.vue       # 全部暂停/恢复/停止按钮栏

    config/
      TranscodeForm.vue         # 编码配置表单
      FilterForm.vue            # 滤镜配置表单
      CommandPreview.vue        # 命令预览文本框 + 验证结果
      PresetSelector.vue        # 预设下拉 + 保存/删除按钮
      PresetEditor.vue          # 预设编辑弹窗（新建/编辑时）

    settings/
      FFmpegSetup.vue           # FFmpeg检测/下载/版本切换
      FFmpegVersionList.vue     # 已知FFmpeg版本列表（单选切换）
      ThreadCountInput.vue      # 线程数选择
      OutputFolderInput.vue     # 输出文件夹设置

  utils/
    format.ts                   # 格式化工具函数（时长、大小、百分比）
```

### 7.2 Composable 职责分配

| Composable | 管理的状态 | 职责 |
|------------|-----------|------|
| `useBridge` | 无 | `on(event, handler)` 包装，组件卸载时自动取消监听 |
| `useTaskQueue` | tasks[], selectedIds[], queueSummary | 任务CRUD、多选、排序、调用bridge获取数据 |
| `useTaskControl` | 无 | 单任务/批量 start/pause/resume/stop/retry，调用bridge |
| `useTaskProgress` | progressMap{}, logsMap{} | 订阅 task_progress/task_log 事件，更新本地状态 |
| `usePresets` | presets[], currentPresetId | 预设列表、加载、保存、删除 |
| `useConfig` | transcodeConfig, filterConfig | 表单双向绑定、重置、序列化为DTO |
| `useCommandPreview` | commandText, errors[], warnings[] | 调用后端验证、生成预览命令 |
| `useSettings` | settings | 加载/保存应用设置 |
| `useFileDrop` | isDragging | 拖拽进入/离开/放下事件处理 |

### 7.3 状态管理方案

使用 Vue 3 的 `provide/inject` + composable 模式，不引入 Pinia/Vuex：

- App.vue 通过 `provide` 注入全局 composable 实例
- 各页面组件通过 `inject` 获取共享状态
- 事件驱动的实时数据（进度、日志）通过 bridge 事件机制更新
- 页面级表单状态（配置表单）由页面 composable 独立管理

---

## 8. 数据流

### 8.1 任务添加流程

```
用户点击"添加文件"
  -> call("select_files")
  <- 返回文件路径列表
  -> call("add_tasks", { paths, config: currentConfig })
     -> TaskQueue.add_tasks()
        -> file_info.probe() 每个文件
        -> 创建 Task 对象，加入队列
        -> save_state() 持久化
        -> _emit("task_added", task) 每个任务
        -> _emit("queue_changed", summary)
  <- 返回 { success, data: tasks }
```

### 8.2 任务执行流程

```
用户点击任务"开始"
  -> call("start_task", task_id)
     -> TaskRunner.start_task()
        -> 从 TaskQueue 获取任务
        -> 更新状态: pending -> running
        -> _emit("task_state_changed")
        -> 构建 FFmpeg 命令 (command_builder)
        -> 提交到 ThreadPoolExecutor
           -> ffmpeg_runner.run_single()
              -> 解析 stderr 进度
              -> _emit("task_progress") 每0.5s
              -> _emit("task_log") 每行stderr
           -> 完成时:
              -> 更新状态: running -> completed/failed
              -> save_state()
              -> _emit("task_state_changed")
              -> _emit("queue_changed")
  <- 返回 { success }
```

### 8.3 任务暂停/恢复流程

```
用户点击"暂停"
  -> call("pause_task", task_id)
     -> TaskRunner.pause_task()
        -> suspend_process(ffmpeg_proc.pid)
        -> 更新状态: running -> paused
        -> save_state()
        -> _emit("task_state_changed")
  <- 返回 { success }

用户点击"恢复"
  -> call("resume_task", task_id)
     -> TaskRunner.resume_task()
        -> resume_process(ffmpeg_proc.pid)
        -> 更新状态: paused -> running
        -> save_state()
        -> _emit("task_state_changed")
  <- 返回 { success }
```

### 8.4 配置预览流程

```
用户修改任何配置参数
  -> useConfig composable 更新本地状态
  -> useCommandPreview.buildPreview()
     -> call("validate_config", { config })
     <- 返回 { errors, warnings }
     -> call("build_command", { config })
     <- 返回 { command }
  -> 更新 commandText, errors[], warnings[]
  -> CommandPreview 组件显示结果
```

---

## 9. 命令构建规则 (command_builder.py)

### 设计原则: 可扩展的命令构建器

`command_builder.py` 采用策略模式设计，将命令构建拆分为独立的、可组合的步骤，便于后续扩展新的转码选项和滤镜类型。

**架构要点：**

1. **参数注册机制**: 每种转码参数和滤镜类型通过注册函数添加，新增参数无需修改核心构建逻辑
2. **滤镜链自动排序**: 滤镜通过声明优先级自动排序，新增滤镜只需声明优先级数值
3. **独立验证层**: 每种参数/滤镜拥有独立的验证函数，验证逻辑与构建逻辑解耦
4. **插件化扩展点**: 通过 `_register_transcode_param` / `_register_filter` 接口，未来可支持第三方滤镜插件

```python
# command_builder.py 扩展接口示意

# 注册新的转码参数（未来扩展示例: 硬件加速）
_register_transcode_param("hwaccel", {
    "build": lambda val: ["-hwaccel", val] if val else [],
    "validate": lambda val, ctx: [] if val in ("auto", "cuda", "qsv", "d3d11va") else ["error: 不支持的硬件加速: " + val],
})

# 注册新的滤镜（未来扩展示例: 去噪）
_register_filter("denoise", {
    "priority": 10,       # 在 crop(5) 之后、scale(20) 之前
    "build_vf": lambda val: [f"hqdn3d={val}"] if val else [],
    "validate": lambda val: [] if not val or 1 <= float(val) <= 20 else ["warning: 去噪强度建议 1-20"],
})
```

### 9.1 转码参数映射

| 配置项 | FFmpeg 参数 | 条件 |
|--------|-------------|------|
| video_codec=libx264 | `-c:v libx264` | 非copy非none |
| video_codec=copy | `-c:v copy` | - |
| video_codec=none | `-vn` | - |
| video_bitrate | `-b:v 5M` | 非空且非copy |
| audio_codec=aac | `-c:a aac` | 非copy非none |
| audio_codec=copy | `-c:a copy` | - |
| audio_codec=none | `-an` | - |
| audio_bitrate | `-b:a 192k` | 非空且非copy |
| resolution | `-vf scale=1920:1080` | 非空（与滤镜合并） |
| framerate | `-r 30` | 非空 |
| output_extension | 输出路径后缀 | - |

### 9.2 滤镜链构建

滤镜采用优先级自动排序机制。每个滤镜声明一个 `priority` 数值，构建时按数值升序排列，自动生成正确的 FFmpeg 滤镜链。

**内置滤镜优先级表：**

| 滤镜 | priority | 说明 |
|------|----------|------|
| crop | 5 | 裁剪（优先于缩放，避免缩放后裁剪坐标失效） |
| denoise | 10 | 去噪（预留扩展位） |
| scale | 20 | 缩放/分辨率调整 |
| rotate | 30 | 旋转（transpose） |
| speed | 40 | 速度调整（setpts + atempo） |
| overlay | 50 | 水印叠加（必须最后，因涉及多输入流合流） |

新增滤镜只需注册并声明 priority，系统自动将其插入正确位置。

当有多个滤镜时，按 priority 升序排列，自动合并为正确的 FFmpeg 表达式：

```
# 仅有视频滤镜 (无水印)
-vf "crop=1920:800:0:140,transpose=1,scale=1920:1080,setpts=0.5*PTS"

# 有水印时 (使用 filter_complex)
-filter_complex "[0:v]crop=...,transpose=...,scale=...,setpts=...[tmp];[tmp][1:v]overlay=W-10-ow:10"
-i watermark.png

# 有音频滤镜
-af "volume=1.5,atempo=2.0"
```

### 9.3 完整命令示例

基本用例:

```
# H.264转码 + 720p缩放 + 旋转90度 + 音量1.5倍
ffmpeg -i input.mp4 \
  -c:v libx264 -b:v 5M \
  -c:a aac -b:a 192k \
  -vf "scale=1280:720,transpose=1" \
  -af "volume=1.5" \
  -r 30 \
  output.mp4

# 添加水印
ffmpeg -i input.mp4 -i watermark.png \
  -filter_complex "[0:v]scale=1920:1080[tmp];[tmp][1:v]overlay=W-10-ow:10" \
  -c:v libx264 -c:a aac \
  output.mp4
```

未来扩展示例（仅展示命令构建器的生成能力，2.0.0 不实现）:

```
# 硬件加速 + 去噪 + 2x超分辨率（通过注册扩展参数和滤镜自动生成）
ffmpeg -hwaccel cuda -i input.mp4 \
  -c:v h264_nvenc -b:v 8M \
  -c:a aac -b:a 192k \
  -vf "crop=1920:1080:0:0,hqdn3d=4,scale=3840:2160" \
  -r 60 \
  output.mp4
```

### 9.4 验证规则

验证通过 `validate_config()` 方法实现，每种参数拥有独立的验证函数。验证函数接收配置值和上下文（context，包含已探测的文件信息等），返回错误列表和警告列表。

```python
# 验证函数签名
def validate_transcode_param(key: str, value: str, ctx: ValidationContext) -> list[str]:
    """返回错误列表，空列表表示通过。"""
    ...

def validate_filter_param(key: str, value: str, ctx: ValidationContext) -> list[str]:
    """返回错误列表和警告列表。"""
    ...
```

**验证规则清单：**

| 级别 | 参数 | 规则 | 说明 |
|------|------|------|------|
| 错误 | video_bitrate | 正则 `^\d+[kKMGT]?$` | 格式不合法时报错 |
| 错误 | resolution | 正则 `^\d+x\d+$` | 非数字x数字格式时报错 |
| 错误 | resolution | 如果 ctx.file_info 存在，解析出的宽高必须 > 0 | 无效分辨率值 |
| 错误 | crop | 正则 `^\d+:\d+:\d+:\d+$` | 非W:H:X:Y格式时报错 |
| 错误 | crop | 如果 ctx.file_info 存在，裁剪区域不能超出视频尺寸 | 否则 FFmpeg 报错 |
| 错误 | watermark_path | 非空时必须是存在的文件路径 | 路径不存在或不是文件 |
| 错误 | watermark_path | 非空时必须是图片格式 (后缀匹配) | 非图片文件 |
| 错误 | volume | 非空时必须是有效数字 | 无效数值 |
| 错误 | speed | 非空时必须是 0.25-100 范围内的数字 | 超出 FFmpeg atempo 支持范围 |
| 警告 | video_codec=copy + 任何滤镜 | copy 不重编码，滤镜不会生效 | 用户可能误操作 |
| 警告 | audio_codec=copy + volume | copy 不重编码，音量调整不会生效 | 同上 |
| 警告 | speed < 0.5 或 speed > 4.0 | 可能导致音画不同步 | 非硬性错误，但需提醒 |
| 警告 | framerate + video_codec=copy | copy 直接复制帧率，framerate 参数无效 | 同上 |

**验证上下文 (ValidationContext)：**

```python
@dataclass(frozen=True)
class ValidationContext:
    file_info: FileItem | None  # 如果有已探测的文件信息，用于边界检查
    ffmpeg_version: str | None  # FFmpeg 版本，用于版本兼容性检查
```

**命令注入防护：**

所有用户输入的参数值在构建命令前必须经过转义处理：
- 路径类参数（watermark_path）: 使用 `shlex.quote()` 转义
- 数值类参数（resolution, crop, volume, speed）: 只允许数字和有限符号（`x`, `:`, `.`）
- 编码器名称: 只允许白名单中的值（`libx264`, `libx265`, `aac`, `copy`, `none` 等）

---

## 10. 持久化方案

### 10.1 存储位置

| 数据 | 路径 | 格式 |
|------|------|------|
| 队列状态 | `%APPDATA%/ff-intelligent-neo/queue_state.json` | JSON |
| 应用设置 | `%APPDATA%/ff-intelligent-neo/settings.json` | JSON |
| 用户预设 | `%APPDATA%/ff-intelligent-neo/presets/*.json` | JSON (每个预设一个文件) |
| 内置预设 | `{app}/presets/default_presets.json` | JSON (只读) |

### 10.2 队列持久化内容

```json
{
  "version": "2.0.0",
  "saved_at": "2026-04-22T13:00:00",
  "tasks": [
    {
      "id": "uuid",
      "file_path": "/path/to/video.mp4",
      "file_name": "video.mp4",
      "state": "running",
      "progress": { "percent": 38.5, ... },
      "config": { "transcode": {...}, "filters": {...} },
      "log_lines": ["...", "..."]
    }
  ]
}
```

### 10.3 启动恢复逻辑

1. 加载 `queue_state.json`
2. 所有 `running` 状态的任务重置为 `failed`（因进程已不存在）
3. 所有 `paused` 状态的任务重置为 `pending`（因进程已不存在）
4. 保留 `pending` 任务不变
5. 保留 `completed` / `failed` / `cancelled` 任务用于历史查看
6. 清理超过 50 条的已完成/失败任务（保留最近 50 条）

---

## 11. 实施计划

### Phase 1: 基础层

**目标**: 可启动的应用，三个空白页面可导航

| 序号 | 内容 | 类型 |
|------|------|------|
| 1 | 安装 vue-router 依赖 | 配置 |
| 2 | `core/models.py` 全部数据模型 | 新建 |
| 3 | `core/config.py` AppSettings 加载/保存 | 新建 |
| 4 | `frontend/src/router.ts` vue-router 配置 | 新建 |
| 5 | `frontend/src/main.ts` 挂载 router | 修改 |
| 6 | `frontend/src/App.vue` Navbar + router-view + provide/inject | 重写 |
| 7 | `frontend/src/components/layout/AppNavbar.vue` | 新建 |
| 8 | 三个页面占位组件 | 新建 |
| 9 | `frontend/src/types/*.ts` DTO 类型定义 | 新建 |
| 10 | `frontend/src/composables/useBridge.ts` | 新建 |
| 11 | `frontend/src/bridge.ts` 适配新统一返回格式 | 修改 |
| 12 | 清理 1.x 不再需要的代码（`batch_runner.py`、旧 `main.py` 方法标记废弃） | 清理 |

### Phase 2a: 任务队列后端

**目标**: 完整的后端任务管理能力

| 序号 | 内容 | 类型 |
|------|------|------|
| 1 | `core/task_queue.py` 任务CRUD + 状态机 + JSON持久化 | 新建 |
| 2 | `core/ffmpeg_runner.py` 重构（每任务cancel_event + 进度解析） | 重写 |
| 3 | `core/command_builder.py` 基础转码命令生成 | 新建 |
| 4 | `core/task_runner.py` 线程池 + 任务分发 + 停止 | 新建 |
| 5 | `main.py` 模块化拆分（TaskApiMixin + ConfigApiMixin）+ 任务相关 @expose 方法 | 重写 |

### Phase 2b: 任务队列前端

**目标**: 完整的任务队列 UI

| 序号 | 内容 | 类型 |
|------|------|------|
| 1 | 全部 task-queue 组件 (7个): TaskToolbar, TaskList, TaskRow, TaskProgressBar, QueueSummary, TaskLogPanel, BatchControlBar | 新建 |
| 2 | useTaskQueue, useTaskControl, useTaskProgress composable | 新建 |
| 3 | useFileDrop（从1.x迁移） | 迁移 |
| 4 | TaskQueuePage.vue 完整实现 | 重写 |
| 5 | `frontend/src/utils/format.ts` 格式化工具 | 新建 |

### Phase 3: FFmpeg 配置页 + 预设

**目标**: 完整的转码/滤镜表单、命令预览、预设管理

| 序号 | 内容 | 类型 |
|------|------|------|
| 1 | `core/command_builder.py` 添加滤镜链支持 + 参数验证 | 扩展 |
| 2 | `core/preset_manager.py` 重写（适配新的 config 结构化预设） | 重写 |
| 3 | 内置预设 JSON 更新（从 command_template 迁移到 config 结构） | 更新 |
| 4 | `main.py` 配置/预设 @expose 方法 | 扩展 |
| 5 | 全部 config 组件 (6个): TranscodeForm, FilterForm, CommandPreview, PresetSelector, PresetEditor | 新建 |
| 6 | useConfig, usePresets, useCommandPreview composable | 新建 |
| 7 | CommandConfigPage.vue 完整实现 | 重写 |

### Phase 3.5: 暂停/恢复技术验证

**目标**: 验证进程挂起方案的可行性

| 序号 | 内容 | 类型 |
|------|------|------|
| 1 | 编写最小 demo: 启动 FFmpeg 子进程 -> SuspendProcess -> ResumeProcess -> 验证 stderr 管道不死锁 | 验证 |
| 2 | 验证 stderr 读取线程暂停/恢复机制 | 验证 |
| 3 | 验证权限不足时的降级策略（kill + 重试） | 验证 |
| 4 | 记录验证结论，如有问题调整 PRD 6.6 方案 | 文档 |

**注意**: 此阶段仅做技术验证，不修改项目代码。如果验证失败，需要回退到替代方案（如 kill 进程 + 记录进度点 + 重新启动）。

### Phase 4: 暂停/恢复 + 设置页

**目标**: 单任务暂停/恢复、任务排序、重试、软件设置

| 序号 | 内容 | 类型 |
|------|------|------|
| 1 | `core/task_runner.py` 暂停/恢复（基于 Phase 3.5 验证结果） | 扩展 |
| 2 | `main.py` 暂停/恢复/重试/设置方法 | 扩展 |
| 3 | 全部 settings 组件 (3个): FFmpegSetup, FFmpegVersionList, ThreadCountInput, OutputFolderInput | 新建 |
| 4 | useSettings composable | 新建 |
| 5 | SettingsPage.vue 完整实现 | 重写 |
| 6 | TaskRow.vue 排序按钮 | 扩展 |

### Phase 5: 持久化 + 打磨

**目标**: 生产可用、状态恢复、边界处理

| 序号 | 内容 | 类型 |
|------|------|------|
| 1 | 队列状态自动保存 + 启动恢复逻辑 | 实现 |
| 2 | `core/ffmpeg_setup.py` 扩展：FFmpeg 版本检测/切换/下载 | 扩展 |
| 3 | 预计剩余时间计算 | 实现 |
| 4 | UI 状态（空状态、加载态、错误提示） | 完善 |
| 5 | 构建配置更新（PyInstaller spec + 预设文件打包） | 更新 |
| 6 | 手动测试清单执行 | 测试 |

---

## 12. 风险评估

| 风险 | 严重度 | 缓解措施 |
|------|--------|----------|
| 命令注入（用户输入恶意滤镜参数） | 高 | 所有参数值经过白名单校验 + `shlex.quote()` 转义，编码器名称只允许枚举值 |
| Windows `SuspendProcess` 需要足够的进程权限 | 中 | 以普通用户权限运行时通常足够，失败时降级为 kill+重试 |
| 进程挂起后 stderr 管道缓冲区可能填满 | 中 | 暂停时暂停读取线程，恢复时继续读取 |
| `filter_complex` 语法因编解码器不同而有差异 | 中 | 使用经过验证的滤镜链排序，提供命令预览供用户确认 |
| FFmpeg 版本兼容性（不同版本滤镜语法差异） | 中 | 在 ValidationContext 中携带 FFmpeg 版本，版本相关的参数给出警告 |
| 批量转码时磁盘空间耗尽 | 中 | 转码前检查输出目录剩余空间（粗略估算：文件大小 x 2），空间不足时警告用户 |
| JSON 持久化在 100+ 任务时可能变慢 | 低 | 防抖 500ms 保存，日志截断，清理已完成任务 |
| 多实例并发写入 `queue_state.json` | 低 | 使用文件锁（`fcntl.flock` / `msvcrt.locking`），或启动时检测已有实例 |
| vue-router hash 模式与 pywebview URL 兼容性 | 低 | Phase 1 优先验证，已知可用 |
| 暂停状态下关闭应用，进程成为孤儿 | 低 | 在应用退出时主动终止所有运行中和已暂停的进程 |

---

## 13. 手动测试清单

### Phase 1 测试

- [ ] 应用启动，三个页面可通过导航栏切换
- [ ] Hash URL 在 pywebview 中正常工作
- [ ] 直接输入 hash URL 可跳转到对应页面

### Phase 2 测试

- [ ] 通过文件对话框添加 5 个文件，全部显示为"待执行"
- [ ] 通过拖拽添加文件
- [ ] 选中多个任务后点击"移除选中"，任务被删除
- [ ] 点击单个任务"开始"，任务转为"执行中"，进度条更新
- [ ] 点击任务"停止"，任务转为"已取消"
- [ ] 全部任务完成后显示正确的队列摘要
- [ ] 某个任务失败时显示错误信息，其他任务继续
- [ ] 选中任务后展开日志面板，显示 FFmpeg stderr 输出

### Phase 3 测试

- [ ] 切换视频编码器，命令预览实时更新
- [ ] 设置分辨率 1280x720，预览中出现 `scale=1280:720`
- [ ] 设置音量 1.5，预览中出现 `volume=1.5`
- [ ] 组合裁剪+旋转+水印，预览中 `filter_complex` 链正确
- [ ] 视频编码器设为 copy 但设置了滤镜，显示验证警告
- [ ] 分辨率格式错误，显示验证错误
- [ ] 保存预设 -> 下拉列表中出现
- [ ] 加载预设 -> 表单自动填充
- [ ] 删除预设 -> 从列表移除
- [ ] 使用当前配置"添加到队列"，文件出现在任务队列页面

### Phase 4 测试

- [ ] 暂停执行中的任务 -> 进程暂停，状态显示"已暂停"
- [ ] 恢复已暂停任务 -> 进程继续，进度继续更新
- [ ] 停止已暂停任务 -> 状态显示"已取消"
- [ ] 重试失败任务 -> 状态重置为"待执行"，可重新执行
- [ ] 上移/下移任务 -> 队列顺序变更
- [ ] 全部暂停/恢复/停止 -> 批量操作正确执行
- [ ] 修改线程数 -> 下次任务调度使用新值
- [ ] 设置自定义输出文件夹 -> 任务使用该文件夹

### Phase 5 测试

- [ ] 执行任务后关闭应用再打开 -> 队列状态恢复
- [ ] 暂停任务后关闭应用再打开 -> 暂停的任务变为待执行
- [ ] 50+ 文件队列 -> UI 响应正常
- [ ] 预计剩余时间显示合理
- [ ] 空状态（无任务）页面显示友好提示
