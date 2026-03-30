<script setup lang="ts">
defineProps<{
  logLines: string[];
}>();
</script>

<template>
  <div class="max-h-48 overflow-y-auto rounded bg-base-200 p-2">
    <pre v-if="logLines.length > 0" class="text-xs font-mono text-base-content/60 leading-relaxed whitespace-pre-wrap break-all">{{
      logLines.join("\n")
    }}</pre>
    <div v-else class="text-xs text-base-content/30 italic">No log output yet</div>
  </div>
</template>
