# Audit Report v2.2.6 - Task Queue Page Issues

**Date**: 2026-06-10
**Auditor**: Claude
**Scope**: Task Queue Page (`TaskQueuePage.vue`) - task ordering and scrollbar behavior
**Severity**: High (functional defects affecting core user workflow)
**Status**: Architect-approved, product decision confirmed (see below)
**Product Decision**: Keep FIFO order (oldest-top, newest-bottom). Auto-scroll to bottom so user sees newest tasks first. Execution remains oldest-first.

---

## Summary

Task Queue page has two UX defects:
1. Tasks are displayed oldest-first (top) to newest-first (bottom) -- should be reversed
2. No vertical scrollbar appears when tasks exceed the visible area -- overflow content is silently clipped

---

## Issue 1: Task Order Reversed (oldest-first instead of newest-first)

### Expected Behavior

Newly added tasks should appear at the **top** of the list. Users expect a "newest first" ordering from top to bottom, consistent with common queue/feed UX patterns.

### Actual Behavior

Newly added tasks appear at the **bottom**. The list displays in insertion order: oldest task at index 0 (top), newest at the end (bottom).

### Root Cause Analysis

The task ordering is entirely determined by the backend array order with no client-side reversal:

**Backend** (`core/task_queue.py`):

```python
# line 73 - new tasks appended to END of list
def add_task(self, task: Task) -> Task:
    with self._lock:
        self._tasks.append(task)      # <-- oldest at index 0, newest at end
        ...

# line 79 - batch add also appends to END
def add_tasks(self, tasks: list[Task]) -> list[Task]:
    with self._lock:
        self._tasks.extend(tasks)     # <-- same FIFO ordering
        ...

# line 96 - returns in queue order (oldest first)
def get_all_tasks(self) -> list[dict]:
    with self._lock:
        return [t.to_dict() for t in self._tasks]  # <-- preserves insertion order
```

**Frontend** (`useTaskQueue.ts`):

```ts
// line 51-53 - stores backend array as-is, no reversal
async function fetchTasks(): Promise<void> {
    const res = await call<TaskDTO[]>("get_tasks")
    if (res.success && res.data) {
        tasks.value = res.data           // <-- same order as backend
    }
}

// line 74-76 - new tasks appended at END of existing array
async function addTasks(paths: string[], config?: TaskConfigDTO): Promise<TaskDTO[]> {
    const res = await call<TaskDTO[]>("add_tasks", paths, config ?? {})
    if (res.success && res.data) {
        const newIds = new Set(res.data.map((t) => t.id))
        const existing = tasks.value.filter((t) => !newIds.has(t.id))
        tasks.value = [...existing, ...res.data]  // <-- new at end
    }
}
```

**Rendering** (`TaskList.vue`):

```html
<!-- line 48 - iterates in raw array order -->
<TaskRow v-for="(task, index) in tasks" :key="task.id" ... />
```

### Data Flow

```
User adds file
  -> Backend: _tasks.append(task)         [newest at END]
  -> get_all_tasks() returns insertion order [oldest=index 0]
  -> Frontend: tasks.value = res.data       [oldest=index 0]
  -> v-for renders index 0 first            [oldest at TOP]
```

### Architectural Analysis

Before proposing fixes, we must resolve a fundamental UX question: **what is the expected execution direction?**

| Pattern | Display Order | Execution Direction | User Expectation |
|---------|--------------|--------------------|------------------|
| FIFO Queue (current) | Oldest top, Newest bottom | Top-down | "Queue fills from bottom, executes from top" |
| LIFO Stack (newest-top) | Newest top, Oldest bottom | Top-down | "Most recent task starts first" |
| Hybrid (display reversed, FIFO execution) | Newest top, Oldest bottom | **Bottom-up** | Contradictory -- progress bars light up from bottom |

**Core UX Contradiction**: If we only reverse the display (frontend-only fix) but keep FIFO execution, then clicking "Start All Pending" causes tasks to execute **from the bottom of the screen upward**. This violates the universal expectation that queues execute "from top to bottom." Any frontend-only reversal that doesn't also change execution order creates this dissonance.

### Recommended Fix (Product Decision: FIFO + Auto-scroll)

**Decision**: Keep FIFO order (oldest at top, newest at bottom). Execution remains oldest-first. Instead of reordering, auto-scroll the task list to the bottom so users see the newest tasks immediately.

**Why this approach**: No backend changes needed. No display/logic index mismatch. No UX contradiction between display and execution direction. The scroll position is the only thing that changes.

