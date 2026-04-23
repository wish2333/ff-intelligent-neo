/**
 * Task progress tracking composable.
 *
 * Subscribes to task_progress and task_log events and maintains
 * reactive maps for real-time UI updates.
 */

import { ref } from "vue"
import { useBridge } from "./useBridge"
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

  on("task_progress", (detail: unknown) => {
    const { task_id, progress } = detail as {
      task_id: string
      progress: TaskProgressDTO
    }
    progressMap.value = { ...progressMap.value, [task_id]: progress }
  })

  on("task_log", (detail: unknown) => {
    const { task_id, line } = detail as { task_id: string; line: string }
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
