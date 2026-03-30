<script setup lang="ts">
import { ref, inject } from "vue";
import { call } from "../bridge";

defineProps<{
  processing: boolean;
  hasFiles: boolean;
}>();

const emit = defineEmits<{
  start: [presetId: string, outputDir: string, maxWorkers: number];
  cancel: [];
}>();

const presets = inject<ReturnType<typeof import("../composables/usePresets").usePresets>>("presets")!;

const outputDir = ref("");
const maxWorkers = ref(2);

async function selectOutputDir() {
  const res = await call<string>("select_output_dir");
  if (res.success && res.data) {
    outputDir.value = res.data;
  }
}

function handleStart() {
  emit("start", presets.currentPresetId.value, outputDir.value, maxWorkers.value);
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 border-t border-base-300 px-4 py-2">
    <button
      class="btn btn-primary btn-sm"
      :disabled="!hasFiles || processing"
      @click="handleStart"
    >
      Start Batch
    </button>
    <button
      class="btn btn-error btn-sm"
      :disabled="!processing"
      @click="emit('cancel')"
    >
      Cancel
    </button>

    <div class="flex items-center gap-1 ml-2">
      <span class="text-xs text-base-content/50">Workers:</span>
      <select v-model="maxWorkers" class="select select-bordered select-xs w-16">
        <option :value="1">1</option>
        <option :value="2">2</option>
        <option :value="3">3</option>
        <option :value="4">4</option>
      </select>
    </div>

    <button class="btn btn-ghost btn-sm ml-2" @click="selectOutputDir">
      Output Dir
    </button>
    <span v-if="outputDir" class="badge badge-ghost badge-sm truncate max-w-xs" :title="outputDir">
      {{ outputDir }}
    </span>
    <span v-else class="text-xs text-base-content/40">Output: same as source</span>
  </div>
</template>