**Implementation**: `TaskList.vue` exposes a `scrollToBottom()` method via `defineExpose`. `TaskQueuePage.vue` calls it after `addTasks()` and on initial mount after `fetchTasks()`. Uses `nextTick()` to ensure DOM is rendered before scrolling.

```ts
// TaskList.vue
const scrollContainer = ref<HTMLElement | null>(null)

async function scrollToBottom(): Promise<void> {
  await nextTick()
  const el = scrollContainer.value
  if (el) el.scrollTop = el.scrollHeight
}

defineExpose({ scrollToBottom })
```

```ts
// TaskQueuePage.vue -- after adding tasks
await queue.addTasks(res.data, globalConfig.toTaskConfig())
taskListRef.value?.scrollToBottom()
```

---

## Issue 2: No Vertical Scrollbar When Tasks Overflow

### Expected Behavior

When the number of tasks exceeds the visible area of the TaskList container, a vertical scrollbar should appear, allowing the user to scroll through all tasks.

### Actual Behavior

Tasks beyond the visible area are silently clipped (hidden). No scrollbar appears anywhere -- not on the TaskList container, nor on the page-level scroll container.

### Root Cause Analysis

The issue is caused by the combination of `flex-1` + `overflow-hidden` on the TaskList wrapper, which creates a fixed-height container that clips overflow content without any scroll mechanism.

**Layout hierarchy:**

```
App.vue
  <div class="flex h-screen flex-col">          -- viewport-sized flex column
    <AppNavbar />                                -- fixed height
    <router-view />                              -- renders TaskQueuePage root

TaskQueuePage.vue
  <div class="page-scroll flex min-h-0 flex-1 flex-col gap-3 p-4 overflow-y-auto">
    -- ^ flex-1: fills remaining viewport height
    -- ^ overflow-y-auto: SHOULD scroll when content overflows
    -- ^ min-h-0: allows shrinking below content size

    [Toolbar row]                                -- fixed height
    [Summary row]                                -- fixed height

    TaskList.vue
      <div class="flex-1 overflow-hidden ...">   -- << BUG IS HERE
        -- ^ flex-1: grows to fill remaining space AFTER toolbar/summary
        -- ^ overflow-hidden: CLIPS content, no scrollbar
        <table>
          <tbody>
            <TaskRow v-for="task in tasks" />    -- grows unbounded
```

**Why the page-level scrollbar also doesn't work:**

The TaskList wrapper has `flex-1` (equivalent to `flex: 1 1 0%`). In the flex column layout:
1. Toolbar and summary take their natural height
2. TaskList gets `flex-basis: 0%` and grows to fill the **remaining space**
3. The table inside TaskList may have content taller than this allocated height
4. `overflow-hidden` clips the excess -- **no scrollbar, content just disappears**
5. From the page container's perspective, TaskList fits within its allocated space (it doesn't overflow the page), so the page's `overflow-y-auto` never activates

The net effect: `flex-1` + `overflow-hidden` = a black hole where extra rows vanish without scroll capability.

### Recommended Fix

**Step 1: Enable scrolling** -- Change `overflow-hidden` to `overflow-y-auto` in `TaskList.vue`:

```html
<!-- BEFORE -->
<div class="flex-1 overflow-hidden rounded-lg border border-base-300">

<!-- AFTER -->
<div class="flex-1 overflow-y-auto rounded-lg border border-base-300">
```

**Step 2: Pin table header** -- Without this, scrolling causes the `<thead>` to scroll out of view and users lose column context. Use `sticky` positioning:

```html
<table class="table table-sm w-full">
  <!-- sticky top-0: pins header during scroll -->
  <!-- z-10: ensures header renders above tbody rows -->
  <!-- bg-base-200: opaque background to cover scrolled rows underneath -->
  <!-- shadow-sm: subtle visual separation from scrolled content -->
  <thead class="sticky top-0 z-10 bg-base-200 shadow-sm">
    <tr>...</tr>
  </thead>
  <tbody>...</tbody>
</table>
```

Alternatively, DaisyUI provides `.table-pin-rows` which can be added to the `<table>` class to achieve the same effect without manual sticky CSS.

**Step 3: Prevent double scrollbars** -- The parent page container (`TaskQueuePage.vue`) already has `overflow-y-auto`. When the viewport is extremely small (e.g., not enough room for toolbar + summary), both the page container and the TaskList could independently show scrollbars. To prevent this, the page container should suppress its own scrolling and let the TaskList be the sole scrollable region:

