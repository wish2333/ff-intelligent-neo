<script setup lang="ts">
/**
 * Single task row in the task list table.
 *
 * Displays file info, state badge, progress, and action buttons.
 */
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import type { TaskDTO, TaskProgressDTO } from "../../types/task"
import { formatDuration, formatFileSize } from "../../utils/format"
import { call } from "../../bridge"
import TaskProgressBar from "./TaskProgressBar.vue"

const { t } = useI18n()

defineProps<{
  task: TaskDTO
  progress?: TaskProgressDTO
  selected: boolean
  isFirst: boolean
  isLast: boolean
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

const stateBadgeClass: Record<string, string> = {
  pending: "badge-ghost",
  running: "badge-success",
  paused: "badge-warning",
  completed: "badge-primary",
  failed: "badge-error",
  cancelled: "badge-ghost opacity-50",
}

const stateLabel = computed<Record<string, string>>(() => ({
  pending: t("taskQueue.state.pending"),
  running: t("taskQueue.state.running"),
  paused: t("taskQueue.state.paused"),
  completed: t("taskQueue.state.completed"),
  failed: t("taskQueue.state.failed"),
  cancelled: t("taskQueue.state.cancelled"),
}))

async function openFolder(path: string): Promise<void> {
  try {
    await call("open_folder", path)
  } catch {
    // silently fail
  }
}
</script>

<template>
  <tr
    class="hover"
    :class="{ 'bg-base-200/50': selected }"
    @click="emit('toggleSelect', task.id)"
  >
    <!-- Checkbox -->
    <th>
      <input
        type="checkbox"
        class="checkbox checkbox-sm checkbox-primary"
        :checked="selected"
        @click.stop="emit('toggleSelect', task.id)"
      />
    </th>

    <!-- File info -->
    <td>
      <div class="flex items-center gap-2 min-w-0">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0 opacity-50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
        </svg>
        <div class="min-w-0 flex-1">
          <div class="truncate font-medium text-sm" :title="task.file_path">
            {{ task.file_name }}
          </div>
          <div class="truncate text-xs opacity-50">
            <span v-if="task.duration_seconds > 0">{{ formatDuration(task.duration_seconds) }}</span>
            <span v-if="task.duration_seconds > 0 && task.file_size_bytes > 0"> &middot; </span>
            <span v-if="task.file_size_bytes > 0">{{ formatFileSize(task.file_size_bytes) }}</span>
          </div>
        </div>
      </div>
    </td>

    <!-- State badge -->
    <td>
      <span :class="['badge badge-sm', stateBadgeClass[task.state] ?? 'badge-ghost']">
        {{ stateLabel[task.state] ?? task.state }}
      </span>
    </td>

    <!-- Progress -->
    <td class="w-44 shrink-0 min-w-0">
      <TaskProgressBar :progress="progress" />
    </td>

    <!-- Actions -->
    <td class="shrink-0">
      <div class="flex items-center gap-1.5 whitespace-nowrap" @click.stop>
        <!-- Pending: Start + Move buttons -->
        <template v-if="task.state === 'pending'">
          <button
            class="btn btn-sm btn-primary"
            @click="emit('start', task.id)"
          >
            {{ t("taskQueue.actions.start") }}
          </button>
          <button
            class="btn btn-xs btn-ghost btn-square"
            :disabled="isFirst"
            :title="t('taskQueue.actions.moveUp')"
            @click="emit('moveUp', task.id)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd" />
            </svg>
          </button>
          <button
            class="btn btn-xs btn-ghost btn-square"
            :disabled="isLast"
            :title="t('taskQueue.actions.moveDown')"
            @click="emit('moveDown', task.id)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </template>

        <!-- Failed: Retry -->
        <button
          v-if="task.state === 'failed'"
          class="btn btn-sm btn-warning"
          @click="emit('retry', task.id)"
        >
          {{ t("taskQueue.actions.retry") }}
        </button>

        <!-- Completed/Cancelled: Reset + Open folder -->
        <button
          v-if="task.state === 'completed' || task.state === 'cancelled'"
          class="btn btn-sm btn-info"
          @click="emit('reset', task.id)"
        >
          {{ t("taskQueue.actions.reset") }}
        </button>
        <button
          v-if="task.state === 'completed' && task.output_path"
          class="btn btn-sm btn-ghost"
          @click="openFolder(task.output_path)"
        >
          {{ t("taskQueue.actions.openFolder") }}
        </button>

        <!-- Running: Pause + Stop -->
        <template v-if="task.state === 'running'">
          <button
            class="btn btn-sm btn-warning btn-outline"
            @click="emit('pause', task.id)"
          >
            {{ t("taskQueue.actions.pause") }}
          </button>
          <button
            class="btn btn-sm btn-error btn-outline"
            @click="emit('stop', task.id)"
          >
            {{ t("taskQueue.actions.stop") }}
          </button>
        </template>

        <!-- Paused: Resume + Stop -->
        <template v-if="task.state === 'paused'">
          <button
            class="btn btn-sm btn-info btn-outline"
            @click="emit('resume', task.id)"
          >
            {{ t("taskQueue.actions.resume") }}
          </button>
          <button
            class="btn btn-sm btn-error btn-outline"
            @click="emit('stop', task.id)"
          >
            {{ t("taskQueue.actions.stop") }}
          </button>
        </template>

        <!-- Log toggle: only for states that retain logs -->
        <button
          v-if="task.state === 'running' || task.state === 'failed' || task.state === 'paused'"
          class="btn btn-sm btn-ghost"
          @click="emit('showLog', task.id)"
        >
          {{ t("taskQueue.actions.log") }}
        </button>
      </div>
    </td>
  </tr>
</template>
