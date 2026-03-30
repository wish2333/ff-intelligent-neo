<script setup lang="ts">
defineProps<{
  dragging: boolean;
}>();
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-primary/20 backdrop-blur-sm transition-opacity"
    :class="dragging ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'"
  >
    <div class="flex flex-col items-center gap-4 rounded-xl border-4 border-dashed border-primary bg-base-100/80 p-16">
      <span class="text-4xl">+</span>
      <span class="text-xl font-semibold text-primary">Drop files here</span>
    </div>
  </div>
</template>
