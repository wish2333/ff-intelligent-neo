# 系统架构

## 整体结构

```
ff-intelligent-neo/
├── main.py                 # 后端入口，Bridge API 定义
├── core/                   # 核心业务逻辑
│   ├── models.py           # 数据模型（Task, TaskState, TranscodeConfig 等）
│   ├── task_runner.py      # 任务执行、暂停/恢复/终止/重置
│   ├── command_builder.py  # FFmpeg 命令构建
│   ├── ffmpeg_setup.py     # FFmpeg 下载/检测/版本管理
│   └── logging.py          # 日志系统
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── bridge.ts       # PyWebVue Bridge 通信层
│   │   ├── components/
│   │   │   ├── common/     # 通用组件
│   │   │   │   ├── FileDropInput.vue  # 文件拖拽输入组件
│   │   │   │   └── SplitDropZone.vue  # 左右分屏全屏拖拽组件 (Phase 3.5.2)
│   │   │   ├── layout/     # 布局组件
│   │   │   │   └── AppNavbar.vue      # 导航栏（含主题切换、FFmpeg 状态）
│   │   │   ├── config/     # 配置相关组件
│   │   │   │   ├── FilterForm.vue     # 滤镜配置表单
│   │   │   │   ├── EncoderSelect.vue  # 编码器分组选择（Phase 3）
│   │   │   │   ├── ClipForm.vue       # 视频剪辑配置（Phase 3, 3.5.2 时间拆分）
│   │   │   │   ├── AvsmixForm.vue     # 音频字幕混合配置（Phase 3）
│   │   │   │   ├── MergeFileList.vue  # 拼接文件列表（Phase 3）
│   │   │   │   ├── MergePanel.vue     # 拼接配置面板（Phase 3）
│   │   │   │   └── MergeSettingsForm.vue  # 拼接设置表单 - Config 页（Phase 3.5.2）
│   │   │   ├── settings/   # 设置相关组件
│   │   │   │   └── FFmpegSetup.vue    # FFmpeg 管理面板
│   │   │   └── task-queue/ # 任务队列组件
│   │   │       ├── TaskList.vue       # 任务列表
│   │   │       ├── TaskRow.vue        # 单行任务
│   │   │       └── TaskProgressBar.vue # 进度条
│   │   ├── composables/   # Vue Composables
│   │   ├── data/          # 静态数据（Phase 3）
│   │   │   └── encoders.ts         # 编码器注册表
│   │   │   ├── useTaskControl.ts      # 任务控制 API
│   │   │   ├── useSettings.ts         # 设置管理
│   │   │   └── useTheme.ts            # 主题切换管理
<!-- v2.1.0-CHANGE: Phase 3.5 新增页面组件 -->
│   │   ├── pages/         # 页面组件
│   │   │   ├── TaskQueuePage.vue
│   │   │   ├── CommandConfigPage.vue
│   │   │   ├── AudioSubtitlePage.vue  # 音频/字幕独立页面（Phase 3.5）
│   │   │   ├── MergePage.vue          # 拼接独立页面（Phase 3.5）
│   │   │   ├── CustomCommandPage.vue  # 自定义命令页面（Phase 3.5）
│   │   │   └── SettingsPage.vue
│   │   ├── types/         # TypeScript 类型定义
│   │   └── style.css      # 全局样式（DaisyUI 主题配置）
│   └── index.html
├── docs/                   # 设计文档
│   ├── StateMachine.md     # 状态机定义
│   ├── BusinessRules.md    # 业务规则
│   ├── Structure.md        # 本文件
│   ├── Procedure.md        # 业务流程
│   └── fields/             # 数据模型字段定义
└── references/             # 参考文档
```

## 通用组件

### FileDropInput.vue

<!-- v2.1.0-CHANGE: 新增 FileDropInput 组件文档 -->

文件拖拽输入组件，支持拖拽放置和点击选择两种输入方式。

**路径**: `frontend/src/components/common/FileDropInput.vue`

**Props**:

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `modelValue` | `string` | `""` | 当前文件路径（v-model 绑定） |
| `accept` | `string` | `undefined` | 接受的文件扩展名，逗号分隔（如 `.png,.jpg`） |
| `placeholder` | `string` | `"Drop file here or click to select"` | 空状态占位文本 |

**Events**:

