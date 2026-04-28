/**
 * Task progress tracking composable.
 *
 * Subscribes to task_progress and task_log events and maintains
 * reactive maps for real-time UI updates.
 */

import { ref } from "vue"
import { useBridge } from "./useBridge"
import { EVENT_TASK_PROGRESS } from "../utils/events"
import type { TaskProgressDTO } from "../types/task"

export function useTaskProgress() {
  const { on } = useBridge()

  const progressMap = ref<Record<string, TaskProgressDTO>>({})
  const logsMap = ref<Record<string, string[]>>({})

  function getProgress(taskId: string): TaskProgressDTO | undefined {
    return progressMap.value[taskId]
  }

  function getLogs(taskId: string): string[] {
    return logsMap.value[taskId] ?? []
  }

  on(EVENT_TASK_PROGRESS, (detail: unknown) => {
    const payload = detail as Record<string, unknown>
    if (typeof payload.task_id !== "string") return
    if (typeof payload.progress !== "object" || payload.progress === null) return
    const task_id = payload.task_id
    progressMap.value = { ...progressMap.value, [task_id]: payload.progress as TaskProgressDTO }
  })

  on("task_log", (detail: unknown) => {
    const payload = detail as Record<string, unknown>
    if (typeof payload.task_id !== "string") return
    if (typeof payload.line !== "string") return
    const task_id = payload.task_id
    const line = payload.line
    const existing = logsMap.value[task_id] ?? []
    const next = existing.length >= 500 ? existing.slice(-499) : existing
    logsMap.value = { ...logsMap.value, [task_id]: [...next, line] }
  })

  return {
    progressMap,
    logsMap,
    getProgress,
    getLogs,
  }
}
