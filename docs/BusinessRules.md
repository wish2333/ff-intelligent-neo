# 业务规则

## 1. 任务状态转移规则

### 合法状态转移矩阵

| 当前状态 | 可转移目标 | 触发方式 |
|---------|-----------|---------|
| pending | running | 用户点击 Start |
| pending | cancelled | 用户点击 Stop |
| running | paused | 用户点击 Pause |
| running | completed | FFmpeg 正常完成 (exit code 0) |
| running | failed | FFmpeg 执行错误 (exit code != 0) |
| running | cancelled | 用户点击 Stop |
| paused | running | 用户点击 Resume |
| paused | cancelled | 用户点击 Stop |
| failed | pending | 用户点击 Retry |
| completed | - | 终态,不可变更 |
| cancelled | - | 终态,不可变更 |

### 状态转移约束

- 终态（completed, cancelled）不可发生任何状态转移
- running -> paused 使用操作系统级进程暂停
- failed -> pending 是唯一可以"回退"到非终态的转移
- 所有状态转移必须通过 `TaskQueue.transition_task()` 执行

## 2. 任务控制权限规则

### 按当前状态允许的操作

| 操作 | pending | running | paused | completed | failed | cancelled |
|------|:-------:|:-------:|:------:|:---------:|:------:|:---------:|
| Start | Y | - | - | - | - | - |
| Pause | - | Y | - | - | - | - |
| Resume | - | - | Y | - | - | - |
| Stop | Y | Y | Y | - | - | - |
| Retry | - | - | - | - | Y | - |

### 批量操作规则

- **Stop All**: 停止所有非终态任务（pending + running + paused）
- **Pause All**: 暂停所有 running 状态的任务
- **Resume All**: 恢复所有 paused 状态的任务
- **Clear Completed**: 删除所有 completed 状态的任务
- **Clear All**: 删除所有任务

## 3. 滤镜链优先级排序规则

滤镜在构建 FFmpeg 命令时按固定优先级自动排序：

| 优先级 | 滤镜 | 说明 |
|-------|------|-----|
| 5 | crop | 裁剪（先裁剪再缩放，避免不必要的缩放计算） |
| 10 | denoise | 降噪（在缩放前处理） |
| 20 | scale | 缩放/分辨率调整 |
| 30 | rotate | 旋转 |
| 40 | speed | 速度调整 |
| 50 | overlay | 水印叠加（最后处理，覆盖在最终画面上） |

排序规则：
- 滤镜按优先级数值从小到大排序
- 只有非空值的滤镜才加入滤镜链
- 空滤镜链时不添加 `-vf` 或 `-filter_complex` 参数
- overlay 滤镜使用 `-filter_complex` 语法（需要双输入流），其他滤镜使用 `-vf` 语法

## 4. 配置验证规则

### 警告 (Warning)

| 条件 | 警告信息 |
|------|---------|
| video_codec=copy 但设置了滤镜 | "视频编码为 copy 时滤镜不生效，需要重新编码" |
| speed > 4.0 | "速度大于 4.0 可能导致音视频不同步" |
| speed < 0.25 | "速度小于 0.25 可能导致音视频不同步" |

### 错误 (Error)

| 条件 | 错误信息 |
|------|---------|
| resolution 格式不是 WxH | "分辨率格式无效，请使用 WxH 格式（如 1920x1080）" |
| crop 参数不合法 | "裁剪参数格式无效，请使用 W:H:X:Y 格式" |
| watermark_path 文件不存在 | "水印文件不存在" |
| watermark_path 不是图片文件 | "水印文件必须是图片格式" |

### 命令构建规则

- video_codec=copy 时不添加视频比特率参数
- video_codec=none 时不添加视频相关参数（`-vn`）
- audio_codec=copy 时不添加音频比特率参数
- audio_codec=none 时不添加音频相关参数（`-an`）
- resolution 为空时不添加 scale 滤镜
- output_extension 决定输出文件格式和容器

## 5. 队列持久化规则

### 保存规则

- 使用防抖机制（0.5 秒延迟），避免频繁 IO
- 保存触发时机：任务增删、状态变更、配置修改
- 存储位置：`%APPDATA%/ff-intelligent-neo/queue_state.json`
- 保存内容：所有非终态任务 + 最近 50 条终态任务

### 保留规则