| 事件 | 参数 | 说明 |
|------|------|------|
| `update:modelValue` | `value: string` | 文件路径变化时触发 |

**行为**:
- 拖拽进入时显示高亮边框（`border-primary`）
- 使用 `dragCounter` 计数器处理子元素 drag 事件冒泡
- drop 后等待 80ms 调用 `get_dropped_files`（兼容 pywebvue 文件处理延迟）
- 点击时调用 `select_file_filtered` 后端 API 打开文件对话框
- 有值时显示文件名，悬停显示完整路径（`title` 属性）
- 右上角 X 按钮清空文件

**使用场景**:
- `FilterForm.vue` 中水印路径输入（accept: `.png,.jpg,.jpeg,.bmp,.webp`）
- `FilterForm.vue` 中横竖屏背景图片路径输入（aspect_convert I 模式）

**Phase 3.5.2-fixes: 上下文依赖的全屏拖拽**:
- `FilterForm.vue` 新增 `fullscreenDropTarget` computed:
  - 无 aspect_convert: 全屏拖拽 → Watermark
  - aspect_convert I 模式 (H2V-I/V2H-I): 全屏拖拽 → Background Image
  - aspect_convert T/B 模式: 无全屏拖拽
- Watermark FileDropInput 使用 `v-if` 而非 `opacity + pointer-events-none`，确保 unmount 时 document 事件监听器被清理

## Composables

### useTheme.ts

<!-- v2.1.0-CHANGE: 新增 useTheme composable 文档 -->

主题管理 composable，处理 light/dark/auto 主题切换。

**路径**: `frontend/src/composables/useTheme.ts`

**类型定义**:
```typescript
type ThemeValue = "auto" | "light" | "dark"
```

**返回值**:

| 属性/方法 | 类型 | 说明 |
|----------|------|------|
| `currentTheme` | `Ref<ThemeValue>` | 当前主题偏好设置 |
| `setTheme` | `(theme: ThemeValue) => Promise<void>` | 设置主题并持久化到 settings.json |
| `toggleTheme` | `() => void` | 在 light/dark 之间快速切换 |
| `resolveTheme` | `(preference: ThemeValue) => string` | 解析实际应用的主题（auto -> light/dark） |

**行为**:
- 通过 `document.documentElement.setAttribute("data-theme", resolved)` 设置 DaisyUI 主题
- auto 模式下监听 `window.matchMedia("(prefers-color-scheme: light)")` 的 change 事件
- 主题变更通过 `save_settings` API 持久化到后端

### useTaskControl.ts

<!-- v2.1.0-CHANGE: 更新 useTaskControl 文档，新增 resetTask -->

任务控制 composable，提供单任务和批量操作 API。

**路径**: `frontend/src/composables/useTaskControl.ts`

**方法列表**:

| 方法 | 参数 | 后端 API | 说明 |
|------|------|---------|------|
| `startTask` | `taskId, config?` | `start_task` | 开始执行任务 |
| `stopTask` | `taskId` | `stop_task` | 终止任务 |
| `pauseTask` | `taskId` | `pause_task` | 暂停任务 |
| `resumeTask` | `taskId` | `resume_task` | 恢复任务 |
| `retryTask` | `taskId, config?` | `retry_task` | 重试失败任务 |
| `resetTask` | `taskId` | `reset_task` | 重置终态任务为 pending |
| `stopAll` | - | `stop_all` | 终止所有任务 |

### task_runner.py

**路径**: `core/task_runner.py`

**Phase 3.5.2-fixes 变更**:

**start_task 配置保护**:
- 启动任务时，来自前端的全局 config 仅更新 `transcode` + `filters`
- 任务已有的子配置（`merge`, `clip`, `avsmix`, `custom_command`）被保留
- 防止 Merge 页面任务的 merge.file_list 被全局 intro/outro 覆盖

**Concat 列表文件管理**:
- 检测 `merge.merge_mode in ("concat_protocol", "ts_concat")` 时自动创建临时列表文件
- 列表文件格式: `file 'D:\path\to\file1.mp4'\nfile 'D:\path\to\file2.mp4'`
- 临时文件路径替换 args 中的 `list.txt` 占位符
- 任务执行完成后自动清理临时文件（通过 `try/finally`）
| `pauseAll` | - | `pause_all` | 暂停所有任务 |
| `resumeAll` | - | `resume_all` | 恢复所有任务 |

