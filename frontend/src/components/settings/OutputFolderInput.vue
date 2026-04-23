<script setup lang="ts">
/**
 * Default output folder setting.
 */
import { call } from "../../bridge"

defineProps<{
  value: string
}>()

const emit = defineEmits<{
  change: [value: string]
}>()

function handleRadioChange(event: Event): void {
  const target = event.target as HTMLInputElement
  if (target.value === "same") {
    emit("change", "")
  }
}

async function handleBrowse(): Promise<void> {
  const res = await call<string>("select_output_dir")
  if (res.success && res.data) {
    emit("change", res.data)
  }
}

function handleInputChange(event: Event): void {
  const target = event.target as HTMLInputElement
  emit("change", target.value)
}
</script>

<template>
  <div class="space-y-3">
    <h3 class="text-lg font-semibold">Output</h3>

    <div class="space-y-2">
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="radio"
          name="output-mode"
          value="same"
          :checked="!value"
          class="radio radio-sm radio-primary"
          @change="handleRadioChange"
        />
        <span class="text-sm">Same as source directory</span>
      </label>

      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="radio"
          name="output-mode"
          value="custom"
          :checked="!!value"
          class="radio radio-sm radio-primary"
          @change="() => {}"
        />
        <span class="text-sm">Custom folder:</span>
      </label>

      <div v-if="!!value" class="flex items-center gap-2 ml-6">
        <input
          type="text"
          :value="value"
          class="input input-bordered input-sm flex-1"
          placeholder="Select a folder..."
          @change="handleInputChange"
        />
        <button class="btn btn-xs btn-outline" @click="handleBrowse">
          Browse...
        </button>
      </div>

      <div v-else class="ml-6">
        <button class="btn btn-xs btn-outline" @click="handleBrowse">
          Select folder...
        </button>
      </div>
    </div>
  </div>
</template>
