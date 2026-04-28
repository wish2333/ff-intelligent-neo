<script setup lang="ts">
/**
 * Page: Command Configuration
 *
 * Global settings page for FFmpeg transcoding parameters.
 * Changes here are shared with the Task Queue page automatically.
 * Uses tab-based layout for Transcode, Filters, and Clip modes.
 *
 * Phase 3.5: Preview moved to top, only 3 tabs remain.
 * Phase 3.5.1: Exclusive tab display (only one visible at a time).
 */

import { ref, computed, onMounted } from "vue"
import { useI18n } from "vue-i18n"
import { call } from "../bridge"
import { useGlobalConfig } from "../composables/useGlobalConfig"
import { useCommandPreview } from "../composables/useCommandPreview"
import { useSettings } from "../composables/useSettings"
import type { PresetDTO } from "../types/preset"
import type { ActiveMode } from "../types/config"

import TranscodeForm from "../components/config/TranscodeForm.vue"
import FilterForm from "../components/config/FilterForm.vue"
import ClipForm from "../components/config/ClipForm.vue"
import MergeSettingsForm from "../components/config/MergeSettingsForm.vue"
import CommandPreview from "../components/config/CommandPreview.vue"
import PresetSelector from "../components/config/PresetSelector.vue"
import PresetEditor from "../components/config/PresetEditor.vue"

const { t } = useI18n()

const {
  transcode, filters, clip, merge,
  activeMode, supportedEncoders,
  toTaskConfig, loadFromTaskConfig, resetAll,
} = useGlobalConfig()

const { appInfo, fetchAppInfo } = useSettings()

const configRef = computed(() => toTaskConfig())
const { commandText, errors, warnings, validating } = useCommandPreview(configRef)

const presetSelectorRef = ref<InstanceType<typeof PresetSelector> | null>(null)
const showPresetEditor = ref(false)

const TABS = computed<{ key: ActiveMode; label: string }[]>(() => [
  { key: "transcode", label: t("config.tabs.transcode") },
  { key: "filters", label: t("config.tabs.filters") },
  { key: "clip", label: t("config.tabs.clip") },
  { key: "merge", label: t("config.tabs.merge") },
])

function handleTabClick(key: ActiveMode) {
  activeMode.value = key
}

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

// Hardware encoder detection on mount
onMounted(async () => {
  activeMode.value = "transcode"
  await fetchAppInfo()
  try {
    const res = await call<string[]>("check_hw_encoders")
    if (res.success && res.data) {
      const arr = Array.isArray(res.data) ? res.data : []
      supportedEncoders.value = arr
    }
  } catch {
    // silently fail -- all encoders will be shown as available
  }
})
</script>

<template>
  <div class="page-scroll flex flex-1 flex-col gap-4 p-4 overflow-y-auto">
    <!-- Command Preview at TOP -->
    <CommandPreview
      :command-text="commandText"
      :errors="errors"
      :warnings="warnings"
      :validating="validating"
    />

    <!-- Preset Selector -->
    <PresetSelector
      ref="presetSelectorRef"
      @select="handlePresetSelect"
      @save="handlePresetSave"
    />

    <!-- Tab Bar -->
    <div role="tablist" class="tabs tabs-bordered">
      <a
        v-for="tab in TABS"
        :key="tab.key"
        class="tab text-sm font-medium"
        :class="{ 'tab-active': activeMode === tab.key }"
        role="tab"
        @click="handleTabClick(tab.key)"
      >
        {{ tab.label }}
      </a>
    </div>

    <!-- Tab Content: Only show active tab -->
    <TranscodeForm
      v-if="activeMode === 'transcode'"
      :config="transcode"
      :platform="appInfo?.platform ?? ''"
    />
    <FilterForm
      v-if="activeMode === 'filters'"
      :config="filters"
    />
    <ClipForm
      v-if="activeMode === 'clip'"
      :config="clip"
    />
    <MergeSettingsForm
      v-if="activeMode === 'merge'"
      :config="merge"
    />

    <!-- Reset -->
    <div class="flex justify-end">
      <button class="btn btn-ghost btn-sm" @click="handleReset">
        {{ t("config.resetAll") }}
      </button>
    </div>

    <!-- Preset Editor Modal -->
    <PresetEditor
      :open="showPresetEditor"
      @save="handlePresetEditorSave"
      @close="showPresetEditor = false"
    />
  </div>
</template>