| 任务状态 | 保存时处理 |
|---------|-----------|
| pending | 保留 |
| running | 保留（恢复时标记为 failed） |
| paused | 保留（恢复时标记为 failed） |
| completed | 保留最近 50 条（按 completed_at 排序） |
| failed | 保留最近 50 条（按 completed_at 排序） |
| cancelled | 保留最近 50 条（按 completed_at 排序） |

### 日志行限制

- 每个任务最多保留 100 条日志行（`log_lines` 上限）
- FFmpeg 运行时保留 500 条，保存时截断到 100 条

## 6. 队列恢复规则

应用启动时从 JSON 恢复队列状态：

1. **running -> failed**: 进程已不存在，标记为失败（用户可 Retry）
2. **paused -> failed**: 进程已不存在，标记为失败（用户可 Retry）
3. **pending -> pending**: 保持不变
4. **终态任务**: 保留用于历史记录，超过 50 条时裁剪

裁剪逻辑：
- 按 `completed_at` 降序排列终态任务
- 保留最近的 50 条
- 删除超出部分

## 7. 并发规则

### 线程池管理

- 使用 `concurrent.futures.ThreadPoolExecutor`
- 最大工作线程数由 `AppSettings.max_workers` 决定（默认 2）
- 可设置范围：1-8（建议不超过 CPU 核心数）
- 任务提交后由线程池调度，无需用户手动分配

### 线程安全

| 模块 | 同步机制 | 说明 |
|------|---------|-----|
| TaskQueue | `threading.RLock()` | 所有队列操作加锁 |
| TaskRunner._cancel_events | `threading.Lock()` | 取消事件字典操作加锁 |
| TaskRunner._running_procs | `threading.Lock()` | 进程跟踪字典操作加锁 |
| FFmpeg stderr 读取 | 独立线程 | subprocess stderr 通过单独线程读取 |

### 取消机制

- 每个任务有独立的 `threading.Event` 作为取消信号
- `stop_task()` 设置 cancel_event 并调用 `kill_process_tree()`
- FFmpeg 运行循环中检查 cancel_event（每 0.5 秒）
- cancel_event 触发后立即终止进程，不等待当前帧完成

## 8. 进程控制规则

### 跨平台行为

| 操作 | Windows | Linux/macOS |
|------|---------|-------------|
| 暂停进程 | `ctypes: NtSuspendProcess` | `os.kill(pid, SIGSTOP)` |
| 恢复进程 | `ctypes: NtResumeProcess` | `os.kill(pid, SIGCONT)` |
| 终止进程树 | `taskkill /F /T /PID` | `os.killpg(pgid, SIGKILL)` |

### 进程创建

- Windows: 使用 `CREATE_NEW_PROCESS_GROUP` 标志创建子进程
- 目的：允许通过进程组终止整个进程树

### 强制终止规则

- `kill_process_tree()` 终止目标进程及其所有子进程
- 应用关闭时调用 `force_kill_all()` 强制终止所有运行中的 FFmpeg 进程
- `force_kill_all()` 不执行状态转移，直接终止进程（关闭场景无需精细控制）
- `_cleanup()` 方法有防重入保护（`_cleanup_guard`），避免多次调用

## 9. Bridge API 响应格式

所有 `@expose` 方法统一返回格式：

```python
# 成功
{"success": True, "data": <payload>}

# 失败
{"success": False, "error": "<error message>"}

# 带元信息
{"success": True, "data": <payload>, "meta": {"total": 10, "offset": 0}}
```

## 10. 事件发射规则

| 事件 | 发射时机 | 数据载荷 |
|------|---------|---------|
| `task_added` | 任务添加到队列 | `Task.to_dict()` |
| `task_state_changed` | 任务状态变更 | `{task_id, old_state, new_state}` |
| `task_progress` | 任务进度更新（0.5s 间隔） | `{task_id, progress: TaskProgress.to_dict()}` |
| `task_log` | FFmpeg 输出日志行 | `{task_id, line}` |
| `queue_changed` | 队列内容变更 | `QueueSummary` |

事件系统：
- 后端通过 `_emit()` 发射事件
- pywebview 通过 50ms tick 定时器将事件推送到前端
- 前端通过 `useBridge` composable 订阅事件
- 事件在主线程处理，确保 UI 线程安全
