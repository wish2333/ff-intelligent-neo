# 系统架构

## 版本变更索引

<!-- 本文件按功能模块组织，每条变更标注对应版本 -->

| 版本 | 变更模块 | 说明 |
|------|---------|------|
| v2.1.0 | 整体结构 | 初始架构文档 |
| v2.1.0 / Phase 3 | 编码器数据库 | 新增前端编码器注册表 |
| v2.1.0 / Phase 3 | command_builder.py 扩展 | 新增滤镜、剪辑、拼接、A/V Mix 构建函数 |
| v2.1.0 / Phase 3 | 数据模型扩展 | FilterConfig、ClipConfig、MergeConfig、AudioSubtitleConfig |
| v2.1.0 / Phase 3 | 新增前端组件 | EncoderSelect、ClipForm、MergeFileList、AvsmixForm 等 |
| v2.1.0 / Phase 3 | Bridge API 新增 | check_hw_encoders、get_file_duration、build_command 扩展 |
| v2.1.0 / Phase 3.5 | 路由扩展 | 新增 /audio-subtitle、/merge、/custom-command 路由 |
| v2.1.0 / Phase 3.5 | 命令构建改进 | 转码参数注册、片头片尾、自定义命令 |
| v2.1.0 / Phase 3.5 | TranscodeForm 扩展 | Quality Mode/Value、Preset、Pixel Format 等字段 |
| v2.1.0 / Phase 3.5.1 | 路径引用修复 | 移除 shlex.quote，改用 _subprocess_quote |
| v2.1.0 / Phase 3.5.1 | 滤镜互斥修复 | Rotate 和 Aspect Convert 互斥逻辑 |
| v2.1.0 / Phase 3.5.2 | SplitDropZone 组件 | 左右分屏全屏拖拽组件 |
| v2.1.0 / Phase 3.5.2 | Merge 独立提交 | 隔离 merge 配置，不引用全局单例 |
| v2.1.0 / Phase 4 | i18n 国际化架构 | vue-i18n、翻译键命名空间、useLocale |
| v2.1.0 / Phase 4 | 数据目录统一 | 新增 core/paths.py 集中路径管理 |
| v2.1.0 / Phase 4 | 平台检测增强 | download_ffmpeg 非 Windows 返回安装指引 |
| v2.1.0 / Phase 5 | 队列表格布局重构 | TaskList/TaskRow/TaskProgressBar 变更 |
| v2.1.0 / Phase 5 | 打开文件夹功能 | open_folder Bridge API 及前端集成 |
| v2.1.0 / Phase 5 | 任务状态变更重新获取 | completed/failed 时 fetchTasks() |
| v2.1.1 | useCommandPreview 优化 | 合并 IPC、竞态保护、in-flight 保护 |
| v2.1.1 | configRef 模式感知确认 | 审查通过，无需修改 |
| v2.1.1 | MergeFileList 优化 | dragover 节流、key 修复 |
| v2.1.1 | Bridge API 变更 | 新增 preview_command，修改 validate_config/add_tasks |
| v2.1.1 | Bridge 事件处理类型安全 | task_state_changed 等事件添加运行时类型守卫 |
| v2.1.1 | bridge.ts 类型安全 | call 返回 unknown + 泛型，替代 any |
| v2.1.1 | 前端组件变更 | 错误反馈、确认对话框、复制反馈等 |
| v2.2.0 / Phase 1 | auto-editor 后端基础 | 新增 auto_editor_runner.py、auto_editor_api.py，AppSettings 扩展，task_runner 自动剪辑调度 |
| v2.2.0 / Phase 1 | 数据模型扩展 | AppSettings 新增 auto_editor_path 字段 |
| v2.2.0 / Phase 2 | 前端页面与路由 | 新增 /auto-cut 路由、AutoCutPage.vue、useAutoEditor.ts composable |
| v2.2.0 / Phase 2 | 导航栏扩展 | AppNavbar.vue 新增 AutoCut 导航项 + auto-editor 状态徽标 |
| v2.2.0 / Phase 2 | CommandPreview 扩展 | CommandPreview.vue 新增 type prop 支持 auto-editor 命令预览 |
| v2.2.0 / Phase 2 | 国际化扩展 | en.ts / zh-CN.ts 新增 nav.autoCut 及 auto-cut 相关翻译键 |
| v2.2.0 / Phase 2 | FileDropInput 扩展 | 新增 multiple prop，AutoCut 页面使用 :multiple="true" 支持多文件 |
| v2.2.0 / Phase 3 | BasicTab 组件 | 新建 BasicTab.vue，包含编辑方法/阈值/独立speed-volume动作值/编码器选择，从 AutoCutPage 提取 |
| v2.2.0 / Phase 3 | useAutoEditor 扩展 | silentSpeed/Volume + normalSpeed/Volume 独立 ref，selectedFile watch，immediate 预览 |
| v2.2.0 / Phase 3 | i18n 扩展 | en.ts/zh-CN.ts 新增 speed/volume/encoder 翻译键 |
| v2.2.0 / Phase 4 | AdvancedTab 组件 | 新建 AdvancedTab.vue，Actions/Timeline/Switches(8合1)/Video/Audio/Output 分区，curated encoder 列表 |
| v2.2.0 / Phase 4 | autoEditorEncoders 数据 | 新建 autoEditorEncoders.ts，静态 curated 编码器列表（推荐/硬件加速/其他/自定义） |
| v2.2.0 / Phase 4 | useAutoEditor 简化 | 移除 encoderLists/fetchEncoders，编码器改为静态列表 |
| v2.2.0 / Phase 4 | i18n 扩展 | en.ts/zh-CN.ts 新增 AdvancedTab switches 翻译键 |
| v2.2.0 / Phase 7-11 | 命令构建修正 | --edit audio:THRESHOLD 格式替代 --my-thresh，placeholder 预览支持 |
| v2.2.0 / Phase 7-11 | 任务调度修正 | retry_task/reset_task 增加 auto_editor task_type 检查 |
| v2.2.0 / Phase 5 | AutoEditorSetup 组件 | 新建 AutoEditorSetup.vue，auto-editor 路径设置与版本检测，集成到 SettingsPage |
| v2.2.0 / Phase 5 | FileDropInput 扩展 | 新增 multiple prop，支持单文件约束模式 |
| v2.2.0 / Phase 5 | TaskDTO 扩展 | 新增 task_type 字段，TaskRow 区分 auto_editor / ffmpeg 任务类型 |
| v2.2.0 / Phase 5 | i18n 扩展 | en.ts/zh-CN.ts 新增 settings.autoEditor、任务类型标签翻译键 |
| v2.2.0 / Phase 6 | 集成测试指南 | 新建 test-guide-2.2.0.md，覆盖后端与前端全阶段手动测试项 |

