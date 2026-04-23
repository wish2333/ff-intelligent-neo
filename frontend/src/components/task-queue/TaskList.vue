<script setup lang="ts">
/**
 * Scrollable task list table container.
 */
import TaskRow from "./TaskRow.vue"
import type { TaskDTO, TaskProgressDTO } from "../../types/task"

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
  moveUp: [taskId: string]
  moveDown: [taskId: string]
  showLog: [taskId: string]
}>()
</script>

<template>
  <div class="flex-1 overflow-auto rounded-lg border border-base-300">
    <table class="table table-sm">
      <thead>
        <tr>
          <th class="w-10">
            <input type="checkbox" class="checkbox checkbox-sm checkbox-primary" disabled />
          </th>
          <th>File</th>
          <th class="w-24">State</th>
          <th class="w-52">Progress</th>
          <th class="w-36">Info</th>
          <th class="w-52">Actions</th>
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
      <p class="text-sm">No tasks yet</p>
      <p class="text-xs mt-1">Add files to get started</p>
    </div>
  </div>
</template>
