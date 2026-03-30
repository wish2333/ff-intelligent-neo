# 最终修复报告

## 问题汇总

1. **Cancel 按钮点后无效** - 子进程没杀掉，视频继续转码
2. **进度显示异常** - 不显示或更新不及时
3. **按钮状态错误** - Cancel 后按钮未恢复
4. **FFmpeg 间歇性识别失败**
5. **FFmpeg 日志刷屏控制台**

---

## 已完成的修复

### ✅ 1. Cancel 进程立即终止

**文件**: `core/ffmpeg_runner.py`

**问题**: 原来的 `proc.wait()` 会阻塞，即使 `cancel_event` 设置也不会检查，导致 Cancel 按钮点了没反应。

**修复**: 改为循环检查机制：
- 每 0.1 秒检查一次 `cancel_event`
- 如果被设置，立即 `proc.kill()` 并返回
- 同时检查进程是否自然结束（`proc.poll()`）

现在 Cancel 应该立即生效，FFmpeg 进程会被终止。

---

### ✅ 2. 状态同步 - 进度显示的根本修复

**文件**: `frontend/src/App.vue`, `frontend/src/components/ProgressPanel.vue`

**问题**: App.vue 和 ProgressPanel.vue 各自创建 `useBatchProcess()` 实例，导致状态不同步。ProgressPanel 监听到的事件更新的是自己的实例，而非 App 中用于按钮状态的实例。

**修复**:
- App.vue: `const batchProcess = useBatchProcess(); provide("batchProcess", batchProcess);`
- ProgressPanel.vue: `const batchProcess = inject(...)` 使用同一个实例
- 移除 ProgressPanel 中重复的事件监听器

**效果**: 所有状态（`processing`、`overallTotal`、`taskProgressMap` 等）现在完全同步，按钮和进度面板显示一致。

---

### ✅ 3. 防止事件丢失 - `task_start` 防护

**文件**: `frontend/src/composables/useBatchProcess.ts`、`frontend/src/App.vue`

**问题**: `task_start` 事件可能在 `useBatchProcess` 注册监听器之前就发出，导致 `processing` 没有设为 true，Start 按钮不冻结。

**修复**:
- `useBatchProcess` 添加 `setProcessing(value: boolean)` 方法
- `App.vue` 在 `start_batch` 成功后调用 `setProcessing(true)` 作为 fallback

即使事件丢失，按钮状态也能正确更新。

---

### ✅ 4. 初始进度立即显示

**文件**: `core/batch_runner.py`

**问题**: `overallTotal` 只在任务完成后才设置，进度面板一开始显示 "0/0"。

**修复**: `BatchRunner.start()` 开始时立即发送初始 `batch_progress` 事件：
```python
self._emit("batch_progress", {
    "total": self._total,
    "completed": 0,
    "overall_percent": 0,
})
```

进度面板现在会立即显示 "Overall 0/N"。

---

### ✅ 5. 确保 `batch_complete` 总能发送

**文件**: `core/batch_runner.py`

**问题**: 如果线程异常崩溃，`batch_complete` 可能不发送，导致按钮状态卡住。

**修复**: `_run_all()` 使用 `try/finally`，无论如何都会发送 `batch_complete`。

---

### ✅ 6. 事件发送诊断

**文件**: `pywebvue/bridge.py`

**问题**: `Bridge._emit()` 在 `_window` 为 None 时静默丢弃事件，无法追踪。

**修复**: 添加警告日志到 stderr，如果 `_window` 为 None 或 `evaluate_js` 抛出异常，会打印错误信息。

这能帮助诊断事件丢失的具体原因。

---

### ✅ 7. 减少控制台刷屏

**文件**: `core/ffmpeg_runner.py`

**问题**: FFmpeg 的 stderr 每行都经过 `on_log`，如果这里再记录到 loguru 会刷屏。

**现状**: `on_log` 只发送事件给前端，不再调用 `logger`。**FFmpeg 的原始输出只在前端显示（可折叠面板），后端控制台不再出现。**

