<script setup lang="ts">
/**
 * Task progress bar with time, speed, and FPS display.
 */
import type { TaskProgressDTO } from "../../types/task"
import { formatDuration } from "../../utils/format"

defineProps<{
  progress: TaskProgressDTO | undefined
}>()
</script>

<template>
  <div v-if="progress && progress.percent > 0" class="flex items-center gap-2 text-xs opacity-80 min-w-0 overflow-hidden">
    <progress
      class="progress progress-primary h-2 shrink-0 w-20"
      :value="progress.percent"
      max="100"
    />
    <span class="shrink-0 w-9 text-right font-mono tabular-nums">{{ Math.round(progress.percent) }}%</span>
    <span v-if="progress.total_seconds > 0" class="shrink-0 font-mono tabular-nums truncate">
      {{ formatDuration(progress.current_seconds) }}/{{ formatDuration(progress.total_seconds) }}
    </span>
    <span v-if="progress.estimated_remaining" class="shrink-0 font-mono text-info tabular-nums">
      ~{{ progress.estimated_remaining }}
    </span>
    <span v-if="progress.speed" class="shrink-0 font-mono tabular-nums">{{ progress.speed }}x</span>
    <span v-if="progress.fps" class="shrink-0 font-mono tabular-nums">{{ progress.fps }}fps</span>
  </div>
</template>
