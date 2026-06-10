# Audit Report 2.2.6-2: Completed Task Progress Display Optimization

> Date: 2026-06-10
> Branch: dev-2.2.6
> Status: Investigation Complete

## Background

Completed tasks currently display a full progress bar, "100%", and duration/duration info (e.g., `05:23/05:23`), which is redundant. User wants to replace these with more useful information: **output file size** and **compression ratio**. Additionally, speed display shows double `x` (e.g., `6.03xx`) — this bug needs fixing.

---

## Issue 1: Speed Display Double "x" Bug (BUG - HIGH)

### Symptom

Speed in progress bar shows `6.03xx` instead of `6.03x`.

### Root Cause

**Backend**: `core/ffmpeg_runner.py:23` regex captures the entire speed token including the `x` suffix:

```python
_SPEED_RE = re.compile(r"speed=\s*(\S+)")
```

FFmpeg stderr output: `speed=  6.03x`
Regex capture group result: `"6.03x"` (includes the `x`)

**Frontend**: `frontend/src/components/task-queue/TaskProgressBar.vue:27` appends another `x`:

```html
<span v-if="progress.speed" ...>{{ progress.speed }}x</span>
```

Result displayed: `6.03xx`

### Fix

**Option A (Recommended)**: Strip `x` in backend regex — single source of truth:

```python
_SPEED_RE = re.compile(r"speed=\s*([\d.]+)")
```

This captures only the numeric part (`"6.03"`), and the frontend `x` suffix stays correct.

**Option B**: Keep backend regex, remove frontend `x`:

```html
<span v-if="progress.speed" ...>{{ progress.speed }}</span>
```

**Recommendation**: Option A is preferred. Backend should normalize data to a canonical format (pure number) so the frontend controls display formatting.

### Affected Files

| File | Line | Change |
|------|------|--------|
| `core/ffmpeg_runner.py` | 23 | `_SPEED_RE` regex: capture only digits/decimal |
| `core/ffmpeg_runner.py` | 153 | `current_speed = speed_match.group(1)` — no change needed, just cleaner value |

---

## Issue 2: Completed Task Progress Info Redundancy (UX - MEDIUM)

### Current Behavior

When a task completes, `TaskProgressBar.vue` shows:

```
[=========] 100% 05:23/05:23  6.03xx  30.0fps
```

For a **completed** task, the following info is redundant:
- Progress bar (always full)
- "100%" (obvious from state badge showing "Completed")
- Duration/duration (both are identical for completed tasks)

### Desired Behavior

For **completed** tasks, replace redundant progress info with:

```
125.3MB (-42.1%)  6.03x  30.0fps
```

Where:
- `125.3MB` — output file size
- `(-42.1%)` — compression ratio (negative = smaller, positive = larger)
- Speed and fps retained as-is (with the `x` bug fixed)

For **running** tasks, keep the current progress display unchanged.

### Missing Infrastructure

Currently **no code exists** to:

1. **Capture output file size** — `Task` model (`core/models.py:358`) has `file_size_bytes` (input) and `output_path`, but no `output_file_size_bytes` field.
2. **Calculate compression ratio** — No logic anywhere to compare input vs output size.

---

## Implementation Plan

### Step 1: Add `output_file_size_bytes` to Task Model

**File**: `core/models.py`

```python
@dataclass
class Task:
    # ... existing fields ...
    file_size_bytes: int = 0          # input file size
    output_path: str = ""
    output_file_size_bytes: int = 0   # NEW: output file size (set on completion)
```

Update `to_dict()` and `from_dict()` methods accordingly.

### Step 2: Capture Output File Size on Task Completion

**File**: `core/task_runner.py`

After FFmpeg task completes successfully (~line 719), add:

```python
import os
# ... in _run_task_inner, after success transition ...
if new_state == "completed" and task.output_path:
    try:
        task.output_file_size_bytes = os.path.getsize(task.output_path)
    except OSError:
        task.output_file_size_bytes = 0
```

Similarly for auto-editor tasks (~line 625).

