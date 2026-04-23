<script setup lang="ts">
/**
 * Page 2: Command Configuration
 *
 * Global settings page for FFmpeg transcoding parameters.
 * Changes here are shared with the Task Queue page automatically.
 * No "Add to Queue" button -- the task queue reads these settings when adding files.
 */

import { ref, computed } from "vue"
import { call } from "../bridge"
import { useGlobalConfig } from "../composables/useGlobalConfig"
import { useCommandPreview } from "../composables/useCommandPreview"
import type { PresetDTO } from "../types/preset"

import TranscodeForm from "../components/config/TranscodeForm.vue"
import FilterForm from "../components/config/FilterForm.vue"
import CommandPreview from "../components/config/CommandPreview.vue"
import PresetSelector from "../components/config/PresetSelector.vue"
import PresetEditor from "../components/config/PresetEditor.vue"

const { transcode, filters, toTaskConfig, loadFromTaskConfig, resetAll } =
  useGlobalConfig()
const configRef = computed(() => toTaskConfig())
const { commandText, errors, warnings, validating } = useCommandPreview(configRef)

const presetSelectorRef = ref<InstanceType<typeof PresetSelector> | null>(null)
const showPresetEditor = ref(false)

function handlePresetSelect(preset: PresetDTO) {
  loadFromTaskConfig(preset.config)
}

function handlePresetSave() {
  showPresetEditor.value = true
}

async function handlePresetEditorSave(data: { name: string; description: string }) {
  const config = toTaskConfig()
  await call("save_preset", {
    name: data.name,
    description: data.description,
    config,
  })
  showPresetEditor.value = false
  if (presetSelectorRef.value) {
    await presetSelectorRef.value.fetchPresets()
  }
}

function handleReset() {
  resetAll()
  if (presetSelectorRef.value) {
    presetSelectorRef.value.setSelectedId("")
  }
}
</script>

<template>
  <div class="flex flex-1 flex-col gap-4 p-4 overflow-y-auto">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-bold">FFmpeg Command Configuration</h1>
      <button class="btn btn-ghost btn-sm" @click="handleReset">
        Reset All
      </button>
    </div>

    <p class="text-xs text-base-content/60">
      Settings on this page apply when adding files from the Task Queue.
    </p>

    <!-- Preset Selector -->
    <PresetSelector
      ref="presetSelectorRef"
      @select="handlePresetSelect"
      @save="handlePresetSave"
    />

    <!-- Two-column: Transcode + Filters -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <TranscodeForm :config="transcode" />
      <FilterForm :config="filters" />
    </div>

    <!-- Command Preview -->
    <CommandPreview
      :command-text="commandText"
      :errors="errors"
      :warnings="warnings"
      :validating="validating"
    />

    <!-- Preset Editor Modal -->
    <PresetEditor
      :open="showPresetEditor"
      @save="handlePresetEditorSave"
      @close="showPresetEditor = false"
    />
  </div>
</template>
