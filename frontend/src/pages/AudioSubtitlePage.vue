<script setup lang="ts">
/**
 * Page: Audio / Subtitle Mixing
 *
 * Independent page for external audio and subtitle mixing.
 * Inherits global transcode settings but does not show transcode UI.
 * Has its own command preview.
 * Phase 3.5.2: Split-screen drag-drop for audio/subtitle.
 */

import { computed, onMounted } from "vue"
import { useI18n } from "vue-i18n"
import { call } from "../bridge"
import { useGlobalConfig } from "../composables/useGlobalConfig"
import { useCommandPreview } from "../composables/useCommandPreview"
import SplitDropZone from "../components/common/SplitDropZone.vue"
import CommandPreview from "../components/config/CommandPreview.vue"
import { useFileFormats } from "../composables/useFileFormats"

const { fileFormats } = useFileFormats()

const { t } = useI18n()

const { avsmix, activeMode, toTaskConfig } = useGlobalConfig()

const configRef = computed(() => toTaskConfig())
const { commandText, errors, warnings, validating } = useCommandPreview(configRef)

function handleDropAudio(path: string) {
  avsmix.external_audio_path = path
}

function handleDropSubtitle(path: string) {
  avsmix.subtitle_path = path
}

async function handleClickAudio() {
  const res = await call<string[]>("select_files")
  if (res.success && res.data && res.data.length > 0) {
    avsmix.external_audio_path = res.data[0]
  }
}

async function handleClickSubtitle() {
  const res = await call<string[]>("select_files")
  if (res.success && res.data && res.data.length > 0) {
    avsmix.subtitle_path = res.data[0]
  }
}

onMounted(() => {
  activeMode.value = "avsmix"
})
</script>

<template>
  <div class="page-scroll flex flex-1 flex-col gap-4 p-4 overflow-y-auto">
    <h1 class="text-xl font-bold tracking-tight">{{ t("avMix.title") }}</h1>
    <p class="text-sm text-base-content/60">
      {{ t("avMix.description") }}
      {{ t("avMix.dragHint") }}
    </p>

    <CommandPreview
      :command-text="commandText"
      :errors="errors"
      :warnings="warnings"
      :validating="validating"
    />

    <SplitDropZone
      :left-label="t('avMix.audio.title')"
      :right-label="t('avMix.subtitle.title')"
      :left-accept="fileFormats.audio"
      :right-accept="fileFormats.subtitle"
      @drop-left="handleDropAudio"
      @drop-right="handleDropSubtitle"
    >
      <template #left>
        <div class="card bg-base-200 shadow-sm border border-base-300">
          <div class="card-body p-4">
            <h2 class="card-title text-sm font-semibold mb-3">{{ t("avMix.audio.title") }}</h2>
            <p class="text-xs text-base-content/60 mb-3">
              {{ t("avMix.audio.description") }}
            </p>
            <div class="form-control">
              <label class="label py-1">
                <span class="label-text text-xs">{{ t("avMix.audio.externalAudio") }}</span>
              </label>
              <div
                class="rounded-lg border border-dashed px-3 py-6 text-center text-sm cursor-pointer border-base-300 hover:border-primary/50 hover:bg-base-200/50 transition-colors"
                @click="handleClickAudio"
              >
                <span v-if="avsmix.external_audio_path" class="truncate block" :title="avsmix.external_audio_path">
                  {{ avsmix.external_audio_path.split(/[/\\]/).pop() }}
                </span>
                <span v-else class="opacity-40">
                  {{ t("avMix.audio.clickOrDrag") }}
                </span>
              </div>
              <div v-if="avsmix.external_audio_path" class="flex justify-end mt-1">
                <button class="btn btn-xs btn-ghost text-error" @click.stop="avsmix.external_audio_path = ''">{{ t("common.clear") }}</button>
              </div>
            </div>
            <!-- Replace Audio Toggle -->
            <div v-if="avsmix.external_audio_path" class="form-control mt-2">
              <label class="label cursor-pointer justify-start gap-2 py-1">
                <input
                  v-model="avsmix.replace_audio"
                  type="checkbox"
                  class="checkbox checkbox-sm checkbox-primary"
                />
                <div>
                  <span class="label-text text-xs">{{ t("avMix.audio.replaceOriginal") }}</span>
                  <p class="text-xs text-base-content/50 mt-0.5">{{ t("avMix.audio.replaceHint") }}</p>
                </div>
              </label>
            </div>
          </div>
        </div>
      </template>
      <template #right>
        <div class="card bg-base-200 shadow-sm border border-base-300">
          <div class="card-body p-4">
            <h2 class="card-title text-sm font-semibold mb-3">{{ t("avMix.subtitle.title") }}</h2>
            <p class="text-xs text-base-content/60 mb-3">
              {{ t("avMix.subtitle.description") }}
            </p>
            <div class="form-control">
              <label class="label py-1">
                <span class="label-text text-xs">{{ t("avMix.subtitle.subtitleFile") }}</span>
              </label>
              <div
                class="rounded-lg border border-dashed px-3 py-6 text-center text-sm cursor-pointer border-base-300 hover:border-primary/50 hover:bg-base-200/50 transition-colors"
                @click="handleClickSubtitle"
              >
                <span v-if="avsmix.subtitle_path" class="truncate block" :title="avsmix.subtitle_path">
                  {{ avsmix.subtitle_path.split(/[/\\]/).pop() }}
                </span>
                <span v-else class="opacity-40">
                  {{ t("avMix.subtitle.clickOrDrag") }}
                </span>
              </div>
              <div v-if="avsmix.subtitle_path" class="flex justify-end mt-1">
                <button class="btn btn-xs btn-ghost text-error" @click.stop="avsmix.subtitle_path = ''">{{ t("common.clear") }}</button>
              </div>
            </div>
            <!-- Subtitle Language -->
            <div v-if="avsmix.subtitle_path" class="form-control mt-2">
              <label class="label py-1">
                <span class="label-text text-xs">{{ t("avMix.subtitle.languageCode") }}</span>
              </label>
              <input
                v-model="avsmix.subtitle_language"
                type="text"
                placeholder="e.g. eng, chi, jpn"
                class="input input-bordered input-sm w-full"
              />
              <label class="label py-0.5">
                <span class="label-text-alt text-xs text-base-content/50">
                  {{ t("avMix.subtitle.languageHint") }}
                </span>
              </label>
            </div>
          </div>
        </div>
      </template>
    </SplitDropZone>
  </div>
</template>