---

## 整体结构

```
ff-intelligent-neo/
├── main.py                 # 后端入口，Bridge API 定义
├── core/                   # 核心业务逻辑
│   ├── models.py           # 数据模型（Task, TaskState, TranscodeConfig 等）
│   ├── task_runner.py      # 任务执行、暂停/恢复/终止/重置
│   ├── command_builder.py  # FFmpeg 命令构建
│   ├── auto_editor_runner.py  # auto-editor 命令构建、输入验证、进度解析 (v2.2.0)
│   ├── auto_editor_api.py  # auto-editor Bridge API 类 (v2.2.0)
│   ├── ffmpeg_setup.py     # FFmpeg 下载/检测/版本管理
│   ├── paths.py           # 路径管理（Phase 4 新增）
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
│   │   │   ├── auto-cut/     # 自动剪辑组件（v2.2.0 Phase 2）
│   │   │   │   ├── BasicTab.vue          # 基础选项卡（Phase 3）
│   │   │   │   └── AdvancedTab.vue       # 高级选项卡（Phase 4）
│   │   │   ├── settings/   # 设置相关组件
│   │   │   │   ├── FFmpegSetup.vue    # FFmpeg 管理面板
│   │   │   │   └── AutoEditorSetup.vue # auto-editor 路径设置面板（v2.2.0 Phase 5）
│   │   │   └── task-queue/ # 任务队列组件
│   │   │       ├── TaskList.vue       # 任务列表
│   │   │       ├── TaskRow.vue        # 单行任务
│   │   │       └── TaskProgressBar.vue # 进度条
│   │   ├── composables/   # Vue Composables
│   │   │   ├── useTaskControl.ts      # 任务控制 API
│   │   │   ├── useSettings.ts         # 设置管理
│   │   │   ├── useTheme.ts            # 主题切换管理
│   │   │   ├── useLocale.ts           # 语言切换（Phase 4）
│   │   │   ├── useGlobalConfig.ts     # 全局配置 + configRef
│   │   │   ├── useCommandPreview.ts   # 命令预览（v2.1.1 优化）
│   │   │   └── useAutoEditor.ts       # auto-editor 状态与预览（v2.2.0 Phase 2）
│   │   ├── pages/         # 页面组件
│   │   │   ├── TaskQueuePage.vue
│   │   │   ├── CommandConfigPage.vue
│   │   │   ├── AudioSubtitlePage.vue  # 音频/字幕独立页面（Phase 3.5）
│   │   │   ├── MergePage.vue          # 拼接独立页面（Phase 3.5）
│   │   │   ├── CustomCommandPage.vue  # 自定义命令页面（Phase 3.5）
│   │   │   ├── AutoCutPage.vue          # 自动剪辑页面（v2.2.0 Phase 2）
│   │   │   └── SettingsPage.vue
│   │   ├── data/          # 静态数据（Phase 3）
│   │   │   ├── encoders.ts                # FFmpeg 编码器注册表
│   │   │   └── autoEditorEncoders.ts      # Auto-Editor 编码器注册表 (v2.2.0 Phase 4)
│   │   ├── types/         # TypeScript 类型定义
│   │   └── style.css      # 全局样式（DaisyUI 主题配置）
│   └── index.html
├── docs/                   # 设计文档
│   ├── StateMachine.md     # 状态机定义
│   ├── BusinessRules.md    # 业务规则
│   ├── Structure.md        # 本文件
│   ├── Procedure.md        # 业务流程
│   └── fields/             # 数据模型字段定义
├── references/             # 参考文档
│   ├── PRD-2.2.0.md        # Auto-Editor 集成 PRD (v2.2.0)
│   └── test-guide-2.2.0.md # 集成测试指南 (v2.2.0 Phase 6)
```

---

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
| `multiple` | `boolean` | `true` | 是否允许多文件（v2.2.0 Phase 5 新增） |

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

**Phase 5 扩展: 多文件支持**:
- `multiple=true`（默认）时，拖拽和文件对话框均支持多文件，逐个 emit
- `multiple=false` 时，拖拽或选择多个文件显示错误提示 "Please select only one file"
- `AutoCutPage.vue` 使用 `:multiple="true"` 支持多文件输入，命令预览使用占位文件
- 现有多文件使用场景不受影响（`FilterForm.vue` 等默认 `multiple=true`）

---

### SplitDropZone.vue

<!-- v2.1.0-CHANGE: Phase 3.5.2 新增 SplitDropZone 文档 -->

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

**使用场景**:
- `FilterForm.vue` 水印全屏拖放（Phase 3.5.1）
- `FilterForm.vue` Intro/Outro 左右分屏拖放（Phase 3.5.2）
- `AudioSubtitlePage.vue` 音频/字幕各占半屏（Phase 3.5）

---

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

---

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
| `pauseAll` | - | `pause_all` | 暂停所有任务 |
| `resumeAll` | - | `resume_all` | 恢复所有任务 |

---

### useCommandPreview.ts

<!-- v2.1.0-CHANGE: Phase 3 初始实现 -->
<!-- v2.1.1-CHANGE: 重写优化，合并 IPC、竞态保护、in-flight 保护 -->

