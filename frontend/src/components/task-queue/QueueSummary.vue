<script setup lang="ts">
/**
 * Queue summary bar showing task counts by state.
 */
import type { QueueSummary } from "../../types/task"

defineProps<{ summary: QueueSummary }>()
</script>

<template>
  <div class="flex flex-wrap items-center gap-3 rounded-lg bg-base-200 px-4 py-2 text-sm">
    <span class="font-semibold">Queue:</span>
    <span class="badge badge-info">{{ summary.pending }} Pending</span>
    <span class="badge badge-success">{{ summary.running }} Running</span>
    <span class="badge badge-warning" v-if="summary.paused > 0">{{ summary.paused }} Paused</span>
    <span class="badge badge-primary" v-if="summary.completed > 0">{{ summary.completed }} Done</span>
    <span class="badge badge-error" v-if="summary.failed > 0">{{ summary.failed }} Failed</span>
  </div>
</template>
