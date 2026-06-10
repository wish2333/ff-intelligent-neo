# 更新记录 v2.2.6

- 日期: 2026-06-10
- 分支: dev-2.2.6
- 类型: 修复 (fix) + 新功能 (feat)

---

## 变更概述

修复任务队列页两个 UX 问题：(1) 页面加载和添加任务后用户看不到最新任务，(2) 任务列表超出可视区域时垂直滚动条不显示。

采用产品决策：保持 FIFO 存储和展示顺序（旧->新从上到下），通过自动滚动到底部让用户优先看到最新任务。

### v2.2.6-2 优化已完成任务进度栏显示

已完成任务的"进度"栏冗余信息（满格进度条、100%、已完成时长/视频时长）替换为输出文件大小和压缩率，保留速率和 FPS 信息。同时修复速率显示双 `x` bug。

---

## 变更详情

### 1. 新增自动滚动到底部 (feat)

**文件**: `frontend/src/components/task-queue/TaskList.vue`, `frontend/src/pages/TaskQueuePage.vue`

- `TaskList` 新增 `scrollContainer` 模板 ref 和 `scrollToBottom()` 方法，通过 `defineExpose` 暴露给父组件
- `TaskQueuePage` 在以下 3 个时机调用 `scrollToBottom()`:
  - `onMounted` -- 页面初始加载后自动滚到底部，优先展示最新任务
  - `handleAddFiles` -- 通过文件选择器添加任务后滚动
  - `handleDrop` -- 拖放文件添加任务后滚动
- 用户手动向上滚动浏览旧任务时，不会被强制回滚（仅在主动添加/加载时触发）

### 2. 修复垂直滚动条不显示 (fix)

**文件**: `frontend/src/components/task-queue/TaskList.vue`

- 根因：`flex-1` + `overflow-hidden` 组合导致内容超出时被裁剪，无滚动条
- 修复：`overflow-hidden` 改为 `overflow-y-auto`，使 TaskList 成为唯一的滚动上下文

### 3. 新增表头固定 (feat)

**文件**: `frontend/src/components/task-queue/TaskList.vue`

- `<thead>` 添加 `sticky top-0 z-10 bg-base-200 shadow-sm` 样式
- 滚动任务列表时表头保持固定在顶部，列标签始终可见
- `bg-base-200` 不透明背景遮挡滚动到下方的行内容

### 4. 防止双重滚动条 (fix)

**文件**: `frontend/src/pages/TaskQueuePage.vue`

- 移除页面容器的 `overflow-y-auto`，避免 TaskList 内部和页面外部同时出现滚动条
- 工具栏、汇总信息始终固定可见，仅任务列表区域可滚动

### 5. 修复速率双 x 显示 (bug fix)

**文件**: `core/ffmpeg_runner.py`

- 根因：正则 `_SPEED_RE = r"speed=\s*(\S+)"` 捕获了 `"6.03x"`（含 `x` 后缀），前端模板又追加一个 `x`，导致显示 `6.03xx`
- 修复：正则改为 `r"speed=\s*([\d.]+)"`，只捕获数字部分，前端保持 `{{ speed }}x` 显示

### 6. 记录输出文件大小 (feat)

**文件**: `core/models.py`, `core/task_runner.py`

- `Task` 模型新增 `output_file_size_bytes: int` 字段，更新 `to_dict()` / `from_dict()` 序列化
- FFmpeg 和 auto-editor 任务完成时，使用 `os.path.getsize()` 捕获输出文件大小
- 重试/重置任务时清零该字段

### 7. 已完成任务进度栏优化 (feat)

**文件**: `frontend/src/types/task.ts`, `frontend/src/components/task-queue/TaskProgressBar.vue`, `frontend/src/components/task-queue/TaskRow.vue`

- `TaskDTO` 新增 `output_file_size_bytes` 类型定义
- `TaskProgressBar.vue` 重写：根据任务状态条件渲染
  - **运行中/暂停**：保持原进度条 + 百分比 + 时长 + ETA + 速率 + FPS
  - **已完成**：显示 `125.3MB (-42.1%)  6.03x  30.0fps`（文件大小 + 压缩率 + 速率 + FPS）
  - 压缩率彩色标注：绿色（text-success）= 输出小于输入，黄色（text-warning）= 输出大于输入
- 新增 `effectiveProgress` 计算属性，优先使用实时进度事件数据，降级到 `task.progress`（TaskDTO 自带进度），解决刷新页面后已完成任务 speed/fps 不显示的问题

---

## 变更文件清单

| 文件 | 变更类型 |
|------|----------|
| `frontend/src/components/task-queue/TaskList.vue` | 新增 ref + scrollToBottom + overflow 修复 + sticky 表头 |
| `frontend/src/pages/TaskQueuePage.vue` | 新增 taskListRef + 3 处滚动调用 + 移除页面 overflow |
| `core/ffmpeg_runner.py` | 修复速率双 x bug：speed 正则只捕获数字 |
| `core/models.py` | 新增 `output_file_size_bytes` 字段 + 序列化 |
| `core/task_runner.py` | 任务完成时捕获输出文件大小 + retry/reset 清零 |
| `frontend/src/types/task.ts` | 新增 `output_file_size_bytes` 类型定义 |
| `frontend/src/components/task-queue/TaskProgressBar.vue` | 重写：已完成任务显示文件大小/压缩率/速率/FPS |
| `frontend/src/components/task-queue/TaskRow.vue` | 传递 `taskProgress` 等新 props |

---

## Commit Message

```
fix: 修复任务队列页滚动条缺失，新增自动滚动到底部，优化已完成任务进度栏，修复速率双 x bug

- overflow-hidden 改为 overflow-y-auto 修复垂直滚动条不显示
- 新增 scrollToBottom 方法，页面加载/添加任务后自动滚到底部
- thead 添加 sticky 样式，滚动时表头固定可见
- 移除页面容器 overflow-y-auto 防止双重滚动条
- 修复 speed 正则只捕获数字部分，解决 "6.03xx" 双 x 问题
- Task 模型新增 output_file_size_bytes，任务完成时捕获输出文件大小
- 已完成任务进度栏改为显示：文件大小 (-42.1%) 6.03x 30.0fps
- 运行中任务进度栏保持不变
- effectiveProgress 降级策略解决刷新后 speed/fps 不显示
```

---

## Release Notes

### 修复

- **滚动条缺失**: 任务数量超出可视区域时，垂直滚动条现在正常出现
- **最新任务不可见**: 页面加载和添加任务后，列表自动滚动到底部展示最新任务
- **速率显示双 x**: 修复 FFmpeg 速率解析正则，`6.03xx` 改为 `6.03x`

### 改进

- **固定表头**: 滚动浏览任务列表时，列标签（文件名/状态/进度/操作）保持固定在顶部
- **已完成任务进度栏**: 满格进度条、100%、已完成时长替换为输出文件大小和压缩率（如 `125.3MB (-42.1%)`），保留速率和 FPS 信息。压缩率彩色标注（绿色=压缩成功，黄色=文件变大）
