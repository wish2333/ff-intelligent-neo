<script setup lang="ts">
/**
 * Batch control bar: pause all, resume all, stop all, start all pending.
 */
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
  <div class="flex flex-wrap items-center gap-2 text-sm">
    <span class="font-semibold opacity-70">Batch:</span>
    <button
      class="btn btn-xs btn-success btn-outline"
      :disabled="pendingCount === 0"
      @click="emit('startAllPending')"
    >
      Start All ({{ pendingCount }})
    </button>
    <button
      class="btn btn-xs btn-warning btn-outline"
      :disabled="runningCount === 0"
      @click="emit('pauseAll')"
    >
      Pause All ({{ runningCount }})
    </button>
    <button
      class="btn btn-xs btn-info btn-outline"
      :disabled="pausedCount === 0"
      @click="emit('resumeAll')"
    >
      Resume All ({{ pausedCount }})
    </button>
    <button
      class="btn btn-xs btn-error btn-outline"
      :disabled="runningCount === 0 && pausedCount === 0 && pendingCount === 0"
      @click="emit('stopAll')"
    >
      Stop All
    </button>
  </div>
</template>