## Bridge API

### 事件系统

<!-- v2.1.0-CHANGE: 新增事件系统文档 -->

后端通过 `self._emit(event_name, data)` 向前端发送事件，前端通过 `onEvent(event_name, callback)` 监听。

#### ffmpeg_version_changed

<!-- v2.1.0-CHANGE: 新增版本切换事件 -->

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `string` | FFmpeg 版本号 |
| `path` | `string` | FFmpeg 二进制路径 |
| `status` | `string` | 状态（`"ready"` 或 `"not_found"`） |

**触发时机**: `main.py` 中 `switch_ffmpeg` 方法调用成功后
**监听组件**: `AppNavbar.vue` — 更新导航栏 FFmpeg 状态徽标

---

## Phase 3: 命令构建功能完善

<!-- v2.1.0-CHANGE: Phase 3 新增编码器数据库、命令构建扩展、新页面架构 -->

### 编码器数据库

<!-- v2.1.0-CHANGE: Phase 3 新增编码器注册表架构 -->

前端维护一个完整的编码器注册表，按优先级分组展示，支持硬件编码器自动检测。

**路径**: `frontend/src/data/encoders.ts`（新增）

**类型定义**:
```typescript
interface EncoderConfig {
  name: string              // FFmpeg 编码器名称
  displayName: string        // 用户友好显示名
  category: 'video' | 'audio'
  hardwareType?: 'cpu' | 'nvidia' | 'amd' | 'intel'
  recommendedQuality?: number // 推荐质量值
  qualityMode?: 'crf' | 'cq' | 'qp'
  description: string       // 使用建议
  priority: 'P0' | 'P1' | 'P2' // 显示优先级
}
```

**视频编码器分组**:

| 优先级 | 编码器 | 硬件 | 推荐质量 | 模式 |
|--------|--------|------|---------|------|
| P0 | av1_nvenc | NVIDIA | 36 | cq |
| P0 | libx265 | CPU | 24 | crf |
| P0 | libsvtav1 | CPU | 32 | crf |
| P1 | libx264 | CPU | 23 | crf |
| P1 | hevc_nvenc | NVIDIA | 28 | cq |
| P1 | h264_nvenc | NVIDIA | 28 | cq |
| P1 | libvpx-vp9 | CPU | 31 | crf |
| P2 | h264_amf | AMD | 34 | qp |
| P2 | hevc_amf | AMD | 32 | qp |
| P2 | h264_qsv | Intel | 28 | qp |
| P2 | hevc_qsv | Intel | 30 | qp |
| - | copy | - | - | - |
| - | none | - | - | - |

**音频编码器**:

| 编码器 | 说明 | 推荐码率 |
|--------|------|---------|
| aac | 通用音频编码 | 192k |
| opus | 开源高质量音频 | 128k |
| flac | 无损音频 | - |
| libmp3lame | MP3 | 320k |
| alac | Apple Lossless | - |
| copy | 不重编码 | - |
| none | 移除音频 | - |

**硬件编码器检测**:
- Bridge API `check_hw_encoders()` 返回当前 FFmpeg 支持的编码器列表
- 前端启动时调用一次，不支持硬件的编码器灰显或隐藏
- 通过 `ffmpeg -encoders` 命令检测可用编码器

### command_builder.py 扩展

<!-- v2.1.0-CHANGE: Phase 3 更新命令构建器架构 -->

**路径**: `core/command_builder.py`

**现有架构**（保持不变）:
- 注册表模式：`_transcode_params` 和 `_filters` 字典管理可扩展参数
- 优先级排序：滤镜按 priority 数值排序构建链

**Phase 3.5.2-fixes 路径引用变更**:
- 移除所有 `shlex.quote()` 调用，替换为 `_subprocess_quote()`（no-op）
- 原因：subprocess.Popen 以列表传递参数时不需要 shell 级别引用
- `shlex.quote` 在 Windows 上产生单引号包裹，导致 Unicode 文件名报 "Illegal byte sequence"
- 新增 `_subprocess_quote()` 和 `_preview_quote()` 辅助函数
- 所有子 builder 函数移除 `-hide_banner -y`（由 `ffmpeg_runner.py` 统一添加）

