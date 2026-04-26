<script setup lang="ts">
/**
 * Page: Auto Cut
 *
 * Automatic silence/motion detection and cutting using auto-editor.
 * Uses useAutoEditor composable for all state management.
 *
 * v2.2.0 Phase 2: Initial page shell with status bar, file input,
 * tab container, command preview, and add-to-queue button.
 */

import { computed, onMounted, onUnmounted } from "vue"
import { useI18n } from "vue-i18n"
import { useRouter } from "vue-router"
import { useAutoEditor } from "../composables/useAutoEditor"
import CommandPreview from "../components/config/CommandPreview.vue"
import FileDropInput from "../components/common/FileDropInput.vue"

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
  selectedFile,
  autoEditorStatus,
  commandPreview,
  validating,
  alertMessage,
  alertType,
  init,
  dispose,
  addToQueue,
} = useAutoEditor()

const currentThreshold = computed({
  get: () => editMethod.value === "audio" ? audioThreshold.value : motionThreshold.value,
  set: (v: number) => {
    if (editMethod.value === "audio") {
      audioThreshold.value = v
    } else {
      motionThreshold.value = v
    }
  },
})

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

const activeTab = computed(() => "basic")

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

    <!-- Tab container placeholder -->
    <div class="tabs tabs-bordered">
      <a class="tab tab-active" data-tab="basic">{{ t("autoCut.basicTab") }}</a>
      <a class="tab" data-tab="advanced">{{ t("autoCut.advancedTab") }}</a>
    </div>

    <!-- Basic tab content placeholder -->
    <div v-if="activeTab === 'basic'" class="card bg-base-200 shadow-sm border border-base-300">
      <div class="card-body">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Edit method -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t("autoCut.editMethod") }}</span>
            </label>
            <select
              v-model="editMethod"
              class="select select-bordered select-sm w-full"
            >
              <option value="audio">{{ t("autoCut.audio") }}</option>
              <option value="motion">{{ t("autoCut.motion") }}</option>
            </select>
          </div>

          <!-- Threshold -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t("autoCut.threshold") }}</span>
              <span class="label-text-alt">{{ currentThreshold }}</span>
            </label>
            <input
              v-model.number="currentThreshold"
              type="range"
              min="0.01"
              max="0.20"
              step="0.01"
              class="range range-sm range-primary"
            />
          </div>

          <!-- When silent -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t("autoCut.whenSilent") }}</span>
            </label>
            <select
              v-model="whenSilentAction"
              class="select select-bordered select-sm w-full"
            >
              <option value="cut">cut</option>
              <option value="nil">nil</option>
            </select>
          </div>

          <!-- When normal -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t("autoCut.whenNormal") }}</span>
            </label>
            <select
              v-model="whenNormalAction"
              class="select select-bordered select-sm w-full"
            >
              <option value="nil">nil</option>
              <option value="cut">cut</option>
            </select>
          </div>

          <!-- Margin -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t("autoCut.margin") }}</span>
            </label>
            <input
              v-model="margin"
              type="text"
              class="input input-bordered input-sm w-full"
              placeholder="0.2s"
            />
          </div>

          <!-- Smooth -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">
                {{ t("autoCut.smoothMincut") }} / {{ t("autoCut.smoothMinclip") }}
              </span>
            </label>
            <input
              v-model="smooth"
              type="text"
              class="input input-bordered input-sm w-full"
              placeholder="0.2s,0.1s"
            />
          </div>
        </div>
      </div>
    </div>

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