**路径**: `frontend/src/composables/useCommandPreview.ts`

**v2.1.0 现状**:
- `watch(configRef, scheduleUpdate, { deep: true, immediate: true })`
- 300ms debounce，无 in-flight 保护
- 两次独立 IPC 调用: `validate_config` + `build_command`（`Promise.all`）
- 无请求竞态保护，快速输入可能导致慢响应覆盖新结果

**v2.1.1 变更**:

| 优化项 | 变更内容 |
|--------|---------|
| 合并 IPC | 单次 `preview_command` 调用替代 `Promise.all([validate_config, build_command])` |
| 竞态保护 | 单调递增 `requestId`，丢弃过期响应（`myId !== requestId` 时 return） |
| watch 策略 | 移除 `deep: true`（configRef 是 computed，Vue 已自动追踪依赖） |
| debounce | 300ms -> 500ms |
| in-flight 保护 | `validating` 标志 + `pendingUpdate` 标志，请求进行中时标记 pending 而非堆积请求 |
| 批量字段赋值 | TranscodeForm/FilterForm/MergePanel 中多字段清空改为 `Object.assign` 原子操作 |

**返回值变更**:

```typescript
// v2.1.0
const [valRes, cmdRes] = await Promise.all([
  call<{ errors: string[]; warnings: string[] }>("validate_config", config),
  call<string>("build_command", config),
])

// v2.1.1
const res = await call<{
  command: string
  errors: Array<{ param: string; message: string }>
  warnings: Array<{ param: string; message: string }>
}>("preview_command", config)
```

---

### useGlobalConfig.ts / configRef

<!-- v2.1.0-CHANGE: Phase 3 初始实现 -->
<!-- v2.1.1-CHANGE: 模式感知确认，审查通过 -->

**路径**: `frontend/src/composables/useGlobalConfig.ts`

**v2.1.0 现状**: `configRef` computed 已按 `activeMode` 过滤子配置（transcode + filters 始终包含，clip/merge/avsmix/custom 仅在对应 mode 时包含）。

**v2.1.1 确认**: 经审查 `configRef` 已正确实现模式感知过滤，无需修改。全局 intro/outro 通过独立的 watch 在 `merge` 子配置中设置，不影响模式感知逻辑。

---

### useLocale.ts

<!-- v2.1.0-CHANGE: Phase 4 新增 -->

**路径**: `frontend/src/composables/useLocale.ts`

**类型**: `LocaleValue = "zh-CN" | "en"`

**返回**: `currentLocale`, `setLocale`

**行为**: 调用 `save_settings({ language })` 持久化，更新 vue-i18n 全局 locale。


### useAutoEditor.ts

<!-- v2.2.0-CHANGE: Phase 2 新增 -->

**路径**: `frontend/src/composables/useAutoEditor.ts`

**状态**:

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `editMethod` | `Ref<'audio' | 'motion'>` | `'audio'` | 编辑方法（subtitle 隐藏） |
| `audioThreshold` | `Ref<number>` | `0.04` | 音频阈值（range 0.01-0.20） |
| `motionThreshold` | `Ref<number>` | `0.02` | 运动阈值（range 0.01-0.20） |
| `whenSilentAction` | `Ref<string>` | `'cut'` | 静音时动作 |
| `whenNormalAction` | `Ref<string>` | `'nil'` | 正常时动作 |
| `margin` | `Ref<string>` | `'0.2s'` | 边距 |
| `smooth` | `Ref<string>` | `'0.2s,0.1s'` | 平滑参数 |
| `silentSpeedValue` | `Ref<number>` | `4` | 静音时 speed action 值 |
| `silentVolumeValue` | `Ref<number>` | `0.5` | 静音时 volume action 值 |
| `normalSpeedValue` | `Ref<number>` | `4` | 正常时 speed action 值 |
| `normalVolumeValue` | `Ref<number>` | `0.5` | 正常时 volume action 值 |
| `advancedOptions` | `Ref<AdvancedOptions>` | `{...}` | 高级选项（含 videoCodec/audioCodec 等） |
| `commandPreview` | `Ref<string>` | `''` | 命令预览文本（immediate + debounced） |
| `autoEditorStatus` | `Ref<{available, compatible, version, path}>` | `{available: false, ...}` | auto-editor 可用状态 |
| `selectedFile` | `Ref<string | null>` | `null` | 已选输入文件路径（AutoCutPage watcher 同步） |
| `initializing` | `Ref<boolean>` | `true` | 初始化标志，防止状态栏闪烁 |

**方法**:

| 方法 | 说明 | 后端 API |
|------|------|---------|
| `fetchStatus()` | 获取 auto-editor 可用状态 | `get_auto_editor_status` |
| `setPath(path)` | 设置并验证 auto-editor 路径 | `set_auto_editor_path` |
| `updatePreview()` | 更新命令预览（300ms debounce，immediate 触发） | `preview_auto_editor_command` |
| `addToQueue()` | 验证参数并添加任务到队列 | `add_auto_editor_task` |
| `buildParams(inputFile?)` | 构建命令参数字典 | - |

**行为**:
- `fetchStatus()` 在 `init()` 时调用，`initializing` 在 try/finally 中设为 false
- `updatePreview()` 通过 `watch` 监听所有参数 + selectedFile 变化，`{ immediate: true }` 立即触发
- 切换 `editMethod` 时自动切换阈值值（audio 0.04 <-> motion 0.02）
- speed/volume 输入独立分离：silent 和 normal 各自拥有独立的 speed/volume ref
- 编码器选择使用静态 curated 列表（`autoEditorEncoders.ts`），无动态查询
---

## 后端核心

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

---

### command_builder.py

**路径**: `core/command_builder.py`

