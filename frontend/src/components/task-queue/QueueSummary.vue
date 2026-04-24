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
  <div class="flex flex-wrap items-center gap-3 rounded-lg bg-base-200 px-4 py-2 text-sm">
    <span class="font-semibold">{{ t("taskQueue.summary.queue") }}</span>
    <span class="badge badge-info">{{ summary.pending }} {{ t("taskQueue.summary.pending") }}</span>
    <span class="badge badge-success">{{ summary.running }} {{ t("taskQueue.summary.running") }}</span>
    <span class="badge badge-warning" v-if="summary.paused > 0">{{ summary.paused }} {{ t("taskQueue.summary.paused") }}</span>
    <span class="badge badge-primary" v-if="summary.completed > 0">{{ summary.completed }} {{ t("taskQueue.summary.done") }}</span>
    <span class="badge badge-error" v-if="summary.failed > 0">{{ summary.failed }} {{ t("taskQueue.summary.failed") }}</span>
  </div>
</template>
