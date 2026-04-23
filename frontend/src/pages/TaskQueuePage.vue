<script setup lang="ts">
/**
 * Page 1: Task Queue
 *
 * Full task queue UI with file add/remove, task control,
 * real-time progress, drag-and-drop, and log viewing.
 */
import { onMounted, ref, computed } from "vue"
import { call, waitForPyWebView } from "../bridge"
import { useTaskQueue } from "../composables/useTaskQueue"
import { useTaskControl } from "../composables/useTaskControl"
import { useTaskProgress } from "../composables/useTaskProgress"
import { useFileDrop } from "../composables/useFileDrop"
import { useGlobalConfig } from "../composables/useGlobalConfig"

import TaskToolbar from "../components/task-queue/TaskToolbar.vue"
import QueueSummary from "../components/task-queue/QueueSummary.vue"
import BatchControlBar from "../components/task-queue/BatchControlBar.vue"
import TaskList from "../components/task-queue/TaskList.vue"
import TaskLogPanel from "../components/task-queue/TaskLogPanel.vue"

const queue = useTaskQueue()
const control = useTaskControl()
const progress = useTaskProgress()
const fileDrop = useFileDrop()
const globalConfig = useGlobalConfig()

const activeLogTaskId = ref<string | null>(null)

const logContents = computed(() => {
  if (activeLogTaskId.value === null) return []
  return progress.getLogs(activeLogTaskId.value)
})

onMounted(async () => {
  try {
    await waitForPyWebView()
    await Promise.all([queue.fetchTasks(), queue.fetchSummary()])
  } catch (err) {
    console.error("[TaskQueuePage] mount failed:", err)
  }
})

// --- Handlers ---

async function handleAddFiles(): Promise<void> {
  try {
    const res = await call<string[]>("select_files")
    if (!res.success) {
      console.error("[TaskQueuePage] select_files failed:", res.error)
      return
    }
    if (!res.data || res.data.length === 0) return
    console.log("[TaskQueuePage] selected files:", res.data)
    const added = await queue.addTasks(res.data, globalConfig.toTaskConfig())
    console.log("[TaskQueuePage] added tasks:", added.length)
  } catch (err) {
    console.error("[TaskQueuePage] handleAddFiles error:", err)
  }
}

async function handleDrop(): Promise<void> {
  try {
    const paths = await fileDrop.onDrop()
    console.log("[TaskQueuePage] dropped files:", paths)
    if (paths.length > 0) {
      const added = await queue.addTasks(paths, globalConfig.toTaskConfig())
      console.log("[TaskQueuePage] added tasks:", added.length)
    }
  } catch (err) {
    console.error("[TaskQueuePage] handleDrop error:", err)
  }
}

async function handleStartAllPending(): Promise<void> {
  try {
    const pending = queue.pendingTasks.value
    for (const task of pending) {
      await control.startTask(task.id)
    }
  } catch (err) {
    console.error("[TaskQueuePage] handleStartAllPending error:", err)
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
    class="flex flex-1 flex-col gap-3 p-4"
    @dragenter="fileDrop.onDragEnter"
    @dragover="fileDrop.onDragOver"
    @dragleave="fileDrop.onDragLeave"
    @drop.prevent="handleDrop"
  >
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
        <p class="text-lg font-semibold text-primary">Drop files here</p>
      </div>
    </div>

    <!-- Toolbar -->
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
      @start="control.startTask"
      @stop="control.stopTask"
      @pause="control.pauseTask"
      @resume="control.resumeTask"
      @retry="control.retryTask"
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
  </div>
</template>