**现有架构**（保持不变）:
- 注册表模式：`_transcode_params` 和 `_filters` 字典管理可扩展参数
- 优先级排序：滤镜按 priority 数值排序构建链。

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
| `build_merge_intro_outro_command()` | 片头片尾拼接：3-input filter_complex concat | Phase 3.5 |
| `build_custom_command()` | 自定义命令：直接注入用户原始参数 | Phase 3.5 |

**命令构建优先级**: custom_command > clip > merge > 默认转码

**Phase 3.5 扩展 - 转码参数注册**:

| 参数 | 映射 | 条件 |
|------|------|------|
| quality_mode | `-crf N` / `-cq N` / `-qp N` | video_codec 非 copy/none |
| preset | `-preset val` | video_codec 非 copy/none |
| pixel_format | `-pix_fmt val` | video_codec 非 copy/none |
| max_bitrate | `-maxrate val -bufsize N` | video_codec 非 copy/none, bufsize 可配置 (Phase 3.5.1) |
| bufsize | `-bufsize val` (跟随 max_bitrate) | video_codec 非 copy/none (Phase 3.5.1) |

**Phase 3.5.2-fixes 路径引用变更**:
- 移除所有 `shlex.quote()` 调用，替换为 `_subprocess_quote()`（no-op）
- 原因：subprocess.Popen 以列表传递参数时不需要 shell 级别引用
- `shlex.quote` 在 Windows 上产生单引号包裹，导致 Unicode 文件名报 "Illegal byte sequence"
- 新增 `_subprocess_quote()` 和 `_preview_quote()` 辅助函数
- 所有子 builder 函数移除 `-hide_banner -y`（由 `ffmpeg_runner.py` 统一添加）

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

---

### models.py（数据模型）

<!-- v2.1.0-CHANGE: Phase 3 新增数据模型 -->
<!-- v2.1.0-CHANGE: Phase 3.5 新增数据模型 -->
<!-- v2.1.0-CHANGE: Phase 3.5.1 MergeConfig 默认值变更 -->

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
    target_resolution: str = "1920x1080"  # Phase 3.5.1 默认 1920x1080 (原空字符串)
    target_fps: int = 30                  # Phase 3.5.1 默认 30 (原 0)
    transcode_config: dict = field(default_factory=dict)
    intro_path: str = ""                # Phase 3.5: 片头视频路径
    outro_path: str = ""                # Phase 3.5: 片尾视频路径

@dataclass(frozen=True)
class AudioSubtitleConfig:
    external_audio_path: str = ""
    subtitle_path: str = ""
    subtitle_language: str = ""
    replace_audio: bool = True

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

---

### paths.py

<!-- v2.1.0-CHANGE: Phase 4 新增模块 -->

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

---

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

#### task_info_updated（v2.1.1 新增）

| 属性 | 说明 |
|------|------|
| 事件名 | `task_info_updated` |
| 数据 | `{task_id: str, file_name: str, duration_seconds: float, file_size_bytes: int}` |
| 触发时机 | 后台 probe_file 完成后逐个触发 |

---

### Bridge API 新增（Phase 3）

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

### Bridge API 变更（v2.1.1）

<!-- v2.1.1-CHANGE: 新增 preview_command API，修改 validate_config 返回格式，修改 add_tasks 行为 -->

#### 新增 API: preview_command

| 属性 | 说明 |
|------|------|
| 方法名 | `preview_command` |
| 参数 | `config: dict` |
| 返回 | `{success: bool, data: {command: str, errors: [{param: str, message: str}], warnings: [{param: str, message: str}]}}` |
| 说明 | 合并 `build_command` + `validate_config`，单次 IPC 往返 |
| preview_mode | 内部调用 `validate_task_config(task_config, preview_mode=True)`，跳过 watermark 文件存在性检查 |

**后端实现**: `main.py`

```python
@expose
def preview_command(self, config: dict) -> dict:
    """合并命令预览和参数校验，单次 IPC 返回全部结果。"""
    try:
        tc = TaskConfig.from_dict(config)
        from core.command_builder import validate_config, ValidationContext, build_command_preview
        ctx = ValidationContext(preview_mode=True)
        issues = validate_config(tc, ctx)
        errors = [{"param": i["param"], "message": i["message"]} for i in issues if i["level"] == "error"]
        warnings = [{"param": i["param"], "message": i["message"]} for i in issues if i["level"] == "warning"]
        command = build_command_preview(tc)
        return {"success": True, "data": {"command": command, "errors": errors, "warnings": warnings}}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
```

#### 修改 API: validate_config

| 属性 | v2.1.0 | v2.1.1 |
|------|--------|--------|
| 返回 errors | `string[]` | `[{param: string, message: string}]` |
| 返回 warnings | `string[]` | `[{param: string, message: string}]` |

#### 修改 API: add_tasks

| 属性 | v2.1.0 | v2.1.1 |
|------|--------|--------|
| probe_file | 同步阻塞，逐个文件 probe | 后台线程批量 probe，主线程立即返回占位任务 |
| task_info_updated 事件 | 无 | probe 完成后逐个触发 |

#### 新增 API: open_folder（Phase 5）

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `open_folder` | `path: str` | `{success: bool, error?: str, data: null}` | 在系统文件管理器中打开指定路径 |

**跨平台实现** (main.py):
- Windows: `os.startfile(folder)`
- macOS: `subprocess.Popen(["open", folder])`
- Linux: `subprocess.Popen(["xdg-open", folder])`

---

### AutoEditorApi Bridge（v2.2.0）

<!-- v2.2.0-CHANGE: 新增 AutoEditorApi Bridge 文档 -->

独立于 `FFmpegApi` 的第二个 Bridge 类，注册于 `main.py`。

#### 事件: auto_editor_version_changed

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `string` | auto-editor 版本号（如 "30.1.4"） |
| `path` | `string` | auto-editor 二进制路径 |
| `status` | `string` | `"ready"` / `"not_found"` / `"incompatible"` |