---

### ✅ 8. 前端日志简化

**文件**: `frontend/src/composables/useBatchProcess.ts`

**注意**: 保留了事件接收的调试日志（`[useBatchProcess] task_start received` 等），便于追踪事件流。生产环境可以移除。

---

## 测试步骤

### 1. 重启应用
```bash
dev.bat
```

### 2. 验证启动
- 后端控制台应看到 `[DEBUG] Creating FFmpegApi instance`
- 浏览器控制台应看到 `[App.vue] ✅ Script setup BEGINNING`
- `[App] onMounted` 及相关日志

### 3. 测试 Cancel 功能
1. 添加一个大视频文件（>100MB）
2. 点击 "Start Batch"
3. 立即点击 "Cancel"
4. **预期**:
   - ✅ FFmpeg 进程很快终止（任务状态变为 error，显示 "Cancelled"）
   - ✅ 视频文件大小不会增长（确认进程真的停止了）
   - ✅ 按钮状态恢复：Start 启用，Cancel 禁用

### 4. 测试进度显示
1. 添加 2-3 个视频
2. 点击 Start
3. **预期**:
   - ✅ 进度面板立即出现，显示 "Overall 0/3"
   - ✅ 每个文件的行出现 Running 状态和进度条
   - ✅ 百分比、速度、FPS 实时更新
   - ✅ Overall 进度条同步增长
4. 完成后:
   - ✅ 文件状态变为 "Done"（绿色徽章）
   - ✅ 按钮状态恢复

### 5. 测试按钮状态同步
1. 开始批处理 → Start 禁用，Cancel 启用
2. 等待完成或点击 Cancel → Start 启用，Cancel 禁用
3. **不应该出现**：Start 一直禁用或 Cancel 一直启用的情况

### 6. 测试 FFmpeg 状态
- 打开 Settings，查看 FFmpeg 版本是否正常显示
- 如果看到 "Not Found"，检查后端日志中的 `[ffmpeg_setup]` 信息

---

## 如果仍有问题

### 现象: 进度面板不显示

1. 检查 `processing` 是否为 true：
```javascript
// 在浏览器控制台
window.__VUE_DEVTOOLS_GLOBAL_HOOK__?.Vue?.getCurrentInstance()?.data?.processing
```
或使用 Vue Devtools 检查组件 state。

2. 检查 `overallTotal` 是否大于 0。

3. 检查是否收到 `batch_progress` 事件：
   - 浏览器控制台应看到 `[App] GLOBAL batch_progress`
   - 如果没有，检查后端是否发送了此事件（查看 bat 控制台的 `[BatchRunner]` 日志）

### 现象: 收到事件但进度不更新

检查 `taskProgressMap` 是否正确。在 Vue Devtools 中查看 `batchProcess.taskProgressMap`。

### 现象: Cancel 无效

检查 bat 控制台是否看到：
```
[ffmpeg_runner] FFmpeg process cancelled/cancelled/killed
```

如果没有，说明 `cancel_event` 没有传递到 `run_single`，或者 `run_single` 没有检查到。

### 现象: `_emit` 警告

如果看到 `[BRIDGE WARNING] _emit('...') failed: _window is None`，说明事件在窗口未准备好时就发送了。报告这个情况。

---

## 已知改进空间

1. **事件可靠性**: 当前依赖 `document.dispatchEvent`，如果前端代码出错，事件可能丢失。可以添加重试机制或状态持久化。
2. **进度初始值**: `overallTotal` 在 `start` 时才发送，如果用户快速点击 Start，可能在 `overallTotal` 更新前就开始等待。可以考虑在 `App.vue` 手动设置 `overallTotal = files.length`（从前端文件列表获取）。
3. **日志级别**: 生产环境应降低 `batch_runner` 的日志级别。

---

**现在请按照测试步骤操作，并告诉我结果。如果有任何异常，提供完整的控制台输出（bat + 浏览器）。**
