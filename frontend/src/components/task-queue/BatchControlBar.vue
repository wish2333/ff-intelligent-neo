<script setup lang="ts">
/**
 * Batch control bar: pause all, resume all, stop all, start all pending.
 */
import { useI18n } from "vue-i18n"

const { t } = useI18n()

defineProps<{
  runningCount: number
  pausedCount: number
  pendingCount: number
}>()

const emit = defineEmits<{
  startAllPending: []
  stopAll: []
  pauseAll: []
  resumeAll: []
}>()
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <span class="text-sm font-semibold opacity-70">{{ t("taskQueue.batch.label") }}</span>
    <button
      class="btn btn-sm btn-success btn-outline"
      :disabled="pendingCount === 0"
      @click="emit('startAllPending')"
    >
      {{ t("taskQueue.batch.startAll", { count: pendingCount }) }}
    </button>
    <button
      class="btn btn-sm btn-warning btn-outline"
      :disabled="runningCount === 0"
      @click="emit('pauseAll')"
    >
      {{ t("taskQueue.batch.pauseAll", { count: runningCount }) }}
    </button>
    <button
      class="btn btn-sm btn-info btn-outline"
      :disabled="pausedCount === 0"
      @click="emit('resumeAll')"
    >
      {{ t("taskQueue.batch.resumeAll", { count: pausedCount }) }}
    </button>
    <button
      class="btn btn-sm btn-error btn-outline"
      :disabled="runningCount === 0 && pausedCount === 0 && pendingCount === 0"
      @click="emit('stopAll')"
    >
      {{ t("taskQueue.batch.stopAll") }}
    </button>
  </div>
</template>
