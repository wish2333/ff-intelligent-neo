<script setup lang="ts">
import { inject } from "vue";
import { useBatchProcess, type TaskProgressData } from "../composables/useBatchProcess";
import LogViewer from "./LogViewer.vue";

const batchProcess = inject<ReturnType<typeof useBatchProcess>>("batchProcess");
if (!batchProcess) {
  throw new Error("ProgressPanel: batchProcess not provided. Make sure App.vue provides it.");
}

const {
  processing,
  overallProgress,
  overallTotal,
  overallCompleted,
  taskProgressMap,
  logLines,
} = batchProcess;

function statusBadge(status: string): string {
  switch (status) {
    case "running": return "badge-info";
    case "done": return "badge-success";
    case "error": return "badge-error";
    default: return "badge-ghost";
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case "done": return "Done";
    case "error": return "Error";
    case "running": return "Running";
    default: return status;
  }
}

function formatProgressInfo(task: TaskProgressData): string {
  const parts: string[] = [];
  if (task.speed) parts.push(`speed=${task.speed}`);
  if (task.fps) parts.push(`fps=${task.fps}`);
  return parts.join(" | ");
}

const tasksList = () => Object.values(taskProgressMap.value);
</script>

<template>
  <div v-if="processing || overallTotal > 0" class="border-t border-base-300 px-4 py-2">
    <!-- Overall progress -->
    <div class="flex items-center gap-3 mb-2">
      <span class="text-xs text-base-content/50 w-16">Overall</span>
      <progress
        class="progress progress-primary flex-1"
        :value="overallProgress"
        max="100"
      ></progress>
      <span class="text-xs text-base-content/50 w-12 text-right">
        {{ overallCompleted }}/{{ overallTotal }}
      </span>
    </div>

    <!-- Per-file progress -->
    <div v-if="tasksList().length > 0" class="flex flex-col gap-1 mb-2">
      <div
        v-for="task in tasksList()"
        :key="task.file_index"
        class="flex items-center gap-2"
      >
        <span class="badge badge-sm" :class="statusBadge(task.status)">{{ statusLabel(task.status) }}</span>
        <span class="text-xs truncate max-w-32" :title="task.file_name">{{ task.file_name }}</span>
        <progress
          v-if="task.status === 'running'"
          class="progress progress-info flex-1"
          :value="task.percent"
          max="100"
        ></progress>
        <span v-if="task.status === 'running' && formatProgressInfo(task)" class="text-xs text-base-content/50 whitespace-nowrap">
          {{ formatProgressInfo(task) }}
        </span>
        <span v-if="task.status === 'running'" class="text-xs text-base-content/50 w-10 text-right">
          {{ task.percent.toFixed(0) }}%
        </span>
        <span v-if="task.status === 'error'" class="text-xs text-error truncate max-w-xs" :title="task.error">
          {{ task.error }}
        </span>
      </div>
    </div>

    <!-- Log viewer -->
    <details v-if="logLines.length > 0" class="collapse collapse-arrow bg-base-200">
      <summary class="collapse-title text-xs py-1 min-h-0">FFmpeg Log</summary>
      <div class="collapse-content">
        <LogViewer :log-lines="logLines" />
      </div>
    </details>
  </div>
</template>
