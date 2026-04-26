<script setup lang="ts">
/**
 * Page: Auto Cut
 *
 * Automatic silence/motion detection and cutting using auto-editor.
 * Uses useAutoEditor composable for all state management.
 *
 * v2.2.0 Phase 2: Initial page shell.
 * v2.2.0 Phase 3: Extract BasicTab as independent component.
 */

import { ref, computed, onMounted, onUnmounted } from "vue"
import { useI18n } from "vue-i18n"
import { useRouter } from "vue-router"
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
  speedValue,
  volumeValue,
  advancedOptions,
  encoderLists,
  selectedFile,
  autoEditorStatus,
  commandPreview,
  validating,
  alertMessage,
  alertType,
  init,
  dispose,
  addToQueue,
  fetchEncoders,
} = useAutoEditor()

const activeTab = ref("basic")

const isReady = computed(
  () => autoEditorStatus.value.available && autoEditorStatus.value.compatible,
)

const statusMessage = computed(() => {
  if (!autoEditorStatus.value.path) {
    return t("autoCut.notConfigured")
  }
  if (!autoEditorStatus.value.compatible) {
    return t("autoCut.versionIncompatible", {
      version: autoEditorStatus.value.version,
    })
  }
  return ""
})

function handleTabClick(tab: string) {
  activeTab.value = tab
}

async function handleAddToQueue() {
  const success = await addToQueue()
  if (success) {
    router.push("/task-queue")
  }
}

onMounted(() => {
  init()
})

onUnmounted(() => {
  dispose()
})
</script>

<template>
  <div class="flex flex-col gap-4 p-4 min-h-0">
    <!-- Page header -->
    <div>
      <h1 class="text-xl font-bold tracking-tight">{{ t("autoCut.title") }}</h1>
      <p class="text-sm text-base-content/60">{{ t("autoCut.description") }}</p>
    </div>

    <!-- Status bar -->
    <div
      v-if="statusMessage"
      class="alert alert-warning py-2 px-4 text-sm"
    >
      {{ statusMessage }}
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
      :model-value="selectedFile ?? ''"
      :placeholder="t('common.dropDefault')"
      accept=".mp4,.mov,.mkv,.m4v,.mp3,.wav,.m4a,.aac"
      @update:model-value="selectedFile = $event || null"
    />

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
      :speed-value="speedValue"
      :volume-value="volumeValue"
      @update:edit-method="editMethod = $event"
      @update:audio-threshold="audioThreshold = $event"
      @update:motion-threshold="motionThreshold = $event"
      @update:when-silent-action="whenSilentAction = $event"
      @update:when-normal-action="whenNormalAction = $event"
      @update:margin="margin = $event"
      @update:smooth="smooth = $event"
      @update:speed-value="speedValue = $event"
      @update:volume-value="volumeValue = $event"
    />

    <!-- Advanced tab -->
    <AdvancedTab
      v-show="activeTab === 'advanced'"
      :advanced-options="advancedOptions"
      :encoder-lists="encoderLists"
      @update:advanced-options="advancedOptions = $event"
      @fetch-encoders="fetchEncoders($event)"
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
      :disabled="!isReady || !selectedFile"
      @click="handleAddToQueue"
    >
      {{ t("autoCut.addToQueue") }}
    </button>
  </div>
</template>