```html
<!-- TaskQueuePage.vue -->
<!-- BEFORE -->
<div class="page-scroll flex min-h-0 flex-1 flex-col gap-3 p-4 overflow-y-auto">

<!-- AFTER: remove overflow-y-auto, the TaskList handles its own scroll -->
<div class="page-scroll flex min-h-0 flex-1 flex-col gap-3 p-4">
```

This ensures a single, unambiguous scroll context: toolbar and summary are always visible, and only the task list scrolls.

---

## Affected Files

| File | Issue | Change Needed |
|------|-------|---------------|
| `frontend/src/components/task-queue/TaskList.vue` | #1 auto-scroll, #2 overflow | Add scroll ref + expose `scrollToBottom`; `overflow-hidden` -> `overflow-y-auto`; sticky `<thead>` |
| `frontend/src/pages/TaskQueuePage.vue` | #1 auto-scroll trigger, #2 double scrollbar | Add TaskList ref, call `scrollToBottom` on mount/after add; remove `overflow-y-auto` |

---

## Risk Assessment

| Fix | Risk | Mitigation |
|-----|------|------------|
| Auto-scroll to bottom (Issue 1) | User manual scroll gets overridden only on explicit add/mount actions | Only call `scrollToBottom` on add and mount, not on state changes |
| `overflow-y-auto` + sticky header (Issue 2) | Double scrollbar if parent `overflow-y-auto` is not removed | Remove parent `overflow-y-auto`; visual verification |

---

## Architect Review Notes

This section documents the architectural review feedback applied to the original audit report:

### Issue 1 Revisions

1. **Template inline reversal rejected**: Original Option A used `[...tasks].reverse()` in the `v-for` template. This is a performance anti-pattern -- Vue re-executes the expression on every render (progress updates, state changes, active log toggle), causing repeated array allocation and GC pressure on large queues. If frontend reversal is chosen, it must use a `computed` property.

2. **Event swapping rejected**: Original Option A swapped `@move-up="emit('moveDown')"` and `@move-down="emit('moveUp')"` in the template. This creates a fragile "visual vs logical index" trap for future maintainers and makes `isFirst`/`isLast` semantics confusing.

3. **UX contradiction identified**: Frontend-only display reversal without changing execution order causes "bottom-up execution" -- progress bars light up from the bottom of the screen, violating the universal "top-down" queue expectation. This makes Option B (backend fix) the correct approach if the product requires "newest on top + top-down execution."

### Issue 2 Revisions

1. **Sticky header added**: Original fix only changed `overflow-hidden` to `overflow-y-auto`. Without pinning the `<thead>`, column headers scroll out of view. Added `sticky top-0 z-10 bg-base-200 shadow-sm` to `<thead>`.

2. **Double scrollbar prevention**: Identified that both `TaskQueuePage.vue` (parent `overflow-y-auto`) and `TaskList.vue` (new `overflow-y-auto`) could show scrollbars simultaneously on small viewports. Fix: remove `overflow-y-auto` from the page container so the TaskList is the sole scroll context.

---

## Appendix: Current Code

### A. `frontend/src/components/task-queue/TaskList.vue`

