<script setup lang="ts">
/**
 * Queue summary bar showing task counts by state.
 */
import { useI18n } from "vue-i18n"
import type { QueueSummary } from "../../types/task"

const { t } = useI18n()

defineProps<{ summary: QueueSummary }>()
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 rounded-lg border border-base-300 bg-base-100 px-3 py-1.5 text-sm">
    <span class="text-xs font-semibold text-base-content/70">{{ t("taskQueue.summary.queue") }}</span>
    <span class="badge badge-info badge-sm">{{ summary.pending }} {{ t("taskQueue.summary.pending") }}</span>
    <span class="badge badge-success badge-sm">{{ summary.running }} {{ t("taskQueue.summary.running") }}</span>
    <span class="badge badge-warning badge-sm" v-if="summary.paused > 0">{{ summary.paused }} {{ t("taskQueue.summary.paused") }}</span>
    <span class="badge badge-primary badge-sm" v-if="summary.completed > 0">{{ summary.completed }} {{ t("taskQueue.summary.done") }}</span>
    <span class="badge badge-error badge-sm" v-if="summary.failed > 0">{{ summary.failed }} {{ t("taskQueue.summary.failed") }}</span>
  </div>
</template>