**Phase 3 新增滤镜**:

| 滤镜 | 优先级 | 参数 | filter_complex |
|------|--------|------|----------------|
| audio_normalize | 16 | target_loudness, true_peak, lra | `loudnorm=I=-16:TP=-1.5:LRA=11` |
| aspect_convert | 35 | mode, target_resolution, bg_image_path | 见横竖屏转换章节 |

**Phase 3 新增命令构建函数**:

| 函数 | 用途 | 命令模式 |
|------|------|---------|
| `build_clip_command()` | 视频剪辑（extract/cut） | `-ss -to -accurate_seek -i ...` |
| `build_merge_command()` | 多视频拼接 | `-f concat` 或 `-filter_complex concat` |
| `build_avsmix_command()` | 音频字幕混合 | `-map 0:v -map 1:a -map 2:s` |

**VALID_VIDEO_CODECS 扩展**:
```python
VALID_VIDEO_CODECS = {
    # CPU
    "libx264", "libx265", "libsvtav1", "libvpx-vp9",
    # NVIDIA
    "av1_nvenc", "hevc_nvenc", "h264_nvenc",
    # AMD
    "h264_amf", "hevc_amf",
    # Intel
    "h264_qsv", "hevc_qsv",
    # Special
    "copy", "none",
}
```

### 数据模型扩展 (models.py)

<!-- v2.1.0-CHANGE: Phase 3 新增数据模型 -->

**FilterConfig 新增字段**:
```python
@dataclass(frozen=True)
class FilterConfig:
    # ... existing fields ...
    audio_normalize: bool = False
    target_loudness: int = -16
    true_peak: int = -1
    lra: int = 11
    aspect_convert: str = ""       # H2V-I, H2V-T, H2V-B, V2H-I, V2H-T, V2H-B
    target_resolution: str = ""    # e.g. "1080x1920"
    bg_image_path: str = ""
```

**新增数据模型**:
```python
@dataclass(frozen=True)
class ClipConfig:
    clip_mode: str = "extract"          # extract / cut
    start_time: str = ""
    end_time_or_duration: str = ""
    use_copy_codec: bool = True

@dataclass(frozen=True)
class MergeConfig:
    merge_mode: str = "ts_concat"       # ts_concat / concat_protocol / filter_complex
    target_resolution: str = ""
    target_fps: int = 0
    transcode_config: dict = field(default_factory=dict)
    intro_path: str = ""                # Phase 3.5: 片头视频路径
    outro_path: str = ""                # Phase 3.5: 片尾视频路径

@dataclass(frozen=True)
class AudioSubtitleConfig:
    external_audio_path: str = ""
    subtitle_path: str = ""
    subtitle_language: str = ""
    replace_audio: bool = True

<!-- v2.1.0-CHANGE: Phase 3.5 新增数据模型 -->
@dataclass(frozen=True)
class CustomCommandConfig:
    raw_args: str = ""                  # 原始 FFmpeg 参数
    output_extension: str = ".mp4"      # 输出文件扩展名
```

**TranscodeConfig 新增字段** (Phase 3.5):

```python
@dataclass(frozen=True)
class TranscodeConfig:
    # ... existing fields ...
    quality_mode: str = ""       # "crf", "cq", "qp"
    quality_value: int = 0       # CRF/CQ/QP 数值
    preset: str = ""             # 编码速度预设 (ultrafast ~ veryslow)
    pixel_format: str = ""       # 像素格式 (yuv420p, yuv420p10le, ...)
    max_bitrate: str = ""        # 最大码率 (e.g. "8M")
    bufsize: str = ""            # 缓冲区大小 (e.g. "2M"), Phase 3.5.1
```

**MergeConfig 默认值变更** (Phase 3.5.1):

```python
@dataclass(frozen=True)
class MergeConfig:
    target_resolution: str = "1920x1080"  # 默认 1920x1080 (原空字符串)
    target_fps: int = 30                  # 默认 30 (原 0)
```

### 新增前端组件

<!-- v2.1.0-CHANGE: Phase 3.5 重构页面布局 -->

**命令配置页** (`CommandConfigPage.vue`):

