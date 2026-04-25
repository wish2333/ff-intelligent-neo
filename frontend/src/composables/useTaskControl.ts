/**
 * Task control composable.
 *
 * Provides single-task and batch control operations that call bridge methods.
 */

import { call } from "../bridge"
import type { TaskConfigDTO } from "../types/config"

export function useTaskControl() {
  async function startTask(taskId: string, config?: TaskConfigDTO): Promise<boolean> {
    const res = await call<null>("start_task", taskId, config ?? null)
    return res.success
  }

  async function stopTask(taskId: string): Promise<boolean> {
    const res = await call<null>("stop_task", taskId)
    return res.success
  }

  async function pauseTask(taskId: string): Promise<boolean> {
    const res = await call<null>("pause_task", taskId)
    return res.success
  }

  async function resumeTask(taskId: string): Promise<boolean> {
    const res = await call<null>("resume_task", taskId)
    return res.success
  }

  async function retryTask(taskId: string, config?: TaskConfigDTO): Promise<boolean> {
    const res = await call<null>("retry_task", taskId, config ?? null)
    return res.success
  }

  async function resetTask(taskId: string): Promise<boolean> {
    const res = await call<null>("reset_task", taskId)
    return res.success
  }

  async function stopAll(): Promise<boolean> {
    const res = await call<{ stopped: number }>("stop_all")
    return res.success
  }

  async function pauseAll(): Promise<boolean> {
    const res = await call<{ paused: number }>("pause_all")
    return res.success
  }

  async function resumeAll(): Promise<boolean> {
    const res = await call<{ resumed: number }>("resume_all")
    return res.success
  }

  return {
    startTask,
    stopTask,
    pauseTask,
    resumeTask,
    retryTask,
    resetTask,
    stopAll,
    pauseAll,
    resumeAll,
  }
}
