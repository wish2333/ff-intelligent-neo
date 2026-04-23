# 测试清单 - 进度显示和按钮状态修复

## 修复内容

1. **添加调试日志**：前后端都添加了详细日志，可追踪事件流
2. **修复 SettingsModal 无限加载**：`get_app_info` 失败时设置默认值，避免一直显示 Loading
3. **确保 FFmpeg 未找到时发送 batch_complete**：防止 processing 状态卡住
4. **改进 reset 逻辑**：开始新批次前自动重置，且 reset 现在也会重置 processing 状态
5. **App.vue 中改进错误处理**：更好地处理 start_batch 错误

## 测试步骤

### 准备工作

1. 重新构建前端（如果需要）：
   ```bash
   cd frontend
   npm run build
   ```

2. 运行应用：
   ```bash
   uv run main.py
   ```

### 测试 1: 检查前端控制台日志

打开开发者工具（如果 PyWebView 支持）或查看后端控制台输出。

**预期行为：**

- 应用启动时，应看到 `[useBatchProcess] Component mounted, registering event listeners`
- 点击 Settings 按钮，应看到设置界面显示内容（不再一直显示 "Loading..."）
- 如果 FFmpeg 未找到，Settings 中会显示 "Not Found"，但界面应能正常打开

### 测试 2: 测试按钮状态

1. 添加一些视频文件到文件列表
2. 选择一个输出目录（或使用默认）
3. 选择一个预设
4. **点击 "Start Batch"**

**预期行为：**
- 点击后，Start 按钮应立即**禁用**（变灰）
- Cancel 按钮应立即**启用**
- 如果在控制台查看，应看到 `[App] handleStartBatch called` 和 `[App] start_batch succeeded`

**完成后（或出错后）：**
- Cancel 按钮应重新**禁用**
- Start 按钮应重新**启用**

### 测试 3: 测试进度显示

1. 确保 FFmpeg 可用（在 Settings 中查看 FFmpeg 状态）
2. 添加至少一个视频文件
3. 点击 "Start Batch"

**预期行为：**
- 窗口底部会出现一个 **Progress Panel**（ Overall 进度条 + 每个文件的任务）
- 应看到 `[useBatchProcess] batch_progress received` 日志
- 应看到 `[useBatchProcess] task_start received` 和 `[useBatchProcess] task_progress received`
- Overall 进度条会随着进度增加
- 每个文件会显示运行状态（"Running" 徽章）、进度条、百分比、速度等信息

### 测试 4: 测试 FFmpeg 未找到的情况

如果 FFmpeg 未正确安装或路径问题触发：

**预期行为：**
- 点击 Start 后，在控制台看到 `[useBatchProcess] task_error received` 和 `batch_complete`
- Settings 面板中 FFmpeg 状态显示 "Not Found"
- Start 按钮禁用状态会解除（允许重试）
- 可能在 Progress Panel 中看到错误信息

### 测试 5: 取消批处理

1. 开始一个批处理（有足够长的任务）
2. 点击 "Cancel"

**预期行为：**
- 正在运行的任务会尝试取消
- 所有任务完成后，Cancel 按钮禁用，Start 按钮启用
- 进度面板会保持显示最后的状态

## 调试信息

如果问题仍然存在，请收集以下信息：

1. **前端控制台输出**（如果可用）
2. **后端控制台输出**，特别是包含以下标签的日志：
   - `[useBatchProcess]`
   - `[BatchRunner]`
   - `[App]`
3. **事件流**：检查是否看到所有事件：
   - `task_start`
   - `batch_progress`
   - `task_progress`（多个）
   - `task_complete` 或 `task_error`
   - `batch_complete`

## 常见问题

### Q: 看不到任何 `[useBatchProcess]` 日志
A: 事件监听器可能没有正确注册，或者事件系统有问题。请检查控制台是否有 JavaScript 错误。

### Q: 看到 `task_start` 但没有看到 `task_progress`
A: 可能 FFmpeg 没有输出进度信息，或者 `on_progress` 回调没有被调用。检查 FFmpeg 日志（展开 "FFmpeg Log" 详情）。

### Q: 按钮状态不更新
A: 检查 `[useBatchProcess] batch_complete received` 是否出现。如果没有，说明批次没有正常结束（可能线程崩溃）。

### Q: Settings 一直显示 "Loading..."
A: 应已修复。如果仍然出现，检查 `get_app_info` 是否抛出异常。查看后端日志。

## 已知限制

- 如果 FFmpeg 路径检测失败，建议在 Settings 中查看详细信息或重新安装依赖
- 事件系统依赖 PyWebVue，如果版本不兼容可能需要更新
