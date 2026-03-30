<script setup lang="ts">
import type { FileItemDTO } from "../composables/useFileQueue";
import type { TaskProgressData } from "../composables/useBatchProcess";
import FileItemRow from "./FileItemRow.vue";

defineProps<{
  files: FileItemDTO[];
  selectedIndices: Set<number>;
  taskProgressMap: Record<number, TaskProgressData>;
}>();

const emit = defineEmits<{
  toggle: [index: number, shiftKey: boolean, ctrlKey: boolean];
}>();

function handleToggle(index: number, shiftKey: boolean, ctrlKey: boolean) {
  emit("toggle", index, shiftKey, ctrlKey);
}
</script>

<template>
  <div class="flex-1 overflow-y-auto px-4 py-2">
    <div v-if="files.length === 0" class="flex h-full items-center justify-center text-base-content/40">
      <span class="text-sm">Drag files here or click "Add Files"</span>
    </div>
    <div v-else class="overflow-x-auto">
      <table class="table table-sm">
        <thead>
          <tr>
            <th class="w-10"></th>
            <th>Name</th>
            <th class="w-20">Duration</th>
            <th class="w-28">Codec</th>
            <th class="w-24">Resolution</th>
            <th class="w-20 text-right">Size</th>
            <th class="w-12">Status</th>
          </tr>
        </thead>
        <tbody>
          <FileItemRow
            v-for="(file, index) in files"
            :key="file.path"
            :file="file"
            :index="index"
            :selected="selectedIndices.has(index)"
            :task-progress="taskProgressMap[index] ?? null"
            @toggle="handleToggle"
          />
        </tbody>
      </table>
    </div>
  </div>
</template>