#### API 方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `set_auto_editor_path` | `path: str` | `{success, data: {version, path}}` | 验证二进制（`--version`），保存到 AppSettings |
| `get_auto_editor_status` | - | `{success, data: {available, compatible, version, path}}` | 检查路径、版本兼容性（>=30.1.0, <31.0.0） |
| `get_auto_editor_encoders` | `output_format: str` | `{success, data: {video: [...], audio: [...], subtitle: [...], other: [...]}}` | 查询 `auto-editor info -encoders <fmt>` |
| `add_auto_editor_task` | `input_file: str, params: dict` | `{success, data: {task_id}}` | 验证输入+参数，入队任务 |
| `preview_auto_editor_command` | `params: dict` | `{success, data: {argv: [...], display: str}}` | 构建预览命令 |
| `cancel_auto_editor_task` | `task_id: str` | `{success}` | 终止进程，清理部分输出 |

#### auto_editor_runner.py 模块

| 函数 | 说明 |
|------|------|
| `validate_local_input(input_file)` | 拒绝 URL 输入，验证文件存在/扩展名 |
| `build_command(input_file, params, auto_editor_path, output_path)` | 构建 auto-editor CLI 命令，自动添加 `--progress machine` |
| `generate_output_path(input_file, output_dir, task_id, extension)` | 生成唯一输出路径，防止路径遍历 |
| `parse_auto_editor_segment(segment)` | 解析 `title~current~total~eta` 格式进度 |
| `read_auto_editor_output(proc)` | 逐字节读取 stdout，按 `\r` 分割并解析进度 |

#### task_runner.py 扩展

| 变更 | 说明 |
|------|------|
| `auto_editor` 任务类型 | 路由到 `\r`-based 进度解析器 |
| `NO_COLOR=1` 环境变量 | auto-editor 子进程禁用 ANSI 颜色 |
| 命令构建时机 | 执行时构建（非入队时） |

---

## 前端组件

### 页面组件

#### CommandConfigPage.vue

<!-- v2.1.0-CHANGE: Phase 3.5 重构页面布局 -->
<!-- v2.1.0-CHANGE: Phase 3.5.1 互斥，Phase 3.5.2 新增 Merge 选项卡 -->

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

#### AudioSubtitlePage.vue

<!-- v2.1.0-CHANGE: Phase 3.5 新增 -->

```
AudioSubtitlePage
  CommandPreview.vue     - 独立命令预览
  AvsmixForm.vue         - 音频/字幕各占半屏，全屏拖放 (Phase 3.5.1)
```

#### MergePage.vue

<!-- v2.1.0-CHANGE: Phase 3.5 新增, Phase 3.5.2 简化, Phase 3.5.2-fixes 隔离 -->

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

#### CustomCommandPage.vue

<!-- v2.1.0-CHANGE: Phase 3.5 新增, Phase 3.5.2-fixes 改进 -->

```
CustomCommandPage
  CommandPreview.vue     - 标准命令预览（通过 useCommandPreview + build_command_preview）
  Raw Args Textarea      - 原始 FFmpeg 参数输入
```

#### AutoCutPage.vue

<!-- v2.2.0-CHANGE: Phase 2 新增，Phase 7-11 重构 -->

```
AutoCutPage (v2.2.0 Phase 2+)
  StatusBar              - auto-editor 可用状态（initializing 期间隐藏防闪烁）
  FileDropInput          - 多文件输入（:multiple="true"），selectedFiles watcher 同步到 composable
  TabContainer           - [Basic] [Advanced] 选项卡
  BasicTab.vue           - 基础选项卡（含编码器选择）
  AdvancedTab.vue        - 高级选项卡（开关已整合）
  CommandPreview.vue     - 命令预览（type="auto-editor"，immediate 触发）
  "Add to Queue" Button - 多文件逐个添加，全成功后跳转队列
```

**状态栏**:
- `initializing=true` 时状态栏完全隐藏，防止短暂闪烁
- 未配置: "Set auto-editor path in Settings"
- 版本不兼容: "Version X not supported"
- 就绪: 隐藏

**行为**:
- `!isReady || selectedFiles.length === 0` 时按钮禁用
- 使用 `useAutoEditor` composable 管理所有状态
- 多文件支持：每个文件独立创建一个 auto-editor 任务
- `selectedFile` 通过 watcher 从 `selectedFiles` 数组同步到 composable（取第一个文件用于预览）
---

### 配置组件

#### CommandPreview.vue

<!-- v2.2.0-CHANGE: Phase 2 新增 type prop -->

**路径**: `frontend/src/components/config/CommandPreview.vue`

**Props**:

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `commandText` | `string` | `''` | 命令文本 |
| `errors` | `ValidationItem[]` | `[]` | 验证错误列表 |
| `warnings` | `ValidationItem[]` | `[]` | 验证警告列表 |
| `validating` | `boolean` | `false` | 是否正在验证 |
| `type` | `'ffmpeg' | 'auto-editor'` | `'ffmpeg'` | 命令类型（v2.2.0 Phase 2） |

**行为**:
- `type='ffmpeg'`: 显示 FFmpeg 特有语法高亮（默认行为不变）
- `type='auto-editor'`: 纯文本显示，禁用 FFmpeg 语法高亮
- 文件路径显示为纯文本（不使用 `v-html`，XSS 防护）
- 复制按钮复用现有逻辑（`navigator.clipboard` + fallback）

---

#### EncoderSelect.vue

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

---

#### TranscodeForm.vue

<!-- v2.1.0-CHANGE: Phase 3.5 扩展 -->
<!-- v2.1.0-CHANGE: Phase 3.5.1 重新排序 -->

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

#### FilterForm.vue

**关键行为**:
- 横竖屏转换与基础滤镜互斥（aspect_convert 启用时 crop/rotate/watermark 禁用）
- 滤镜互斥自动清理（选择 aspect_convert 时清空 rotate，选择 rotate 时清空 aspect_convert）
- 水印路径使用 FileDropInput 组件
- 全屏拖放支持（Phase 3.5.1）
- 音频归一化位置：speed 之前、watermark 之后（priority 16）

---