### Step 3: Add `output_file_size_bytes` to Frontend Type

**File**: `frontend/src/types/task.ts`

```typescript
export interface TaskDTO {
  // ... existing fields ...
  file_size_bytes: number
  output_path: string
  output_file_size_bytes: number  // NEW
}
```

### Step 4: Fix Speed Regex

**File**: `core/ffmpeg_runner.py`

```python
_SPEED_RE = re.compile(r"speed=\s*([\d.]+)")
```

### Step 5: Update TaskProgressBar.vue — Conditional Display

**File**: `frontend/src/components/task-queue/TaskProgressBar.vue`

Add a `taskState` prop to differentiate between running and completed display:

```typescript
defineProps<{
  progress: TaskProgressDTO | undefined
  taskState: string                    // NEW
  inputFileSize: number                // NEW: for compression ratio
  outputFileSize: number               // NEW: for display
}>()
```

Template logic:
- **Running/Paused** (current behavior unchanged): progress bar + percent + duration + ETA + speed + fps
- **Completed**: output file size + compression ratio + speed + fps (no progress bar, no percent, no duration)

### Step 6: Update TaskRow.vue — Pass New Props

**File**: `frontend/src/components/task-queue/TaskRow.vue`

```html
<TaskProgressBar
  :progress="progress"
  :task-state="task.state"
  :input-file-size="task.file_size_bytes"
  :output-file-size="task.output_file_size_bytes"
/>
```

### Step 7: Add i18n Keys

**File**: `frontend/src/locales/zh-CN.json` / `en.json`

```json
{
  "taskQueue": {
    "progress": {
      "outputSize": "Output {size}",
      "compressionRatio": "({ratio}%)"
    }
  }
}
```

---

## Affected Files Summary

| File | Type | Changes |
|------|------|---------|
| `core/ffmpeg_runner.py:23` | Bug fix | Speed regex: strip trailing `x` |
| `core/models.py` | Model | Add `output_file_size_bytes` field + serialization |
| `core/task_runner.py` | Logic | Capture output file size on task completion |
| `frontend/src/types/task.ts` | Type | Add `output_file_size_bytes` to `TaskDTO` |
| `frontend/src/components/task-queue/TaskProgressBar.vue` | UX | Conditional display: running vs completed |
| `frontend/src/components/task-queue/TaskRow.vue` | Props | Pass task state and file sizes to progress bar |
| `frontend/src/locales/zh-CN.json` | i18n | Add compression ratio display strings |
| `frontend/src/locales/en.json` | i18n | Add compression ratio display strings |

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Speed regex change breaks on unusual FFmpeg output | LOW | FFmpeg output format is stable; unit test the regex |
| `os.path.getsize` fails on missing file | LOW | Try/except with fallback to 0 |
| Progress bar refactoring breaks running task display | MEDIUM | Keep running display path unchanged; only modify completed path |
| Backward compatibility with persisted tasks (no `output_file_size_bytes`) | LOW | Default to 0 in `from_dict()` |

## Appendix: Data Flow (Current)

```
FFmpeg stderr
  -> ffmpeg_runner.py: regex parse (speed="6.03x", fps="30.0", time=...)
  -> TaskProgress(frozen dataclass)
  -> bridge._emit("task_progress", {task_id, progress})
  -> useTaskProgress.ts: progressMap[task_id] = payload.progress
  -> TaskProgressBar.vue: {{ progress.speed }}x  =>  "6.03xx" (BUG)
```

## Appendix: Data Flow (Proposed, Completed Tasks)

```
Task completion
  -> task_runner.py: os.path.getsize(output_path) -> task.output_file_size_bytes
  -> bridge._emit("task_state_changed", {task_id, new_state: "completed"})
  -> useTaskQueue.ts: fetchTasks() -> tasks refreshed with output_file_size_bytes
  -> TaskRow.vue: passes task.state + file sizes to TaskProgressBar
  -> TaskProgressBar.vue (completed): "125.3MB (-42.1%) 6.03x 30.0fps"
```