```vue
<script setup lang="ts">
/**
 * Scrollable task list table container.
 */
import { useI18n } from "vue-i18n"
import TaskRow from "./TaskRow.vue"
import type { TaskDTO, TaskProgressDTO } from "../../types/task"

const { t } = useI18n()

defineProps<{
  tasks: TaskDTO[]
  selectedIds: Set<string>
  progressMap: Record<string, TaskProgressDTO>
  activeLogTaskId: string | null
}>()

const emit = defineEmits<{
  toggleSelect: [taskId: string]
  start: [taskId: string]
  stop: [taskId: string]
  pause: [taskId: string]
  resume: [taskId: string]
  retry: [taskId: string]
  reset: [taskId: string]
  moveUp: [taskId: string]
  moveDown: [taskId: string]
  showLog: [taskId: string]
}>()
</script>

<template>
  <div class="flex-1 overflow-hidden rounded-lg border border-base-300">
    <table class="table table-sm w-full">
      <thead>
        <tr>
          <th class="w-10 shrink-0">
            <input type="checkbox" class="checkbox checkbox-sm checkbox-primary" disabled />
          </th>
          <th class="min-w-0">{{ t("taskQueue.table.file") }}</th>
          <th class="w-20 shrink-0">{{ t("taskQueue.table.state") }}</th>
          <th class="w-44 shrink-0">{{ t("taskQueue.table.progress") }}</th>
          <th class="w-52 shrink-0">{{ t("taskQueue.table.actions") }}</th>
        </tr>
      </thead>
      <tbody>
        <TaskRow
          v-for="(task, index) in tasks"
          :key="task.id"
          :task="task"
          :progress="progressMap[task.id]"
          :selected="selectedIds.has(task.id)"
          :is-first="index === 0"
          :is-last="index === tasks.length - 1"
          @toggle-select="emit('toggleSelect', $event)"
          @start="emit('start', $event)"
          @stop="emit('stop', $event)"
          @pause="emit('pause', $event)"
          @resume="emit('resume', $event)"
          @retry="emit('retry', $event)"
          @reset="emit('reset', $event)"
          @move-up="emit('moveUp', $event)"
          @move-down="emit('moveDown', $event)"
          :class="{ 'bg-base-300/20': activeLogTaskId === task.id }"
          @show-log="emit('showLog', $event)"
        />
      </tbody>
    </table>

    <!-- Empty state -->
    <div
      v-if="tasks.length === 0"
      class="flex flex-col items-center justify-center py-16 text-base-content/40"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
      <p class="text-sm">{{ t("taskQueue.noTasksYet") }}</p>
      <p class="text-xs mt-1">{{ t("taskQueue.addFilesToStart") }}</p>
    </div>
  </div>
</template>
```

### B. `frontend/src/pages/TaskQueuePage.vue`

