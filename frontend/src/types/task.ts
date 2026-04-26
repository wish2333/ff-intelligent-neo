/** Task-related type definitions. */

export type TaskState =
  | "pending"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled"

export interface TaskProgressDTO {
  percent: number
  current_seconds: number
  total_seconds: number
  speed: string
  fps: string
  frame: number
  estimated_remaining: string
}

export interface TaskDTO {
  id: string
  file_path: string
  file_name: string
  file_size_bytes: number
  duration_seconds: number
  config: TaskConfigDTO
  task_type: string
  state: TaskState
  progress: TaskProgressDTO
  output_path: string
  error: string
  log_lines: string[]
  created_at: string
  started_at: string
  completed_at: string
}

export interface QueueSummary {
  pending: number
  running: number
  paused: number
  completed: number
  failed: number
  cancelled: number
}

import type { TaskConfigDTO } from "./config"