```
CommandConfigPage (Phase 3.5 重构, Phase 3.5.1 互斥, Phase 3.5.2 新增 Merge 选项卡)
  CommandPreview.vue      - 移至顶部（预设选择器之上）
  PresetSelector.vue      - 预设管理
  TabBar: [转码] [滤镜] [剪辑] [Merge]  (4 个选项卡，互斥显示, Phase 3.5.2)
  TranscodeForm.vue      - 3 列布局，分辨率拆分为 W/H (Phase 3.5.2)
  FilterForm.vue         - 3 列布局，水印冻结+全屏拖放 (Phase 3.5.2)
  ClipForm.vue           - H:MM:SS:ms 时间拆分 (Phase 3.5.2)
  MergeSettingsForm.vue  - Intro/Outro + 拼接设置 (Phase 3.5.2)
```

**音频/字幕独立页面** (`AudioSubtitlePage.vue`) (Phase 3.5 新增):

```
AudioSubtitlePage
  CommandPreview.vue     - 独立命令预览
  AvsmixForm.vue         - 音频/字幕各占半屏，全屏拖放 (Phase 3.5.1)
```

**拼接独立页面** (`MergePage.vue`) (Phase 3.5 新增, Phase 3.5.2 简化, Phase 3.5.2-fixes 隔离):

```
MergePage
  CommandPreview.vue     - 独立命令预览（使用本地 mergeConfig，不是全局共享 merge）
  MergePanel.vue         - 文件列表 + 拼接模式 (W/H 分离输入)
  "Add to Queue" Button  - 添加 ONE 合并任务（非每个文件一个任务），自动跳转 Queue 页面
```

**配置隔离** (Phase 3.5.2-fixes):
- 使用本地 `reactive<MergeConfigDTO>` 作为 merge 配置，不引用全局 `merge` 单例
- 默认 merge_mode: `concat_protocol`
- `handleAddToQueue` 构建纯净 config：仅继承全局 `transcode` + `filters`，不继承全局 `merge`（intro/outro）
- 添加任务后通过 `router.push("/task-queue")` 自动跳转到 Queue 页面

<!-- v2.1.0-CHANGE: Phase 3.5.2 新增 SplitDropZone 文档 -->

**SplitDropZone 组件** (`SplitDropZone.vue`):

左右分屏全屏拖拽包装组件。

**路径**: `frontend/src/components/common/SplitDropZone.vue`

**Props**:

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `leftLabel` | `string` | `"Left"` | 左半屏拖拽区标签 |
| `rightLabel` | `string` | `"Right"` | 右半屏拖拽区标签 |
| `leftAccept` | `string` | `""` | 左侧接受的文件扩展名 |
| `rightAccept` | `string` | `""` | 右侧接受的文件扩展名 |

**Events**:

| 事件 | 参数 | 说明 |
|------|------|------|
| `drop-left` | `path: string` | 文件拖入左半屏时触发 |
| `drop-right` | `path: string` | 文件拖入右半屏时触发 |

**Slots**:

| Slot | 说明 |
|------|------|
| `left` | 左半屏内容 |
| `right` | 右半屏内容 |

**行为**:
- 注册 document 级 dragenter/dragover/dragleave/drop 事件监听
- 拖入时显示全屏左右分屏遮罩，带标签提示
- drop 时根据鼠标 X 坐标判断左/右半屏，触发对应事件
- onUnmounted 清理事件监听

**自定义命令页面** (`CustomCommandPage.vue`) (Phase 3.5 新增, Phase 3.5.2-fixes 改进):

```
CustomCommandPage
  CommandPreview.vue     - 标准命令预览（通过 useCommandPreview + build_command_preview）
  Raw Args Textarea      - 原始 FFmpeg 参数输入
```

**编码器选择组件** (`EncoderSelect.vue`):

**路径**: `frontend/src/components/config/EncoderSelect.vue`

| Prop | 类型 | 说明 |
|------|------|------|
| `modelValue` | `string` | 当前选中的编码器名称 |
| `category` | `'video' \| 'audio'` | 编码器类别 |
| `supportedEncoders` | `string[]` | 当前 FFmpeg 支持的编码器列表 |

**Events** (Phase 3.5 扩展):

| 事件 | 参数 | 说明 |
|------|------|------|
| `update:modelValue` | `value: string` | 编码器名称变更 |
| `qualityChange` | `{ quality: number, mode: string } \| null` | 预设编码器的推荐质量值（自定义编码器返回 null） |

