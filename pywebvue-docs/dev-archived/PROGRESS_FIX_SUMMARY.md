# 修复总结 - 进度显示和按钮状态问题

## 已完成的修复

### 1. **状态同步修复** (关键!)
**问题**: App.vue 和 ProgressPanel.vue 各自调用 `useBatchProcess()`，创建了两个独立的 state 实例，导致状态不同步。

**修复**: 使用 provide/inject 共享同一份 state
- `App.vue`: `provide("batchProcess", batchProcess)`
- `ProgressPanel.vue`: `inject("batchProcess")`

### 2. **事件丢失防护**
**问题**: `task_start` 事件可能在 `useBatchProcess` 注册监听器之前就发送，导致 `processing` 不更新。

**修复**: `App.vue` 在 `start_batch` 成功后主动调用 `setProcessing(true)`，作为 fallback。

### 3. **初始进度显示**
**问题**: `overallTotal` 只在任务完成后才设置，进度面板一开始显示 "0/0"。

**修复**: `BatchRunner.start()` 开始时立即发送初始 `batch_progress` 事件。

### 4. **Cancel 后按钮状态不重置**
**问题**: `batch_complete` 事件可能因异常未发送。

**修复**: `_run_all()` 使用 `try/finally`，确保无论如何都会发送 `batch_complete`。

### 5. **FFmpeg 间歇性识别失败**
**修复**: 为 `ffmpeg_setup.py` 添加详细日志，帮助诊断路径查找问题。

### 6. **调试日志**
- 添加 `[BatchRunner]`、`[App]`、`[useBatchProcess]` 前缀的日志
- 可在控制台追踪事件流

## 测试步骤

### 1. 重启应用
```bash
dev.bat
```

### 2. 观察控制台
- 应看到 `[App] onMounted` 日志
- 应看到 `[App] GLOBAL` 事件日志（如果事件到达）

### 3. 添加文件并开始批处理

**预期行为**:
- ✅ "Start Batch" 按钮立即禁用
- ✅ "Cancel" 按钮立即启用
- ✅ 底部进度面板**立即出现**，显示 "Overall 0/N"
- ✅ 各个文件的行会陆续出现，显示 Running 状态和进度条
- ✅ 处理过程中，速度、FPS、百分比实时更新
- ✅ 完成后（或取消后），"Cancel" 禁用，"Start" 启用

### 4. 点击 Cancel
- 批处理应停止
- 按钮状态应恢复
- 进度面板应保持最后状态

### 5. 检查 FFmpeg 状态
- 打开 Settings
- FFmpeg 状态应正确显示（Ready/Not Found + 版本号）

## 如果问题仍然存在

查看控制台，确认是否看到：

```
[BatchRunner] === 🚀 BatchRunner.start() invoked...
[BatchRunner] Emitting initial batch_progress
[BatchRunner] [_run_task] Starting task...
[BatchRunner] Emitting task_progress...
[BatchRunner] Emitting batch_complete
```

如果没有看到这些，说明批次没有正常启动。

同时检查浏览器控制台是否看到：
```
[useBatchProcess] ✅ Component mounted
[App] GLOBAL task_start
[App] GLOBAL batch_progress
```

如果事件到达但进度面板没显示，检查 `processing` 值：
```javascript
// 在浏览器控制台运行
window.__VUE_DEVTOOLS_GLOBAL_HOOK__?.Vue?.getCurrentInstance()?.data?.processing
```
(或使用 Vue Devtools)

## 已知仍可能的日志

- `[useBatchProcess]` 日志可能在热重载时出现多次（开发模式正常）
- FFmpeg 路径查找可能在重启后偶尔失败（可能是 static_ffmpeg 缓存问题）

---

**核心改进**: 状态现在通过 provide/inject 共享，`App.vue` 和 `ProgressPanel.vue` 使用同一份 state，按钮和进度应该完全同步。