#### ClipForm.vue

<!-- v2.1.0-CHANGE: Phase 3.5.2 时间拆分 -->

**时间输入**: H:MM:SS.ms 四个独立数字输入框

| 规则 | 说明 |
|------|------|
| UI 拆分 | 时间输入从单一文本框改为 H:MM:SS.ms 四个独立数字输入框 |
| 格式 | config 存储为 "H:MM:SS.mmm" 字符串，与 FFmpeg 兼容 |
| 可选性 | StartTime 和 EndTime 均为可选（至少提供一个才生成剪辑命令） |
| 对齐布局 | StartTime 和 EndTime 在 ClipForm 中并排显示（md:grid-cols-2） |
| 占位符 | H(0-99), MM(0-59), SS(0-59), ms(0-999) |

---

#### MergeFileList.vue

<!-- v2.1.0-CHANGE: Phase 3.5.2-fixes -->

**路径**: `frontend/src/components/config/MergeFileList.vue`

| Prop | 类型 | 说明 |
|------|------|------|
| `modelValue` | `string[]` | 文件路径列表（v-model） |

**行为** (Phase 3.5.2-fixes):
- [添加文件] / [上移] / [下移] / [移除] 操作按钮
- 每行显示序号、文件名、移除按钮
- 支持拖拽排序（HTML5 drag-and-drop）
- 支持全屏拖拽上传（document 级 drag 事件监听，80ms 延迟后调用 `get_dropped_files`）
- 允许重复文件添加（不降重过滤）
- 至少需要 2 个文件

**v2.1.1 优化**:

| 优化项 | 变更内容 |
|--------|---------|
| dragover 节流 | 仅在 `dragend` 时 emit 最终位置，`dragover` 期间仅做视觉排序（不修改响应式数据） |
| key 修复 | `:key="index"` 改为唯一 ID（自增计数器），避免 Vue 重排追踪失败 |

---

### 任务队列组件

#### TaskList.vue

<!-- v2.1.0-CHANGE: Phase 5 队列表格布局重构 -->

- 移除"信息"列（Info），duration 和 file_size 合并显示到文件名列中
- 列宽: Checkbox `w-10 shrink-0` / File `min-w-0`（弹性） / State `w-20 shrink-0` / Progress `w-44 shrink-0` / Actions `w-52 shrink-0`
- 容器: `overflow-hidden`（禁止横向滚动）
- 文件名列: 内部 `min-w-0 flex-1` + `truncate` 截断长文件名

#### TaskRow.vue

- 文件列信息合并: 文件名 + duration + file_size 均在同一 `<td>` 中，使用 `opacity-50` 次要文本
- 操作列: `shrink-0 whitespace-nowrap`，固定宽度防止按钮跳位
- 所有操作按钮统一升级为 `btn-sm`
- 打开文件夹: `v-if="task.state === 'completed' && task.output_path"`
- v2.2.0 Phase 5: 任务类型标识，文件名前显示 `task_type` badge（`auto_editor` / `ffmpeg`）

#### TaskProgressBar.vue

- 进度条容器: `shrink-0 w-20`
- 所有数值指标: `shrink-0` + `tabular-nums`（等宽数字对齐）
#### BasicTab.vue

<!-- v2.2.0-CHANGE: Phase 3 新增，Phase 7-11 重构 -->

**路径**: `frontend/src/components/auto-cut/BasicTab.vue`

**Props**: 所有参数通过 props 传入（非共享 composable 状态），包括 videoCodec/audioCodec

**布局**: `grid grid-cols-1 md:grid-cols-2 gap-4` 两列网格

| 控件 | 类型 | 绑定 | 说明 |
|------|------|------|------|
| Edit method | select | `editMethod` | audio / motion |
| Threshold | range slider | `currentThreshold` (computed) | 0.01-0.20, step 0.01, 切换方法时自动切换默认值 |
| When-silent action | select | `whenSilentAction` | cut / speed / volume / nil |
| When-silent value | number input | `silentSpeedValue` 或 `silentVolumeValue` | 独立输入框，speed 默认4，volume 默认0.5，非 speed/volume 时冻结 |
| When-normal action | select | `whenNormalAction` | nil / cut / speed / volume |
| When-normal value | number input | `normalSpeedValue` 或 `normalVolumeValue` | 独立输入框，speed 默认4，volume 默认0.5，非 speed/volume 时冻结 |
| Margin | text input | `margin` | 如 "0.2s" |
| Smooth mincut | text input | (smooth 第一部分) | 如 "0.2s" |
| Smooth minclip | text input | (smooth 第二部分) | 如 "0.1s" |
| Video Codec | categorized select | `videoCodec` | 推荐/硬件加速/其他/自定义，optgroup 分组 |
| Audio Codec | categorized select | `audioCodec` | 推荐/其他/自定义，optgroup 分组 |

**动态行为**:
- 切换 `editMethod` 时 `audioThreshold`/`motionThreshold` 自动切换默认值
- silent 和 normal 各自拥有独立的 speed/volume 输入框，不共用
- 选择 action 为 `speed` 时显示 Speed 输入框（默认值4），选择 `volume` 时显示 Volume 输入框（默认值0.5）
- 选择 action 为 `cut`/`nil` 时输入框冻结（disabled），避免排版变动
- 编码器使用静态 curated 列表，分组显示（推荐/硬件加速/其他），支持自定义输入

---


#### AdvancedTab.vue

<!-- v2.2.0-CHANGE: Phase 4 新增，Phase 7-11 重构 -->

**路径**: `frontend/src/components/auto-cut/AdvancedTab.vue`

**Props**:

| Prop | 类型 | 说明 |
|------|------|------|
| `advancedOptions` | `AdvancedOptions` | 高级选项 reactive 对象 |

**Events**:

| 事件 | 参数 | 说明 |
|------|------|------|
| `update:advancedOptions` | `value: AdvancedOptions` | 高级选项变更 |

**布局**: Actions / Timeline / Switches / Video params / Audio params / Output