```vue
<script setup lang="ts">
/**
 * Page 1: Task Queue
 *
 * Full task queue UI with file add/remove, task control,
 * real-time progress, drag-and-drop, and log viewing.
 */
import { onMounted, ref, computed } from "vue"
import { useI18n } from "vue-i18n"
import { call, waitForPyWebView } from "../bridge"
import { logError } from "../utils/logger"
import { useTaskQueue } from "../composables/useTaskQueue"
import { useTaskControl } from "../composables/useTaskControl"
import { useTaskProgress } from "../composables/useTaskProgress"
import { useFileDrop } from "../composables/useFileDrop"
import { useGlobalConfig } from "../composables/useGlobalConfig"
import type { PresetDTO } from "../types/preset"

import TaskToolbar from "../components/task-queue/TaskToolbar.vue"
import QueueSummary from "../components/task-queue/QueueSummary.vue"
import BatchControlBar from "../components/task-queue/BatchControlBar.vue"
import QueuePresetSelect from "../components/task-queue/QueuePresetSelect.vue"
import TaskList from "../components/task-queue/TaskList.vue"
import TaskLogPanel from "../components/task-queue/TaskLogPanel.vue"

const { t } = useI18n()

const queue = useTaskQueue()
const control = useTaskControl()
const progress = useTaskProgress()
const fileDrop = useFileDrop()
const globalConfig = useGlobalConfig()

const activeLogTaskId = ref<string | null>(null)
const isReady = ref(false)

const logContents = computed(() => {
  if (activeLogTaskId.value === null) return []
  return progress.getLogs(activeLogTaskId.value)
})

onMounted(async () => {
  try {
    await waitForPyWebView()
    await Promise.all([queue.fetchTasks(), queue.fetchSummary()])
  } catch (err) {
    logError("TaskQueuePage", "mount failed", err)
  } finally {
    isReady.value = true
  }
})

// --- Handlers ---

async function handleAddFiles(): Promise<void> {
  try {
    const res = await call<string[]>("select_files")
    if (!res.success) {
      logError("TaskQueuePage", "select_files failed", res.error)
      return
    }
    if (!res.data || res.data.length === 0) return
    await queue.addTasks(res.data, globalConfig.toTaskConfig())
  } catch (err) {
    logError("TaskQueuePage", "handleAddFiles error", err)
  }
}

async function handleDrop(): Promise<void> {
  try {
    const paths = await fileDrop.onDrop()
    if (paths.length > 0) {
      await queue.addTasks(paths, globalConfig.toTaskConfig())
    }
  } catch (err) {
    logError("TaskQueuePage", "handleDrop error", err)
  }
}

function currentConfig() {
  return globalConfig.toTaskConfig()
}

function handlePresetApply(preset: PresetDTO) {
  globalConfig.loadFromTaskConfig(preset.config)
}

async function handleStartAllPending(): Promise<void> {
  try {
    const pending = queue.pendingTasks.value
    const cfg = currentConfig()
    for (const task of pending) {
      await control.startTask(task.id, cfg)
    }
  } catch (err) {
    logError("TaskQueuePage", "handleStartAllPending error", err)
  }
}

function handleToggleLog(taskId: string): void {
  activeLogTaskId.value = activeLogTaskId.value === taskId ? null : taskId
}

async function handleMoveUp(taskId: string): Promise<void> {
  const tasks = queue.tasks.value
  const index = tasks.findIndex((t) => t.id === taskId)
  if (index <= 0) return
  const newOrder = [...tasks]
  ;[newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]]
  await call("reorder_tasks", newOrder.map((t) => t.id))
  // Refresh tasks from backend to get the new order
  await queue.fetchTasks()
}

async function handleMoveDown(taskId: string): Promise<void> {
  const tasks = queue.tasks.value
  const index = tasks.findIndex((t) => t.id === taskId)
  if (index < 0 || index >= tasks.length - 1) return
  const newOrder = [...tasks]
  ;[newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]]
  await call("reorder_tasks", newOrder.map((t) => t.id))
  await queue.fetchTasks()
}
</script>

<template>
  <div
    class="page-scroll flex min-h-0 flex-1 flex-col gap-3 p-4 overflow-y-auto"
    @dragenter="fileDrop.onDragEnter"
    @dragover="fileDrop.onDragOver"
    @dragleave="fileDrop.onDragLeave"
    @drop.prevent="handleDrop"
  >
    <!-- Loading state -->
    <div v-if="!isReady" class="flex flex-1 items-center justify-center">
      <span class="loading loading-spinner loading-lg text-primary" />
    </div>

    <template v-else>
    <!-- Drag overlay -->
    <div
      v-if="fileDrop.isDragging.value"
      class="pointer-events-none fixed inset-0 z-50 flex items-center justify-center bg-primary/10"
    >
      <div class="rounded-xl border-2 border-dashed border-primary bg-base-100/80 px-12 py-8 text-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-10 w-10 text-primary mb-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p class="text-lg font-semibold text-primary">{{ t("taskQueue.dropFilesHere") }}</p>
      </div>
    </div>

    <!-- Toolbar + Preset -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <TaskToolbar
        :selected-count="queue.selectedIds.value.size"
        :total-count="queue.tasks.value.length"
        :is-all-selected="queue.isAllSelected.value"
        @add-files="handleAddFiles"
        @remove-selected="queue.removeTasks([...queue.selectedIds.value])"
        @clear-completed="queue.clearCompleted()"
        @clear-all="queue.clearAll()"
        @toggle-select-all="queue.toggleSelectAll()"
      />
      <QueuePresetSelect @apply="handlePresetApply" />
    </div>

    <!-- Summary + Batch controls -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <QueueSummary :summary="queue.summary.value" />
      <BatchControlBar
        :running-count="queue.summary.value.running"
        :paused-count="queue.summary.value.paused"
        :pending-count="queue.summary.value.pending"
        @start-all-pending="handleStartAllPending"
        @stop-all="control.stopAll()"
        @pause-all="control.pauseAll()"
        @resume-all="control.resumeAll()"
      />
    </div>

    <!-- Task list -->
    <TaskList
      :tasks="queue.tasks.value"
      :selected-ids="queue.selectedIds.value"
      :progress-map="progress.progressMap.value"
      :active-log-task-id="activeLogTaskId"
      @toggle-select="queue.toggleSelect"
      @start="(id: string) => control.startTask(id, currentConfig())"
      @stop="control.stopTask"
      @pause="control.pauseTask"
      @resume="control.resumeTask"
      @retry="(id: string) => control.retryTask(id, currentConfig())"
      @reset="control.resetTask"
      @move-up="handleMoveUp"
      @move-down="handleMoveDown"
      @show-log="handleToggleLog"
    />

    <!-- Log panel -->
    <TaskLogPanel
      :task-id="activeLogTaskId"
      :logs="logContents"
      @close="activeLogTaskId = null"
    />
    </template>
  </div>
</template>
```

### C. `frontend/src/composables/useTaskQueue.ts`

