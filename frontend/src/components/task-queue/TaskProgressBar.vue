<script setup lang="ts">
/**
 * Task progress bar with time, speed, and FPS display.
 *
 * Running/paused: progress bar + percent + duration + ETA + speed + fps
 * Completed: output file size + compression ratio + speed + fps
 */
import { computed } from "vue"
import type { TaskProgressDTO } from "../../types/task"
import { formatDuration, formatFileSize } from "../../utils/format"

const props = defineProps<{
  progress: TaskProgressDTO | undefined
  taskState: string
  inputFileSize: number
  outputFileSize: number
  taskProgress?: TaskProgressDTO
}>()

/** Effective progress — prefer real-time events, fall back to TaskDTO data. */
const effectiveProgress = computed<TaskProgressDTO | undefined>(
  () => props.progress ?? props.taskProgress,
)

const compressionRatio = computed<string | null>(() => {
  if (props.inputFileSize <= 0 || props.outputFileSize <= 0) return null
  const ratio = ((props.outputFileSize - props.inputFileSize) / props.inputFileSize) * 100
  const sign = ratio > 0 ? "+" : ""
  return `${sign}${ratio.toFixed(1)}%`
})

const isCompleted = computed(() => props.taskState === "completed")
</script>

<template>
  <!-- Completed state: show output file size + compression ratio + speed + fps -->
  <div v-if="isCompleted && outputFileSize > 0" class="flex items-center gap-2 text-xs opacity-80 min-w-0 overflow-hidden">
    <span class="shrink-0 font-mono tabular-nums">{{ formatFileSize(outputFileSize) }}</span>
    <span v-if="compressionRatio" class="shrink-0 font-mono tabular-nums" :class="compressionRatio.startsWith('-') ? 'text-success' : 'text-warning'">
      ({{ compressionRatio }})
    </span>
    <span v-if="effectiveProgress?.speed" class="shrink-0 font-mono tabular-nums">{{ effectiveProgress.speed }}x</span>
    <span v-if="effectiveProgress?.fps" class="shrink-0 font-mono tabular-nums">{{ effectiveProgress.fps }}fps</span>
  </div>
  <!-- Running/paused state: show progress bar + percent + duration + ETA + speed + fps -->
  <div v-else-if="progress && progress.percent > 0" class="flex items-center gap-2 text-xs opacity-80 min-w-0 overflow-hidden">
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
