<script setup lang="ts">
/**
 * Audio/Subtitle mixing configuration form.
 *
 * Supports external audio replacement and subtitle embedding.
 * Phase 3.5.1: Half-screen layout with fullscreen drag-drop.
 */

import { useI18n } from "vue-i18n"
import type { AudioSubtitleConfigDTO } from "../../types/config"
import FileDropInput from "../common/FileDropInput.vue"

const { t } = useI18n()

defineProps<{
  config: AudioSubtitleConfigDTO
}>()
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- Audio Section -->
    <div class="card bg-base-200 shadow-sm border border-base-300">
      <div class="card-body p-4">
        <h2 class="card-title text-sm font-semibold mb-3">{{ t("avMix.audio.title") }}</h2>
        <p class="text-xs text-base-content/60 mb-3">
          {{ t("avMix.audio.description") }}
        </p>

        <!-- External Audio Path -->
        <div class="form-control mb-3">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("avMix.audio.externalAudio") }}</span>
          </label>
          <FileDropInput
            :model-value="config.external_audio_path"
            accept=".mp3,.aac,.flac,.wav,.m4a,.ogg,.wma"
            :placeholder="t('avMix.audio.dropHint')"
            fullscreen-drop
            @update:model-value="config.external_audio_path = $event"
          />
        </div>

        <!-- Replace Audio Toggle -->
        <div v-if="config.external_audio_path" class="form-control">
          <label class="label cursor-pointer justify-start gap-2 py-1">
            <input
              v-model="config.replace_audio"
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

    <!-- Subtitle Section -->
    <div class="card bg-base-200 shadow-sm border border-base-300">
      <div class="card-body p-4">
        <h2 class="card-title text-sm font-semibold mb-3">{{ t("avMix.subtitle.title") }}</h2>
        <p class="text-xs text-base-content/60 mb-3">
          {{ t("avMix.subtitle.description") }}
        </p>

        <!-- Subtitle Path -->
        <div class="form-control mb-3">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("avMix.subtitle.subtitleFile") }}</span>
          </label>
          <FileDropInput
            :model-value="config.subtitle_path"
            accept=".srt,.ass,.ssa"
            :placeholder="t('avMix.subtitle.dropHint')"
            fullscreen-drop
            @update:model-value="config.subtitle_path = $event"
          />
        </div>

        <!-- Subtitle Language -->
        <div v-if="config.subtitle_path" class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("avMix.subtitle.languageCode") }}</span>
          </label>
          <input
            v-model="config.subtitle_language"
            type="text"
            :placeholder="t('avMix.subtitle.languagePlaceholder')"
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
  </div>
</template>