```ts
/**
 * Task queue state management composable.
 *
 * Manages the task list, selection state, and queue summary.
 * Listens to bridge events for real-time updates.
 */

import { ref, computed } from "vue"
import { call } from "../bridge"
import { logError } from "../utils/logger"
import { EVENT_TASK_STATE_CHANGED, EVENT_QUEUE_CHANGED, EVENT_TASK_INFO_UPDATED } from "../utils/events"
import { useBridge } from "./useBridge"
import type { TaskDTO, QueueSummary, TaskState } from "../types/task"
import type { TaskConfigDTO } from "../types/config"

export function useTaskQueue() {
  const { on } = useBridge()

  const tasks = ref<TaskDTO[]>([])
  const selectedIds = ref<Set<string>>(new Set())
  const loading = ref(false)

  const summary = ref<QueueSummary>({
    pending: 0,
    running: 0,
    paused: 0,
    completed: 0,
    failed: 0,
    cancelled: 0,
  })

  const selectedTasks = computed(() =>
    tasks.value.filter((t) => selectedIds.value.has(t.id)),
  )

  const isAllSelected = computed(
    () => tasks.value.length > 0 && selectedIds.value.size === tasks.value.length,
  )

  const pendingTasks = computed(() =>
    tasks.value.filter((t) => t.state === "pending"),
  )

  const activeTaskCount = computed(
    () => summary.value.running + summary.value.paused,
  )

  async function fetchTasks(): Promise<void> {
    loading.value = true
    try {
      const res = await call<TaskDTO[]>("get_tasks")
      if (res.success && res.data) {
        tasks.value = res.data
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary(): Promise<void> {
    const res = await call<QueueSummary>("get_queue_summary")
    if (res.success && res.data) {
      summary.value = res.data
    }
  }

  async function addTasks(
    paths: string[],
    config?: TaskConfigDTO,
  ): Promise<TaskDTO[]> {
    try {
      const res = await call<TaskDTO[]>("add_tasks", paths, config ?? {})
      if (res.success && res.data) {
        const newIds = new Set(res.data.map((t) => t.id))
        const existing = tasks.value.filter((t) => !newIds.has(t.id))
        tasks.value = [...existing, ...res.data]
        await fetchSummary()
      } else {
        logError("useTaskQueue", "add_tasks failed", res.error)
      }
      return res.success && res.data ? res.data : []
    } catch (err) {
      logError("useTaskQueue", "addTasks exception", err)
      return []
    }
  }

  async function removeTasks(taskIds: string[]): Promise<boolean> {
    const res = await call<{ removed: number }>("remove_tasks", taskIds)
    if (res.success) {
      const next = new Set(selectedIds.value)
      for (const id of taskIds) {
        next.delete(id)
      }
      selectedIds.value = next
      tasks.value = tasks.value.filter((t) => !taskIds.includes(t.id))
      await fetchSummary()
    }
    return res.success
  }

  async function reorderTasks(taskIds: string[]): Promise<boolean> {
    const res = await call<null>("reorder_tasks", taskIds)
    if (res.success) {
      const ordered = taskIds
        .map((id) => tasks.value.find((t) => t.id === id))
        .filter(Boolean) as TaskDTO[]
      tasks.value = ordered
    }
    return res.success
  }

  async function clearCompleted(): Promise<void> {
    const res = await call<{ removed: number }>("clear_completed")
    if (res.success) {
      tasks.value = tasks.value.filter((t) => t.state !== "completed")
      await fetchSummary()
    }
  }

  async function clearAll(): Promise<void> {
    const res = await call<{ removed: number }>("clear_all")
    if (res.success) {
      tasks.value = []
      selectedIds.value.clear()
      await fetchSummary()
    }
  }

  function toggleSelect(taskId: string): void {
    const next = new Set(selectedIds.value)
    if (next.has(taskId)) {
      next.delete(taskId)
    } else {
      next.add(taskId)
    }
    selectedIds.value = next
  }

  function toggleSelectAll(): void {
    if (isAllSelected.value) {
      selectedIds.value = new Set()
    } else {
      selectedIds.value = new Set(tasks.value.map((t) => t.id))
    }
  }

  function getTaskById(id: string): TaskDTO | undefined {
    return tasks.value.find((t) => t.id === id)
  }

  // --- Event listeners ---

  on("task_removed", (detail: unknown) => {
    const payload = detail as Record<string, unknown>
    if (typeof payload.task_id !== "string") return
    tasks.value = tasks.value.filter((t) => t.id !== payload.task_id)
    const next = new Set(selectedIds.value)
    next.delete(payload.task_id)
    selectedIds.value = next
  })

  on(EVENT_TASK_STATE_CHANGED, (detail: unknown) => {
    const payload = detail as Record<string, unknown>
    if (typeof payload.task_id !== "string") return
    if (typeof payload.new_state !== "string") return
    const task_id = payload.task_id as string
    const new_state = payload.new_state as TaskState
    const idx = tasks.value.findIndex((t) => t.id === task_id)
    if (idx !== -1) {
      const updated = [...tasks.value]
      updated[idx] = { ...updated[idx], state: new_state }
      tasks.value = updated
    }
    if (new_state === "completed" || new_state === "failed") {
      fetchTasks()
    }
  })

  on(EVENT_QUEUE_CHANGED, (detail: unknown) => {
    if (detail && typeof detail === "object") {
      const d = detail as Record<string, unknown>
      summary.value = {
        pending: typeof d.pending === "number" ? d.pending : 0,
        running: typeof d.running === "number" ? d.running : 0,
        paused: typeof d.paused === "number" ? d.paused : 0,
        completed: typeof d.completed === "number" ? d.completed : 0,
        failed: typeof d.failed === "number" ? d.failed : 0,
        cancelled: typeof d.cancelled === "number" ? d.cancelled : 0,
      }
    }
  })

  on(EVENT_TASK_INFO_UPDATED, (detail: unknown) => {
    const payload = detail as Record<string, unknown>
    if (typeof payload.task_id !== "string") return
    const task_id = payload.task_id as string
    const idx = tasks.value.findIndex((t) => t.id === task_id)
    if (idx !== -1) {
      const updated = [...tasks.value]
      updated[idx] = {
        ...updated[idx],
        file_name: typeof payload.file_name === "string" ? payload.file_name : updated[idx].file_name,
        duration_seconds: typeof payload.duration_seconds === "number" ? payload.duration_seconds : updated[idx].duration_seconds,
        file_size_bytes: typeof payload.file_size_bytes === "number" ? payload.file_size_bytes : updated[idx].file_size_bytes,
      }
      tasks.value = updated
    }
  })

  return {
    tasks,
    selectedIds,
    selectedTasks,
    isAllSelected,
    summary,
    loading,
    pendingTasks,
    activeTaskCount,
    fetchTasks,
    fetchSummary,
    addTasks,
    removeTasks,
    reorderTasks,
    clearCompleted,
    clearAll,
    toggleSelect,
    toggleSelectAll,
    getTaskById,
  }
}
```

