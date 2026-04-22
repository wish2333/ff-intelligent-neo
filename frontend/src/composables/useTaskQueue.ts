/**
 * Task queue state management composable.
 *
 * Manages the task list, selection state, and queue summary.
 * Listens to bridge events for real-time updates.
 */

import { ref, computed } from "vue"
import { call } from "../bridge"
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
    console.log("[useTaskQueue] addTasks calling backend with", paths.length, "paths")
    try {
      const res = await call<TaskDTO[]>("add_tasks", paths, config ?? {})
      console.log("[useTaskQueue] add_tasks response:", JSON.stringify(res)?.slice(0, 200))
      if (res.success && res.data) {
        const newIds = new Set(res.data.map((t) => t.id))
        const existing = tasks.value.filter((t) => !newIds.has(t.id))
        tasks.value = [...existing, ...res.data]
        await fetchSummary()
      } else {
        console.error("[useTaskQueue] add_tasks failed:", res.error)
      }
      return res.success && res.data ? res.data : []
    } catch (err) {
      console.error("[useTaskQueue] addTasks exception:", err)
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

  // task_added handled directly in addTasks() from response data
  // to avoid duplicates when event system is active

  on("task_removed", (detail: unknown) => {
    const { task_id } = detail as { task_id: string }
    tasks.value = tasks.value.filter((t) => t.id !== task_id)
    const next = new Set(selectedIds.value)
    next.delete(task_id)
    selectedIds.value = next
  })

  on("task_state_changed", (detail: unknown) => {
    const { task_id, new_state } = detail as {
      task_id: string
      old_state: TaskState
      new_state: TaskState
    }
    const idx = tasks.value.findIndex((t) => t.id === task_id)
    if (idx !== -1) {
      const updated = [...tasks.value]
      updated[idx] = { ...updated[idx], state: new_state }
      tasks.value = updated
    }
  })

  on("queue_changed", (detail: unknown) => {
    summary.value = detail as QueueSummary
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