**行为**:
- 编码器按优先级分组显示（首选/次选/条件）
- 不在 `supportedEncoders` 中的硬件编码器灰显并标注"未检测到"
- 选择编码器后自动填充推荐质量值和质量模式到父组件
<!-- v2.1.0-CHANGE: Phase 3.5 新增自定义编码器输入 -->
- 底部提供 "Other (custom name)..." 选项，选中后显示文本输入框
- 自定义编码器跳过硬件检测，不自动填充质量参数

**文件列表面板** (`MergeFileList.vue`):

**路径**: `frontend/src/components/config/MergeFileList.vue`

| Prop | 类型 | 说明 |
|------|------|------|
| `modelValue` | `string[]` | 文件路径列表（v-model） |

**行为** (Phase 3.5.2-fixes):
- [添加文件] / [上移] / [下移] / [移除] 操作按钮
- 每行显示序号、文件名、移除按钮
- 支持拖拽排序（HTML5 drag-and-drop）
- 支持全屏拖拽上传（document 级 drag 事件监听，80ms 延迟后调用 `get_dropped_files`）
- 允许重复文件添加（不下重过滤）
- 至少需要 2 个文件

### Bridge API 新增

<!-- v2.1.0-CHANGE: Phase 3 新增 Bridge API -->

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `check_hw_encoders` | - | `string[]` | 检测 FFmpeg 支持的编码器列表（直接返回数组） |
| `get_file_duration` | `file_path: str` | `float` | 获取文件时长（秒），直接返回数值 |

| 修改方法 | 变更说明 |
|---------|---------|
| `build_command` | 支持 audio_normalize, aspect_convert, clip, avsmix, merge, custom_command 参数 |
| `validate_config` | 增加新参数的验证规则 |

---

## Phase 3.5: 命令构建改进

<!-- v2.1.0-CHANGE: Phase 3.5 新增命令构建改进架构 -->

### 路由扩展

| 路径 | 名称 | 组件 | 说明 |
|------|------|------|------|
| `/` | TaskQueue | `TaskQueuePage.vue` | 任务队列（不变） |
| `/config` | CommandConfig | `CommandConfigPage.vue` | 转码/滤镜/剪辑（仅 3 个选项卡） |
| `/audio-subtitle` | AudioSubtitle | `AudioSubtitlePage.vue` | 音频/字幕独立页面 |
| `/merge` | Merge | `MergePage.vue` | 拼接独立页面 |
| `/custom-command` | CustomCommand | `CustomCommandPage.vue` | 自定义命令页面 |
| `/settings` | Settings | `SettingsPage.vue` | 设置（不变） |

### command_builder.py Phase 3.5 扩展

**新增转码参数注册**:

| 参数 | 映射 | 条件 |
|------|------|------|
| quality_mode | `-crf N` / `-cq N` / `-qp N` | video_codec 非 copy/none |
| preset | `-preset val` | video_codec 非 copy/none |
| pixel_format | `-pix_fmt val` | video_codec 非 copy/none |
| max_bitrate | `-maxrate val -bufsize N` | video_codec 非 copy/none, bufsize 可配置 (Phase 3.5.1) |
| bufsize | `-bufsize val` (跟随 max_bitrate) | video_codec 非 copy/none (Phase 3.5.1) |

**新增命令构建函数**:

| 函数 | 用途 |
|------|------|
| `build_merge_intro_outro_command()` | 片头片尾拼接：3-input filter_complex concat |
| `build_custom_command()` | 自定义命令：直接注入用户原始参数 |

**命令构建优先级**: custom_command > clip > merge > 默认转码

### TranscodeForm.vue 扩展 (Phase 3.5)

**新增 UI 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| Quality Mode | select | crf / cq / qp，自动填充 |
| Quality Value | number | 0-51 数值，自动填充 |
| Preset | select | ultrafast ~ veryslow |
| Pixel Format | combo | yuv420p / yuv420p10le / yuv422p / yuv444p |
| Max Bitrate | input | 最大码率，如 8M |
| Buffer Size | input | 缓冲区大小，如 2M（Phase 3.5.1） |

**字段顺序** (Phase 3.5.1 重新排序):

VC -> QM -> QV -> Resolution -> Framerate -> VB -> MB -> Bufsize -> EP -> PF -> Audio -> Output

