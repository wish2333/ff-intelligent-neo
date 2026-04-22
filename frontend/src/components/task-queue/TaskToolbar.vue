<script setup lang="ts">
/**
 * Task toolbar with add/remove/clear actions and select-all checkbox.
 */
defineProps<{
  selectedCount: number
  totalCount: number
  isAllSelected: boolean
}>()

const emit = defineEmits<{
  addFiles: []
  removeSelected: []
  clearCompleted: []
  clearAll: []
  toggleSelectAll: []
}>()
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <button class="btn btn-sm btn-primary" @click="emit('addFiles')">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
      Add Files
    </button>

    <div class="divider divider-horizontal m-0" />

    <button
      class="btn btn-sm btn-ghost"
      :disabled="selectedCount === 0"
      @click="emit('removeSelected')"
    >
      Remove ({{ selectedCount }})
    </button>

    <button
      class="btn btn-sm btn-ghost"
      @click="emit('clearCompleted')"
    >
      Clear Done
    </button>

    <button
      class="btn btn-sm btn-ghost text-error"
      @click="emit('clearAll')"
    >
      Clear All
    </button>

    <div class="divider divider-horizontal m-0" />

    <label class="flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        class="checkbox checkbox-sm checkbox-primary"
        :checked="isAllSelected"
        :disabled="totalCount === 0"
        @change="emit('toggleSelectAll')"
      />
      Select All
    </label>
  </div>
</template>