### D. `core/task_queue.py`

```python
"""Task queue: CRUD, state machine, ordering, and JSON persistence."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable

from core.models import Task, TaskState, VALID_TRANSITIONS
from core.paths import get_data_dir

_SAVE_DEBOUNCE_SECONDS = 0.5


def _queue_path() -> Path:
    return get_data_dir() / "queue_state.json"


class TaskQueue:
    """In-memory task queue with optional JSON persistence."""

    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._lock = threading.RLock()
        self._save_timer: threading.Timer | None = None
        self._on_change: Callable[[dict], None] | None = None

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def set_on_change(self, fn: Callable[[dict], None]) -> None:
        """Register a callback fired on any queue mutation."""
        self._on_change = fn

    def _notify(self) -> None:
        if self._on_change:
            self._on_change(self.get_summary())

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> Task:
        with self._lock:
            self._tasks.append(task)
            self._notify()
            return task

    def add_tasks(self, tasks: list[Task]) -> list[Task]:
        with self._lock:
            self._tasks.extend(tasks)
            self._notify()
            return tasks

    def remove_tasks(self, task_ids: list[str]) -> int:
        with self._lock:
            before = len(self._tasks)
            self._tasks = [t for t in self._tasks if t.id not in task_ids]
            removed = before - len(self._tasks)
            if removed:
                self._notify()
            return removed

    def get_task(self, task_id: str) -> Task | None:
        with self._lock:
            for t in self._tasks:
                if t.id == task_id:
                    return t
        return None

    def get_all_tasks(self) -> list[dict]:
        """Return serialised copies of all tasks (queue order)."""
        with self._lock:
            return [t.to_dict() for t in self._tasks]

    def get_all_tasks_objects(self) -> list[Task]:
        """Return references to all task objects (queue order)."""
        with self._lock:
            return list(self._tasks)

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def transition_task(self, task_id: str, new_state: TaskState) -> str | None:
        with self._lock:
            task = self._get_by_id_unlocked(task_id)
            if task is None:
                return None
            old = task.transition(new_state)
            self._notify()
            self._schedule_save()
            return old

    # ------------------------------------------------------------------
    # Ordering
    # ------------------------------------------------------------------

    def reorder_tasks(self, task_ids: list[str]) -> None:
        """Reorder the queue to match *task_ids* (first = top)."""
        with self._lock:
            existing = {t.id: t for t in self._tasks}
            ordered: list[Task] = []
            for tid in task_ids:
                if tid in existing:
                    ordered.append(existing.pop(tid))
            ordered.extend(existing.values())
            self._tasks = ordered
            self._schedule_save()

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def clear_completed(self) -> int:
        with self._lock:
            before = len(self._tasks)
            self._tasks = [
                t for t in self._tasks if t.state != "completed"
            ]
            removed = before - len(self._tasks)
            if removed:
                self._notify()
                self._schedule_save()
            return removed

    def clear_all(self) -> int:
        with self._lock:
            removed = len(self._tasks)
            self._tasks.clear()
            if removed:
                self._notify()
                self._schedule_save()
            return removed

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(self) -> dict[str, int]:
        with self._lock:
            summary: dict[str, int] = {
                "pending": 0,
                "running": 0,
                "paused": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
            }
            for t in self._tasks:
                summary[t.state] += 1
            return summary

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_state(self) -> None:
        """Persist current queue to JSON (debounced in normal flow)."""
        from core.logging import get_logger
        _logger = get_logger()

        with self._lock:
            non_terminal = [t for t in self._tasks if t.state not in ("completed", "failed", "cancelled")]
            terminal = [t for t in self._tasks if t.state in ("completed", "failed", "cancelled")]
            terminal.sort(key=lambda t: t.completed_at or "", reverse=True)
            terminal = terminal[:50]
            saved_ids = {t.id for t in non_terminal + terminal}
            ordered = [t for t in self._tasks if t.id in saved_ids]
            to_save = [t.to_dict() for t in ordered]

        path = _queue_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": "2.0.0",
                "saved_at": datetime.now().isoformat(),
                "tasks": to_save,
            }
            import tempfile as _tempfile
            fd, tmp_path = _tempfile.mkstemp(
                dir=path.parent, suffix=".tmp", prefix="queue_"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                os.replace(tmp_path, str(path))
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except OSError as exc:
            _logger.error("Failed to save queue state: {}", exc)

    def load_state(self) -> None:
        """Load queue from JSON on startup with state recovery."""
        from core.logging import get_logger
        _logger = get_logger()

        path = _queue_path()
        if not path.exists():
            return
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
            tasks = [Task.from_dict(d) for d in data.get("tasks", [])]

            recovered = 0
            for task in tasks:
                if task.state in ("running", "paused"):
                    task.state = "failed"
                    task.error = "Process interrupted by app close"
                    task.completed_at = datetime.now().isoformat()
                    recovered += 1

            if recovered:
                _logger.info(
                    "Queue recovery: {} tasks reset to failed (app was closed)",
                    recovered,
                )

            with self._lock:
                self._tasks = tasks
        except (json.JSONDecodeError, OSError) as exc:
            _logger.error("Failed to load queue state: {}", exc)

    def _schedule_save(self) -> None:
        """Debounced save."""
        if self._save_timer is not None:
            self._save_timer.cancel()

        def _do_save() -> None:
            self._save_timer = None
            self.save_state()

        self._save_timer = threading.Timer(_SAVE_DEBOUNCE_SECONDS, _do_save)
        self._save_timer.daemon = True
        self._save_timer.start()

    def _get_by_id_unlocked(self, task_id: str) -> Task | None:
        for t in self._tasks:
            if t.id == task_id:
                return t
        return None
```

### E. `frontend/src/App.vue`

```vue
<script setup lang="ts">
/**
 * Root layout: AppNavbar + router-view.
 * Provides shared state via provide/inject pattern.
 */
import AppNavbar from "./components/layout/AppNavbar.vue"
</script>

<template>
  <div class="flex h-screen flex-col bg-base-100 text-base-content">
    <AppNavbar />
    <router-view />
  </div>
</template>
```

### F. `frontend/src/style.css`

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: dark --default, light;
}

/* Reserve scrollbar space to prevent layout shift on all pages */
html {
  scrollbar-gutter: stable;
}

/* Apply to page-level scroll containers that create their own scrolling context */
.overflow-y-auto,
.overflow-auto {
  scrollbar-gutter: stable;
}

/* Mirror the scrollbar gutter on the left edge for symmetric page layout */
.page-scroll {
  padding-left: calc(1rem + 1.5rem);
}
```
