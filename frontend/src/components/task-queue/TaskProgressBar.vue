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
  <div v-if="progress && progress.percent > 0" class="flex items-center gap-3 text-xs opacity-80">
    <progress
      class="progress progress-primary h-2 flex-1"
      :value="progress.percent"
      max="100"
    />
    <span class="w-10 text-right font-mono">{{ Math.round(progress.percent) }}%</span>
    <span v-if="progress.total_seconds > 0" class="font-mono">
      {{ formatDuration(progress.current_seconds) }}/{{ formatDuration(progress.total_seconds) }}
    </span>
    <span v-if="progress.speed" class="font-mono">{{ progress.speed }}x</span>
    <span v-if="progress.fps" class="font-mono">{{ progress.fps }} fps</span>
  </div>
</template>