| 分区 | 控件 | 类型 | 说明 |
|------|------|------|------|
| Actions | Cut-out ranges | 动态列表 | add/remove，格式 "start,end" |
| Actions | Add-in ranges | 动态列表 | add/remove，格式 "start,end" |
| Actions | Set-action ranges | 动态列表 | add/remove，格式 "start,end,action" |
| Timeline | Frame rate | text input | 如 "30" |
| Timeline | Sample rate | text input | 如 "44100" |
| Timeline | Resolution | text input | 如 "1920x1080" |
| Switches | -vn/-an/-sn/-dn | toggle | 禁用视频/音频/字幕/数据流 |
| Switches | Faststart | toggle | 默认 ON（不发 flag），OFF 时发 `--no-faststart` |
| Switches | Fragmented | toggle | 默认 OFF，ON 时发 `--fragmented` |
| Switches | No-cache | toggle | 禁用缓存 |
| Switches | Open | toggle | 完成后自动打开（含队列警告提示） |
| Video params | Bitrate | text input | 如 "5M" |
| Video params | CRF | text input | 如 "23" |
| Audio params | Bitrate | text input | 如 "128k" |
| Audio params | Layout | text input | 如 "stereo" |
| Audio params | Normalize | select | none / peak / ebu |
| Output | Output extension | select | .mp4 / .mkv / .mov |

**动态行为**:
- 8 个 toggle 开关统一在 Switches 分区，使用 `grid grid-cols-2 md:grid-cols-4` 排列
- 编码器选择已移至 BasicTab，AdvancedTab 不再包含编码器下拉框
- 范围列表支持动态 add/remove

#### AutoEditorSetup.vue

<!-- v2.2.0-CHANGE: Phase 5 新增 -->

**路径**: `frontend/src/components/settings/AutoEditorSetup.vue`

**Props**:

| Prop | 类型 | 说明 |
|------|------|------|
| `status` | `AeStatus` | auto-editor 状态对象 `{available, compatible, version, path}` |

**Events**:

| 事件 | 参数 | 说明 |
|------|------|------|
| `select-binary` | 无 | 请求打开文件选择器选择 auto-editor 二进制路径 |
| `set-path` | `path: string` | 设置 auto-editor 路径（触发后端验证 + 保存） |

**布局**: 与 `FFmpegSetup.vue` 风格一致

- 标题: `t("settings.autoEditor.title")`
- 状态栏: 根据 `status` 显示可用性 badge
  - `available && compatible`: 绿色 badge + 版本号
  - `available && !compatible`: 黄色 badge + "Version X not supported"
  - `!available`: 灰色 badge + "Not configured"
- 操作按钮:
  - "Auto Detect" 按钮: 尝试从 PATH 查找 auto-editor（调用 `get_auto_editor_status`）
  - "Select Binary" 按钮: 打开文件选择器选择二进制路径（emit `select-binary`）
- 路径显示: 容器使用 `min-h-[2.5rem]` 预留空间，避免路径显示后排版变动

**行为**:
- 组件 mount 时自动 fetch 一次 status
- 路径变更后监听 `auto_editor_version_changed` 事件实时更新状态
- 版本不兼容时显示警告文案

### 布局与设置组件

#### AppNavbar.vue

<!-- v2.2.0-CHANGE: Phase 2 新增 AutoCut 导航项 + auto-editor 状态徽标 -->

- 导航栏: `border-b border-base-300`，品牌名 `text-base tracking-tight`，导航项 `gap-0.5`，右侧控件 `gap-1.5`
- FFmpeg 状态徽标: 实时更新版本号和状态（监听 `ffmpeg_version_changed` 事件）
- auto-editor 状态徽标（v2.2.0）: 实时更新版本号和状态（监听 `auto_editor_version_changed` 事件），位于 FFmpeg 状态徽标之后
- 导航项（v2.2.0 新增 AutoCut）: 位于 AudioSubtitle 和 Merge 之间，i18n key: `nav.autoCut`
- 主题切换: 太阳/月亮图标按钮，`toggleTheme()` 在 light/dark 间切换
- 语言切换: CN/EN 标签按钮（Phase 4）

#### FFmpegSetup.vue

- Download FFmpeg 按钮: 始终可见，点击弹出 DaisyUI modal 确认
- 非 Windows: 显示平台安装提示（静态文本）
- v2.1.1: 下载超时改为事件驱动（监听 `ffmpeg_version_changed`），i18n close 按钮

#### AutoEditorSetup.vue（v2.2.0 Phase 5）

- 位于 SettingsPage 右侧列，与 FFmpegSetup 并列
- 路径选择按钮: 调用 `select_file` 选择二进制路径，后端 `set_auto_editor_path` 验证并保存
- 状态显示: 监听 `auto_editor_version_changed` 事件实时更新
- 与 FFmpegSetup 风格一致（badge 状态指示 + 操作按钮）

---

## 数据模型字段定义

详见 `core/models.py` 章节，此处提供 fields/ 目录索引：

| 文件 | 说明 |
|------|------|
| `fields/Task.csv` | 任务基础字段 |
| `fields/TaskConfig.csv` | 任务配置字段 |
| `fields/TaskProgress.csv` | 任务进度字段 |
| `fields/QueueSummary.csv` | 队列摘要字段 |
| `fields/TranscodeConfig.csv` | 转码配置字段 |
| `fields/FilterConfig.csv` | 滤镜配置字段 |
| `fields/ClipConfig.csv` | 剪辑配置字段 |
| `fields/MergeConfig.csv` | 拼接配置字段 |
| `fields/AudioSubtitleConfig.csv` | 音频字幕配置字段 |
| `fields/Encoder.csv` | 编码器注册表字段 |
| `fields/Preset.csv` | 预设字段 |

---

## 路由扩展（Phase 3.5）

<!-- v2.1.0-CHANGE: Phase 3.5 新增路由 -->

