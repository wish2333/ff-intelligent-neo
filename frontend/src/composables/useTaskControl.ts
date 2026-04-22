/**
 * Task control composable.
 *
 * Provides single-task and batch control operations that call bridge methods.
 */

import { call } from "../bridge"

export function useTaskControl() {
  async function startTask(taskId: string): Promise<boolean> {
    const res = await call<null>("start_task", taskId)
    return res.success
  }

  async function stopTask(taskId: string): Promise<boolean> {
    const res = await call<null>("stop_task", taskId)
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
    stopAll,
    pauseAll,
    resumeAll,
  }
}
