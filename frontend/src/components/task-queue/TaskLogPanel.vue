<script setup lang="ts">
/**
 * Collapsible task log panel showing FFmpeg stderr output for a selected task.
 */
import { ref, watch, nextTick } from "vue"

const props = defineProps<{
  taskId: string | null
  logs: string[]
}>()

const containerRef = ref<HTMLElement | null>(null)

watch(
  () => props.logs.length,
  async () => {
    await nextTick()
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight
    }
  },
)
</script>

<template>
  <div
    v-if="taskId !== null"
    class="border-t border-base-300 bg-base-200"
  >
    <div class="flex items-center justify-between px-4 py-1.5">
      <span class="text-xs font-semibold opacity-70">
        Task Log ({{ logs.length }})
      </span>
      <button class="btn btn-xs btn-ghost btn-square" @click="$emit('close')">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
    <pre
      ref="containerRef"
      class="h-40 overflow-auto bg-base-300 px-4 py-2 font-mono text-xs leading-relaxed"
    ><template v-if="logs.length > 0"><span v-for="(line, i) in logs" :key="i">{{ line }}
</span></template><span v-else class="opacity-40">No log output yet.</span></pre>
  </div>
</template>