| 路径 | 名称 | 组件 | 说明 |
|------|------|------|------|
| `/` | TaskQueue | `TaskQueuePage.vue` | 任务队列（不变） |
| `/config` | CommandConfig | `CommandConfigPage.vue` | 转码/滤镜/剪辑（仅 3 个选项卡 → 4 个选项卡） |
| `/audio-subtitle` | AudioSubtitle | `AudioSubtitlePage.vue` | 音频/字幕独立页面 |
| `/merge` | Merge | `MergePage.vue` | 拼接独立页面 |
| `/custom-command` | CustomCommand | `CustomCommandPage.vue` | 自定义命令页面 |
| `/auto-cut` | AutoCut | `AutoCutPage.vue` | 自动剪辑页面（v2.2.0 Phase 2） |
| `/settings` | Settings | `SettingsPage.vue` | 设置（不变） |

---

## 国际化架构（Phase 4）

<!-- v2.1.0-CHANGE: Phase 4 新增 -->

### i18n 框架

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

### 语言切换 UI:

- 位置: AppNavbar.vue 导航栏右侧，主题切换按钮旁
- 样式: `btn btn-ghost btn-sm btn-square`
- 行为: 显示当前语言代码（CN/EN），点击切换

---

## v2.1.1: 性能优化与质量改进

### configRef 模式感知确认

<!-- v2.1.1-CHANGE: 确认 configRef 模式感知正确实现 -->

**路径**: `frontend/src/composables/useGlobalConfig.ts`

**v2.1.0 现状**: `configRef` computed 已按 `activeMode` 过滤子配置（transcode + filters 始终包含，clip/merge/avsmix/custom 仅在对应 mode 时包含）。

**v2.1.1 确认**: 经审查 `configRef` 已正确实现模式感知过滤，无需修改。全局 intro/outro 通过独立的 watch 在 `merge` 子配置中设置，不影响模式感知逻辑。

---

### MergeFileList 优化

<!-- v2.1.1-CHANGE: MergeFileList 优化 -->

**路径**: `frontend/src/components/merge/MergeFileList.vue`

| 优化项 | 变更内容 |
|--------|---------|
| dragover 节流 | 仅在 `dragend` 时 emit 最终位置，`dragover` 期间仅做视觉排序（不修改响应式数据） |
| key 修复 | `:key="index"` 改为唯一 ID（自增计数器），避免 Vue 重排追踪失败 |

---

### Bridge 事件处理类型安全（v2.1.1）

<!-- v2.1.1-CHANGE: Bridge 事件处理类型安全 -->

**路径**: `frontend/src/composables/useTaskQueue.ts`, `frontend/src/composables/useTaskProgress.ts`

**v2.1.0 现状**: 事件处理函数对 `unknown` 数据使用 `as` 强制转换，无运行时校验。

**v2.1.1 变更**: 添加运行时类型守卫。

```typescript
// v2.1.0
on("task_state_changed", (detail: unknown) => {
  const { task_id, new_state } = detail as { task_id: string; ... }

// v2.1.1
on("task_state_changed", (detail: unknown) => {
  const payload = detail as Record<string, unknown>
  if (typeof payload.task_id !== "string") return
  if (typeof payload.new_state !== "string") return
```

**影响文件**:
- `useTaskQueue.ts`: `task_removed`, `task_state_changed`, `queue_changed`, `task_added` 事件处理
- `useTaskProgress.ts`: `task_progress` 事件处理

---

### bridge.ts 类型安全（v2.1.1）

<!-- v2.1.1-CHANGE: bridge.ts 类型安全 -->

**路径**: `frontend/src/bridge.ts`

| 变更项 | v2.1.0 | v2.1.1 |
|--------|--------|--------|
| `call` 返回类型 | `any` | `unknown` + 泛型类型参数 `call<T>` |
| usePresets.ts 类型 | `any` | 具体类型替代 |

---

### 前端组件变更（v2.1.1）

<!-- v2.1.1-CHANGE: 前端组件变更 -->

| 组件 | 变更说明 |
|------|---------|
| `CommandPreview.vue` | 接收 param 字段，复制反馈，prop 传递命令文本 |
| `TaskToolbar.vue` | 破坏性操作添加 DaisyUI modal 确认对话框 |
| `BatchControlBar.vue` | 破坏性操作添加 DaisyUI modal 确认对话框 |
| `ClipForm.vue` | catch 块添加用户错误反馈 |
| `TaskRow.vue` | catch 块添加用户错误反馈，图标按钮添加 aria-label |
| `MergeFileList.vue` | catch 块添加用户错误反馈，key 修复，dragover 节流，i18n title |
| `PresetSelector.vue` | catch 块添加用户反馈，替换原生 confirm() 为 DaisyUI modal，loading 状态使用 |
| `FFmpegSetup.vue` | 下载超时改为事件驱动（监听 `ffmpeg_version_changed`），i18n close 按钮 |
| `AppAbout.vue` | 模块级 `t()` 调用移入组件内部 |
| `EncoderSelect.vue` | 自定义输入框聚焦状态下不被条件渲染移除 |
| `TaskList.vue` | 空状态提示居中布局 |
| `TranscodeForm.vue` | 空 div 替代为 CSS 属性 |
| `ComboInput.vue` | 添加 Escape 键关闭下拉菜单 |
| `AppNavbar.vue` | FFmpeg badge 初始状态设为 `unknown`（灰色） |
| `router/index.ts` | 新增 404 catch-all 路由 |
| `TaskQueuePage.vue` | 清理 console.log |
| `useTaskQueue.ts` | 清理 console.log，事件类型守卫 |
| `useTheme.ts` | 修复 floating promise (save_settings) |
| `useLocale.ts` | 修复 floating promise (save_settings) |
| `FilterForm.vue` | 审查 props 直接修改 |
| `TranscodeForm.vue` | 审查 props 直接修改，批量字段赋值 |
| `MergePanel.vue` | 审查 props 直接修改，批量字段赋值 |
