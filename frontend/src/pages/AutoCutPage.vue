<script setup lang="ts">
/**
 * Page: Auto Cut
 *
 * Automatic silence/motion detection and cutting using auto-editor.
 * Supports multiple file input - one task per file added to queue.
 * Uses useAutoEditor composable for all state management.
 *
 * v2.2.0 Phase 2: Initial page shell.
 * v2.2.0 Phase 3: Extract BasicTab as independent component.
 */

import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import { useI18n } from "vue-i18n"
import { useRouter } from "vue-router"
import { waitForPyWebView } from "../bridge"
import { useAutoEditor } from "../composables/useAutoEditor"
import CommandPreview from "../components/config/CommandPreview.vue"
import FileDropInput from "../components/common/FileDropInput.vue"
import BasicTab from "../components/auto-cut/BasicTab.vue"
import AdvancedTab from "../components/auto-cut/AdvancedTab.vue"

const { t } = useI18n()
const router = useRouter()

const {
  editMethod,
  audioThreshold,
  motionThreshold,
  whenSilentAction,
  whenNormalAction,
  margin,
  smooth,
  silentSpeedValue,
  silentVolumeValue,
  normalSpeedValue,
  normalVolumeValue,
  advancedOptions,


  autoEditorStatus,
  commandPreview,
  validating,
  alertMessage,
  alertType,
  selectedFile,
  init,
  dispose,
  addToQueue,
} = useAutoEditor()

const activeTab = ref("basic")
const selectedFiles = ref<string[]>([])
const displayFile = computed(() => {
  if (selectedFiles.value.length === 0) return ""
  if (selectedFiles.value.length === 1) return selectedFiles.value[0]
  return t("autoCut.multipleFiles", { count: selectedFiles.value.length })
})

const isReady = computed(
  () => autoEditorStatus.value.available && autoEditorStatus.value.compatible,
)

function handleTabClick(tab: string) {
  activeTab.value = tab
}

function handleFilesChanged(path: string) {
  if (path) {
    selectedFiles.value = [...selectedFiles.value, path]
  }
}

function handleClearFiles() {
  selectedFiles.value = []
}

watch(selectedFiles, (files) => {
  selectedFile.value = files.length > 0 ? files[0] : null
})

async function handleAddToQueue() {
  if (selectedFiles.value.length === 0) return
  let allSuccess = true
  for (const file of selectedFiles.value) {
    const success = await addToQueue(file)
    if (!success) allSuccess = false
  }
  if (allSuccess) {
    router.push("/task-queue")
  }
}

onMounted(async () => {
  try {
    await waitForPyWebView()
  } catch {
    // pywebview may already be ready if navigated from another page
  }
  init()
})

onUnmounted(() => {
  dispose()
})
</script>

<template>
  <div class="flex flex-col gap-4 p-4 min-h-0 overflow-y-auto">
    <!-- Page header -->
    <div>
      <h1 class="text-xl font-bold tracking-tight">{{ t("autoCut.title") }}</h1>
      <p class="text-sm text-base-content/60">{{ t("autoCut.description") }}</p>
    </div>

    <!-- Alert message -->
    <div
      v-if="alertMessage"
      class="text-sm"
      :class="alertType === 'error' ? 'text-error' : 'text-success'"
    >
      {{ t(`autoCut.${alertMessage}`) }}
    </div>

    <!-- File input -->
    <FileDropInput
      :model-value="displayFile"
      :placeholder="t('common.dropDefault')"
      accept=".mp4,.mov,.mkv,.m4v,.mp3,.wav,.m4a,.aac"
      fullscreen-drop
      @update:model-value="handleFilesChanged"
    />

    <!-- Clear files button -->
    <div v-if="selectedFiles.length > 0" class="flex justify-end">
      <button class="btn btn-xs btn-ghost" @click="handleClearFiles">
        {{ t("common.clear") }}
      </button>
    </div>

    <!-- Tab container -->
    <div role="tablist" class="tabs tabs-bordered">
      <a
        role="tab"
        class="tab"
        :class="{ 'tab-active': activeTab === 'basic' }"
        @click="handleTabClick('basic')"
      >{{ t("autoCut.basicTab") }}</a>
      <a
        role="tab"
        class="tab"
        :class="{ 'tab-active': activeTab === 'advanced' }"
        @click="handleTabClick('advanced')"
      >{{ t("autoCut.advancedTab") }}</a>
    </div>

    <!-- Basic tab -->
    <BasicTab
      v-show="activeTab === 'basic'"
      :edit-method="editMethod"
      :audio-threshold="audioThreshold"
      :motion-threshold="motionThreshold"
      :when-silent-action="whenSilentAction"
      :when-normal-action="whenNormalAction"
      :margin="margin"
      :smooth="smooth"
      :silent-speed-value="silentSpeedValue"
      :silent-volume-value="silentVolumeValue"
      :normal-speed-value="normalSpeedValue"
      :normal-volume-value="normalVolumeValue"
      :video-codec="advancedOptions.videoCodec"
      :audio-codec="advancedOptions.audioCodec"
      @update:edit-method="editMethod = $event"
      @update:audio-threshold="audioThreshold = $event"
      @update:motion-threshold="motionThreshold = $event"
      @update:when-silent-action="whenSilentAction = $event"
      @update:when-normal-action="whenNormalAction = $event"
      @update:margin="margin = $event"
      @update:smooth="smooth = $event"
      @update:silent-speed-value="silentSpeedValue = $event"
      @update:silent-volume-value="silentVolumeValue = $event"
      @update:normal-speed-value="normalSpeedValue = $event"
      @update:normal-volume-value="normalVolumeValue = $event"
      @update:video-codec="advancedOptions = { ...advancedOptions, videoCodec: $event }"
      @update:audio-codec="advancedOptions = { ...advancedOptions, audioCodec: $event }"
    />

    <!-- Advanced tab -->
    <AdvancedTab
      v-show="activeTab === 'advanced'"
      :advanced-options="advancedOptions"
      @update:advanced-options="advancedOptions = $event"
    />

    <!-- Command preview -->
    <CommandPreview
      :command-text="commandPreview"
      :errors="[]"
      :warnings="[]"
      :validating="validating"
      type="auto-editor"
    />

    <!-- Add to queue -->
    <button
      class="btn btn-primary w-full"
      :disabled="!isReady || selectedFiles.length === 0"
      @click="handleAddToQueue"
    >
      {{ t("autoCut.addToQueue") }}
    </button>
  </div>
</template>