**行为**:
- 选择预设编码器时，`qualityChange` 事件自动填充 Quality Mode 和 Value
- 切换到 copy/none 时清空所有质量字段
- 自定义编码器不触发自动填充
- Bufsize 仅在 Max Bitrate 已设置时显示（Phase 3.5.1）
- 音频码率默认值改为 128k（Phase 3.5.1）

---

## Phase 3.5.1: Bug 修复与 UX 改进

<!-- v2.1.0-CHANGE: Phase 3.5.1 新增 bug 修复与 UX 改进架构 -->

### 路径引用

所有命令构建函数（`build_command`, `build_clip_command`, `build_merge_command`, `build_avsmix_command`, `build_merge_intro_outro_command`, `build_custom_command`）统一使用 `shlex.quote()` 引用文件路径，确保含空格路径正确解析。

### 滤镜互斥修复

FilterForm 中 Rotate 和 Aspect Convert 互斥逻辑修改：
- 使用 `watch` 自动清理：选择一方时清空另一方
- 简化 disabled 条件，避免两个选项同时冻结

### MergePanel 分辨率输入

target_resolution 从单一文本输入改为 W x H 双数字输入框，默认值 1920x1080 通过 `computed` get/set 实现。

### FileDropInput 全屏拖放

新增 `fullscreenDrop` prop，启用后注册 document 级 drag 事件监听，拖入时显示全屏遮罩层（类似 TaskQueuePage 的 drag overlay），适用于水印和 A/V Mix 场景。

### 页面布局变更

| 页面 | 变更 |
|------|------|
| CommandConfigPage | 选项卡互斥显示，表单 3 列网格布局 |
| MergePage | 新增 "Add to Queue" 按钮 |
| AudioSubtitlePage | 音频/字幕各占半屏 |
| FilterForm | 水印支持全屏拖放 |

<!-- v2.1.0-CHANGE: Phase 4 新增章节 -->

## Phase 4: 国际化与平台化

### i18n 国际化架构

**框架**: vue-i18n v9+，Composition API 模式（`legacy: false`）

**目录结构**:
```
frontend/src/
  i18n/
    index.ts              # createI18n 实例，注册到 Vue app
    locales/
      zh-CN.ts            # 中文翻译键（~200 keys）
      en.ts               # 英文翻译键（~200 keys）
  composables/
    useLocale.ts          # 语言切换 composable（持久化到后端）
```

**翻译键命名空间**: `{section}.{key}`，使用扁平点分隔格式

| 命名空间 | 覆盖范围 |
|---------|---------|
| `nav.` | 导航栏（队列、配置、A/V Mix、Merge、Custom、Settings） |
| `ffmpeg.` | FFmpeg 设置（状态、版本选择、下载、确认对话框） |
| `settings.` | 设置页面（工作线程、输出目录、关于信息） |
| `taskQueue.` | 任务队列（工具栏、批量操作、任务状态、进度、日志） |
| `config.` | 命令配置（转码、滤镜、剪辑、编码器、预设） |
| `avMix.` | 音频字幕混合页 |
| `merge.` | 多视频拼接页 |
| `custom.` | 自定义命令页 |
| `common.` | 通用字符串（确认、取消、加载、清除等） |

**useLocale.ts**:
- 路径: `frontend/src/composables/useLocale.ts`
- 类型: `LocaleValue = "zh-CN" \| "en"`
- 返回: `currentLocale`, `setLocale`
- 行为: 调用 `save_settings({ language })` 持久化，更新 vue-i18n 全局 locale

**语言切换 UI**:
- 位置: AppNavbar.vue 导航栏右侧，主题切换按钮旁
- 样式: `btn btn-ghost btn-sm btn-square`
- 行为: 显示当前语言代码（CN/EN），点击切换

### 数据目录统一

**新增模块**: `core/paths.py` - 集中路径管理

| 函数 | 返回值 | 说明 |
|------|--------|------|
| `get_app_dir()` | `Path` | 打包时为 exe 所在目录，开发时为项目根目录 |
| `get_data_dir()` | `Path` | `get_app_dir() / "data"`，自动创建 |
| `get_settings_path()` | `Path` | `get_data_dir() / "settings.json"` |
| `get_log_dir()` | `Path` | `get_data_dir() / "logs"` |
| `get_presets_dir()` | `Path` | `get_data_dir() / "presets"` |
| `migrate_if_needed()` | `None` | 首次启动迁移旧 APPDATA 数据 |

