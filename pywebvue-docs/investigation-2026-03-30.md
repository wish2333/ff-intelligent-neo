# Investigation: fix-progress-and-cancel 未完成的三个问题

> 日期: 2026-03-30
> 背景: 归档变更 `2026-03-30-fix-progress-and-cancel` 声称修复了进度显示和取消功能，但实测发现三个问题未完成

---

## 问题 2（核心根因）：Start/Cancel 按钮状态卡死

### 现象

- 无论是等待转码完成还是中途点击取消，Start 按钮始终保持 disabled，Cancel 按钮始终保持 enabled
- 用户无法开启后续任务，只能重启应用

### 根因：DOM 事件冒泡机制

**`bridge.py:_emit()` 在 `document` 上派发 `CustomEvent`，但 `CustomEvent` 默认 `bubbles: false`。而 `bridge.ts:onEvent()` 在 `window` 上监听，未指定 `{capture: true}`。事件永远不会到达前端。**

#### 事件发射端（Python → JS）

`pywebvue/bridge.py:51`:
```python
js = f"document.dispatchEvent(new CustomEvent('pywebvue:{event}', {{detail: {payload}}}))",
```

在 **`document`** 上派发 `CustomEvent`，`bubbles` 默认为 **`false`**。

#### 事件接收端（前端）

`frontend/src/bridge.ts:33`:
```typescript
window.addEventListener(event, listener);
//                      ^^^^^^ 没有 {capture: true}
```

在 **`window`** 上监听，**没有指定 `capture`**。

#### DOM 事件传播路径

```
dispatch on document, bubbles: false

  Capture Phase ────────────────────────────
    window  (capture: true 的 listener 触发)
    ↓
    document (target: listener 触发)

  Target Phase ─────────────────────────────
    document

  Bubble Phase ─────────────────────────────
    (不存在！因为 bubbles: false)
    window (bubble listener 永远不会触发)
           ↑ onEvent 的 listener 在这里，永远收不到
```

#### 完整因果链

```
handleStartBatch()
  └─ setProcessing(true)           ← 手动设置，立即生效
  └─ call("start_batch")           ← 启动后台线程
       └─ _run_all (后台线程)
            └─ _emit("task_start")       ← dispatched on document, bubbles: false
            └─ _emit("task_progress")    ← 同上
            └─ _emit("task_complete")    ← 同上
            └─ finally:
                 └─ _emit("batch_complete")  ← 同上，永远到不了 window

结果：
  processing = true（由 handleStartBatch 设置）
  batch_complete → window listener → 永远不触发
  processing 永远 = true
  Start 按钮 :disabled="!hasFiles || processing" → disabled
  Cancel 按钮 :disabled="!processing" → enabled
```

#### 排除的假设

| 假设 | 排除原因 |
|------|---------|
| `evaluate_js` 后台线程不安全 | pywebview 6 macOS 实现通过 `AppHelper.callAfter` + `Semaphore` 将 JS 求值调度到主线程并阻塞等待，线程安全 |
| `finally` 块未执行 | `_run_all` 的 `try/finally` 包裹完整逻辑，无逃逸路径 |
| Vue 响应式失效 | `processing` 是 `ref<boolean>`，`.value` 赋值触发响应式更新 |

#### 修复方案

`pywebvue/bridge.py` — 给 `CustomEvent` 加 `bubbles: true`：

```python
# 修复前
js = f"document.dispatchEvent(new CustomEvent('pywebvue:{event}', {{detail: {payload}}}))"

# 修复后
js = f"document.dispatchEvent(new CustomEvent('pywebvue:{event}', {{detail: {payload}, bubbles: true}}))"
```

一行改动，所有事件即可冒泡到 `window`，前端全部 listener 都能收到。

---

## 问题 3：进度显示不符合要求

### 现象

1. 前端出现一个不符合要求的进度条（实际是 `0/0` 的静态条，因为 `processing = true` 但 `overallTotal = 0`）
2. 用户想要的进度显示是 "速度" + "进行时间/完成时间"，而不是百分比进度条
3. 需要支持多进程并行（两个 worker 同时显示各自的进度）
4. status 状态在前端没有任何显示和变化

### 根因分析

问题 3 的根因与问题 2 相同——**所有事件都无法到达前端**：

| 缺失的前端行为 | 对应的后端事件 | 为什么收不到 |
|--------------|--------------|------------|
| per-task 进度不显示 | `task_progress` | `bubbles: false` |
| 任务状态不变化 | `task_start` / `task_complete` / `task_error` | `bubbles: false` |
| 总进度永远 0/0 | `batch_progress`（后台线程发的） | `bubbles: false` |
| 取消后不重置 | `batch_cancelled` | `bubbles: false` |