**迁移策略**: copy-not-move
- 检测新路径不存在且旧路径存在时执行
- 复制 settings.json 和 presets/ 到新路径
- 日志不迁移（轮转制自动清理）
- 旧文件保留作为备份

**模块依赖变更**:
| 模块 | 变更 |
|------|------|
| `core/config.py` | 移除 `_appdata_dir()`/`_settings_path()`/`_ensure_dir()`，改用 `core.paths` |
| `core/logging.py` | 移除 `_ensure_log_dir()`，改用 `core.paths` |
| `core/preset_manager.py` | 移除 `_get_user_presets_dir()`，改用 `core.paths` |
| `main.py` | 启动时在所有 core 模块导入前调用 `migrate_if_needed()` |

### 平台检测增强

**core/app_info.py 变更**:
- `get_app_info()` 返回值新增 `"platform": sys.platform`（"win32" / "darwin" / "linux"）

**main.py download_ffmpeg() 变更**:
- 非 Windows 返回 `{"success": False, "error": "download_not_supported", "data": {"platform": ..., "instructions": {...}}}`
- 新增 `_get_ffmpeg_install_instructions()` 返回平台特定安装命令

---

## Phase 5: 第二阶段用户体验优化

<!-- v2.1.0-CHANGE: Phase 5 新增队列布局重构、打开文件夹 API、按钮升级等架构 -->

### 队列表格布局重构

**TaskList.vue 变更**:
- 移除"信息"列（Info），duration 和 file_size 合并显示到文件名列中
- 列宽: Checkbox `w-10 shrink-0` / File `min-w-0`（弹性） / State `w-20 shrink-0` / Progress `w-44 shrink-0` / Actions `w-52 shrink-0`
- 容器: `overflow-hidden`（禁止横向滚动）
- 文件名列: 内部 `min-w-0 flex-1` + `truncate` 截断长文件名

**TaskRow.vue 变更**:
- 文件列信息合并: 文件名 + duration + file_size 均在同一 `<td>` 中，使用 `opacity-50` 次要文本
- 操作列: `shrink-0 whitespace-nowrap`，固定宽度防止按钮跳位
- 所有操作按钮统一升级为 `btn-sm`

**TaskProgressBar.vue 变更**:
- 进度条容器: `shrink-0 w-20`
- 所有数值指标: `shrink-0` + `tabular-nums`（等宽数字对齐）

### 打开文件夹功能

**Bridge API - open_folder**:

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `open_folder` | `path: str` | `{success: bool, error?: str, data: null}` | 在系统文件管理器中打开指定路径 |

**跨平台实现** (main.py):
- Windows: `os.startfile(folder)`
- macOS: `subprocess.Popen(["open", folder])`
- Linux: `subprocess.Popen(["xdg-open", folder])`

**前端集成** (TaskRow.vue):
- `v-if="task.state === 'completed' && task.output_path"` 条件渲染
- 点击调用 `call("open_folder", task.output_path)`
- 失败时静默处理（console error，不弹提示）

### 任务状态变更重新获取

**useTaskQueue.ts 变更**:
- `task_state_changed` 事件处理器新增逻辑：当 `new_state === "completed" || new_state === "failed"` 时调用 `fetchTasks()`
- 原因: 事件仅携带 `{task_id, old_state, new_state}`，不包含后端设置的 `output_path`、`error` 等字段
- 效果: completed 任务立即显示"打开文件夹"按钮，无需手动刷新页面

### 前端设计一致性

**统一的卡片样式**:
- 所有 `.card` 组件: `card bg-base-200 shadow-sm border border-base-300`

**统一的页面布局**:
- 页面标题: `text-xl font-bold tracking-tight`
- 页面描述: `text-sm text-base-content/60`

**统一的导航栏**:
- 容器: `border-b border-base-300`
- 品牌名: `text-base tracking-tight`
- 导航项间距: `gap-0.5`
- 右侧控件间距: `gap-1.5`

**统一的 Badge 样式**:
- 所有状态 badge: `badge-sm`
- 队列摘要 badge: `badge-sm`