**修复 DOM 事件冒泡后**，后端代码和前端代码的现有逻辑应该能工作：
- `task_progress` 事件携带 `current_seconds`、`total_duration_seconds`、`speed`、`fps`
- `ProgressPanel.vue` 已有 `formatTime()` 和 `formatProgressInfo()` 渲染逻辑
- 多进程支持已内置（`taskProgressMap` 按 `file_index` 存储每个任务的独立进度）

### 修复 DOM 冒泡后仍需额外处理的部分

#### 3a. 取消后前端任务状态未更新

`batch_runner.py:212-219` — 任务取消时只更新了内部 `_progress_map`，**没有发射事件通知前端**：

```python
elif self._cancel_event.is_set():
    logger.info("[_run_task] Task {} cancelled", index)
    self._progress_map[index] = TaskProgress(
        file_index=index, file_name=file_item.name,
        status="cancelled",
        percent=self._progress_map[index].percent if index in self._progress_map else 0,
    )
    # ← 缺少 self._emit("task_progress", {...}) 通知前端
```

`useBatchProcess.ts:115-121` — `batch_cancelled` 处理器只设了 `processing = false`，没有更新 `taskProgressMap`：

```typescript
onEvent("batch_cancelled", (data) => {
    processing.value = false;
    // ← 缺少对 taskProgressMap 中各任务状态的更新
});
```

#### 3b. 取消后进度面板不消失

`ProgressPanel.vue:61` 的显示条件：
```html
<div v-if="processing || overallTotal > 0" ...>
```

`batch_cancelled` 只设了 `processing = false`，但 `overallTotal` 仍 > 0，面板不会消失。

---

## 问题 1：预设添加后需要重启才显示

### 现象

通过 "New" 按钮添加自定义预设后，下拉框不显示新预设。重启应用后可以看到。

### 与问题 2/3 无关

预设操作走 `call()` 直接调用 Python `@expose` 方法，不走事件系统：
- `save_preset()` → Python `PresetManager.save_preset()` → 写磁盘 + 更新内存列表
- `loadPresets()` → Python `PresetManager.list_presets()` → 返回所有预设

### 代码流程分析

代码链路看起来完整：`usePresets.ts:savePreset()` 成功后调用 `await loadPresets()`，`loadPresets()` 更新 `presets.value = res.data`，Vue 应该响应式更新下拉框。**无法仅从静态代码分析定位，需要运行时调试。**

### 可能的调查方向

- 检查 `save_preset` Python 端是否真的成功（`@expose` 可能吞掉了异常）
- 检查 Vue `<select>` + DaisyUI 的响应式渲染是否有已知问题
- 在 `handleSave` 和 `loadPresets` 中添加 console.log 确认执行流程

---

## 架构参考：事件流全貌

```
┌─────────────────────────────────────────────────────────────┐
│                     Python Backend                          │
│                                                             │
│  start_batch()  ──(主线程)──→  _emit("batch_progress")      │
│                                  │                          │
│  Thread(_run_all) ─────────────→  _emit("task_start")      │
│                                  _emit("task_progress")    │
│                                  _emit("task_complete")    │
│                                  _emit("task_error")      │
│                                  _emit("batch_complete")   │
│                                  _emit("batch_cancelled")  │
│                                                             │
│  cancel()  ──(主线程)──→  proc.kill()                     │
│                                                             │
│  _emit() 实际调用:                                          │
│    window.evaluate_js(                                     │
│      "document.dispatchEvent(new CustomEvent(               │
│        'pywebvue:xxx', {detail: {...}}  ← bubbles:false   │
│      ))"                                                   │
│    )                                                       │
│    ↑ 通过 AppHelper.callAfter 调度到主线程，线程安全        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ document.dispatchEvent()
                         │ bubbles: false → 不冒泡到 window
                         │
┌────────────────────────┴────────────────────────────────────┐
│                     JavaScript Frontend                     │
│                                                             │
│  window.addEventListener('pywebvue:xxx', handler)           │
│  ↑ bubble listener，冒泡阶段才触发                          │
│  ↑ 但 bubbles:false → 无冒泡阶段 → 永远不触发              │
│                                                             │
│  结果：所有事件丢失，前端状态永远不变                        │
└─────────────────────────────────────────────────────────────┘
```
