<script setup lang="ts">
/**
 * Page: Custom Command
 *
 * Provides a textarea for raw FFmpeg parameters.
 * Uses the standard command preview pipeline via build_command_preview.
 * Custom command has highest priority and overrides all other settings.
 *
 * v2.2.0: Added ffprobe file analysis with parsed/raw display modes.
 */

import { computed, onMounted, onUnmounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { useGlobalConfig } from "../composables/useGlobalConfig"
import { useCommandPreview } from "../composables/useCommandPreview"
import { useFileProbe } from "../composables/useFileProbe"
import { useFileFormats } from "../composables/useFileFormats"
let copyRawTimer: ReturnType<typeof setTimeout> | null = null
onUnmounted(() => { if (copyRawTimer) clearTimeout(copyRawTimer) })
import {
  formatDuration,
  formatFileSize,
  formatBitRate,
  formatChannels,
} from "../utils/format"
import CommandPreview from "../components/config/CommandPreview.vue"
import FileDropInput from "../components/common/FileDropInput.vue"

const { t } = useI18n()

const { fileFormats } = useFileFormats()
const { customCommand, activeMode, toTaskConfig } = useGlobalConfig()

const configRef = computed(() => toTaskConfig())
const { commandText, errors, warnings, validating } = useCommandPreview(configRef)

const {
  result: probeResult,
  loading: probeLoading,
  error: probeError,
  displayMode: probeDisplayMode,
  hasResult: probeHasResult,
  filePath: probeFilePath,
  probe,
  clear: probeClear,
} = useFileProbe()

const mediaAccept = computed(() => {
  const v = fileFormats.value.video
  const a = fileFormats.value.audio
  return `${v},${a}`.replace(/,\s*,/g, ",")
})

const probeDisplayFile = computed(() => {
  if (!probeFilePath.value) return ""
  return probeFilePath.value.split(/[/\\]/).pop() ?? probeFilePath.value
})

const copiedRaw = ref(false)

// Non-null wrapper for template (guarded by v-if="probeHasResult")
const probeData = computed(() => probeResult.value!)

async function handleProbeFileChanged(path: string) {
  if (path) {
    await probe(path)
  }
}

async function copyRawJson() {
  if (!probeResult.value) return
  try {
    await navigator.clipboard.writeText(probeResult.value.raw)
    copiedRaw.value = true
    if (copyRawTimer) clearTimeout(copyRawTimer)
    copyRawTimer = setTimeout(() => { copiedRaw.value = false }, 2000)
  } catch {
    // clipboard API may not be available in all contexts
  }
}

onMounted(() => {
  activeMode.value = "custom"
})
</script>

<template>
  <div class="page-scroll flex flex-1 flex-col gap-4 p-4 overflow-y-auto">
    <h1 class="text-xl font-bold tracking-tight">{{ t("custom.title") }}</h1>
    <p class="text-sm text-base-content/60">
      {{ t("custom.description") }}
    </p>

    <!-- File Analysis Card -->
    <div class="card bg-base-200 shadow-sm border border-base-300">
      <div class="card-body p-4">
        <div class="flex items-center justify-between mb-1">
          <h2 class="card-title text-sm font-semibold">{{ t("custom.probeTitle") }}</h2>
          <div v-if="probeHasResult" class="join">
            <button
              class="btn btn-xs join-item"
              :class="probeDisplayMode === 'parsed' ? 'btn-primary' : 'btn-ghost'"
              @click="probeDisplayMode = 'parsed'"
            >{{ t("custom.probeParsedMode") }}</button>
            <button
              class="btn btn-xs join-item"
              :class="probeDisplayMode === 'raw' ? 'btn-primary' : 'btn-ghost'"
              @click="probeDisplayMode = 'raw'"
            >{{ t("custom.probeRawMode") }}</button>
          </div>
        </div>

        <p class="text-xs text-base-content/60 mb-3">
          {{ t("custom.probeDescription") }}
        </p>

        <!-- File Input -->
        <FileDropInput
          :model-value="probeDisplayFile"
          :placeholder="t('custom.probeDropHint')"
          :accept="mediaAccept"
          fullscreen-drop
          :multiple="false"
          @update:model-value="handleProbeFileChanged"
        />

        <!-- Clear probe -->
        <div v-if="probeHasResult" class="flex justify-end mt-1">
          <button class="btn btn-xs btn-ghost" @click="probeClear">
            {{ t("common.clear") }}
          </button>
        </div>

        <!-- Loading -->
        <div v-if="probeLoading" class="flex items-center gap-2 text-xs text-base-content/50 mt-2">
          <span class="loading loading-spinner loading-xs"></span>
          {{ t("custom.probeLoading") }}
        </div>

        <!-- Error -->
        <div v-if="probeError" class="alert alert-error py-1 px-3 text-xs mt-2">
          {{ t("custom.probeError", { error: probeError }) }}
        </div>

        <!-- PARSED MODE -->
        <div v-if="probeHasResult && probeDisplayMode === 'parsed'" class="mt-3 space-y-3">
          <!-- General -->
          <div class="collapse collapse-arrow bg-base-300 rounded-lg">
            <input type="checkbox" checked />
            <div class="collapse-title text-xs font-semibold">
              {{ t("custom.probeGeneral") }}
            </div>
            <div class="collapse-content text-xs">
              <div class="grid grid-cols-2 gap-x-4 gap-y-1">
                <span class="text-base-content/50">{{ t("custom.probeFileName") }}</span>
                <span class="truncate" :title="probeData.parsed.general.file_name">{{ probeData.parsed.general.file_name }}</span>
                <span class="text-base-content/50">{{ t("custom.probeFileSize") }}</span>
                <span>{{ formatFileSize(probeData.parsed.general.file_size_bytes) }}</span>
                <span class="text-base-content/50">{{ t("custom.probeDuration") }}</span>
                <span>{{ formatDuration(probeData.parsed.general.duration_seconds) }}</span>
                <span class="text-base-content/50">{{ t("custom.probeFormat") }}</span>
                <span>{{ probeData.parsed.general.format_name }}<span v-if="probeData.parsed.general.format_long_name" class="text-base-content/40"> ({{ probeData.parsed.general.format_long_name }})</span></span>
                <span class="text-base-content/50">{{ t("custom.probeBitRate") }}</span>
                <span>{{ formatBitRate(probeData.parsed.general.bit_rate) }}</span>
                <span class="text-base-content/50">{{ t("custom.probeStreams") }}</span>
                <span>{{ probeData.parsed.general.nb_streams }}</span>
                <span class="text-base-content/50">{{ t("custom.probeProbeScore") }}</span>
                <span>{{ probeData.parsed.general.probe_score }}</span>
              </div>
            </div>
          </div>

          <!-- Video Streams -->
          <div>
            <h3 class="text-xs font-semibold mb-2">{{ t("custom.probeVideo") }}</h3>
            <div v-if="probeData.parsed.video.length > 0" class="space-y-2">
              <div
                v-for="stream in probeData.parsed.video"
                :key="stream.index"
                class="collapse collapse-arrow bg-base-300 rounded-lg"
              >
                <input type="checkbox" :checked="stream.index === probeData.parsed.video[0].index" />
                <div class="collapse-title text-xs font-medium">
                  {{ t("custom.probeStreamIndex", { index: stream.index }) }} - {{ stream.codec_name }}
                </div>
                <div class="collapse-content text-xs">
                  <div class="grid grid-cols-2 gap-x-4 gap-y-1">
                    <span class="text-base-content/50">{{ t("custom.probeCodec") }}</span>
                    <span>{{ stream.codec_long_name || stream.codec_name }}</span>
                    <span class="text-base-content/50">{{ t("custom.probeResolution") }}</span>
                    <span>{{ stream.resolution }}</span>
                    <span class="text-base-content/50">{{ t("custom.probeFps") }}</span>
                    <span>{{ stream.fps }}</span>
                    <span class="text-base-content/50">{{ t("custom.probeBitRate") }}</span>
                    <span>{{ formatBitRate(stream.bit_rate) }}</span>
                    <span class="text-base-content/50">{{ t("custom.probePixelFormat") }}</span>
                    <span>{{ stream.pix_fmt }}</span>
                    <span class="text-base-content/50">{{ t("custom.probeColorSpace") }}</span>
                    <span>{{ stream.color_space || "-" }}</span>
                    <span class="text-base-content/50">{{ t("custom.probeColorRange") }}</span>
                    <span>{{ stream.color_range || "-" }}</span>
                    <span v-if="stream.profile" class="text-base-content/50">{{ t("custom.probeProfile") }}</span>
                    <span v-if="stream.profile">{{ stream.profile }}</span>
                    <span v-if="stream.level >= 0" class="text-base-content/50">{{ t("custom.probeLevel") }}</span>
                    <span v-if="stream.level >= 0">{{ stream.level }}</span>
                    <span v-if="stream.sample_aspect_ratio && stream.sample_aspect_ratio !== 'N/A'" class="text-base-content/50">{{ t("custom.probeSar") }}</span>
                    <span v-if="stream.sample_aspect_ratio && stream.sample_aspect_ratio !== 'N/A'">{{ stream.sample_aspect_ratio }}</span>
                    <span v-if="stream.display_aspect_ratio && stream.display_aspect_ratio !== 'N/A'" class="text-base-content/50">{{ t("custom.probeDar") }}</span>
                    <span v-if="stream.display_aspect_ratio && stream.display_aspect_ratio !== 'N/A'">{{ stream.display_aspect_ratio }}</span>
                    <span v-if="stream.field_order && stream.field_order !== 'progressive'" class="text-base-content/50">{{ t("custom.probeFieldOrder") }}</span>
                    <span v-if="stream.field_order && stream.field_order !== 'progressive'">{{ stream.field_order }}</span>
                    <span v-if="stream.language" class="text-base-content/50">{{ t("custom.probeLanguage") }}</span>
                    <span v-if="stream.language">{{ stream.language }}</span>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="text-xs text-base-content/40">
              {{ t("custom.probeNoStream", { type: "video" }) }}
            </p>
          </div>

          <!-- Audio Streams -->
          <div>
            <h3 class="text-xs font-semibold mb-2">{{ t("custom.probeAudio") }}</h3>
            <div v-if="probeData.parsed.audio.length > 0" class="space-y-2">
              <div
                v-for="stream in probeData.parsed.audio"
                :key="stream.index"
                class="collapse collapse-arrow bg-base-300 rounded-lg"
              >
                <input type="checkbox" :checked="stream.index === probeData.parsed.audio[0].index" />
                <div class="collapse-title text-xs font-medium">
                  {{ t("custom.probeStreamIndex", { index: stream.index }) }} - {{ stream.codec_name }}
                </div>
                <div class="collapse-content text-xs">
                  <div class="grid grid-cols-2 gap-x-4 gap-y-1">
                    <span class="text-base-content/50">{{ t("custom.probeCodec") }}</span>
                    <span>{{ stream.codec_long_name || stream.codec_name }}</span>
                    <span class="text-base-content/50">{{ t("custom.probeSampleRate") }}</span>
                    <span>{{ stream.sample_rate ? `${stream.sample_rate} Hz` : "-" }}</span>
                    <span class="text-base-content/50">{{ t("custom.probeChannels") }}</span>
                    <span>{{ formatChannels(stream.channels) || stream.channel_layout || "-" }}</span>
                    <span class="text-base-content/50">{{ t("custom.probeBitRate") }}</span>
                    <span>{{ formatBitRate(stream.bit_rate) }}</span>
                    <span v-if="stream.language" class="text-base-content/50">{{ t("custom.probeLanguage") }}</span>
                    <span v-if="stream.language">{{ stream.language }}</span>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="text-xs text-base-content/40">
              {{ t("custom.probeNoStream", { type: "audio" }) }}
            </p>
          </div>

          <!-- Subtitle Streams -->
          <div>
            <h3 class="text-xs font-semibold mb-2">{{ t("custom.probeSubtitle") }}</h3>
            <div v-if="probeData.parsed.subtitle.length > 0" class="space-y-2">
              <div
                v-for="stream in probeData.parsed.subtitle"
                :key="stream.index"
                class="collapse collapse-arrow bg-base-300 rounded-lg"
              >
                <input type="checkbox" />
                <div class="collapse-title text-xs font-medium">
                  {{ t("custom.probeStreamIndex", { index: stream.index }) }} - {{ stream.codec_name }}
                </div>
                <div class="collapse-content text-xs">
                  <div class="grid grid-cols-2 gap-x-4 gap-y-1">
                    <span class="text-base-content/50">{{ t("custom.probeCodec") }}</span>
                    <span>{{ stream.codec_name }}</span>
                    <span v-if="stream.language" class="text-base-content/50">{{ t("custom.probeLanguage") }}</span>
                    <span v-if="stream.language">{{ stream.language }}</span>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="text-xs text-base-content/40">
              {{ t("custom.probeNoStream", { type: "subtitle" }) }}
            </p>
          </div>
        </div>

        <!-- RAW MODE -->
        <div v-if="probeHasResult && probeDisplayMode === 'raw'" class="mt-3">
          <div class="flex justify-end mb-1">
            <button
              class="btn btn-xs btn-ghost"
              :class="copiedRaw ? 'btn-success' : ''"
              @click="copyRawJson"
            >{{ t("custom.probeCopyRaw") }}</button>
          </div>
          <pre class="bg-base-300 rounded-lg p-3 text-xs font-mono overflow-auto max-h-96 whitespace-pre-wrap break-all">{{ probeData.raw }}</pre>
        </div>
      </div>
    </div>

    <div class="alert alert-warning text-xs py-2">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11.13 22H9c-.55 0-1-.45-1-1v-2c0-.55.45-1 1-1h2c.55 0 1 .45 1 1v2c0 .55-.45 1-1 1zm.92-6H6.95a.75.75 0 0 1 0-1.5h5.1a.75.75 0 0 1 0 1.5z" clip-rule="evenodd" />
      </svg>
      <span>{{ t("custom.warning") }}</span>
    </div>

    <!-- Command Preview -->
    <CommandPreview
      :command-text="commandText"
      :errors="errors"
      :warnings="warnings"
      :validating="validating"
    />

    <!-- Raw Args Textarea -->
    <div class="card bg-base-200 shadow-sm border border-base-300">
      <div class="card-body p-4">
        <h2 class="card-title text-sm font-semibold mb-3">{{ t("custom.ffmpegParameters") }}</h2>
        <textarea
          v-model="customCommand.raw_args"
          class="textarea textarea-bordered textarea-sm w-full font-mono"
          rows="8"
          placeholder="e.g. -vf crop=1920:800:0:280 -c:v libx265 -preset medium"
        ></textarea>
        <p class="text-xs text-base-content/50 mt-2">
          {{ t("custom.hint") }}
        </p>
      </div>
    </div>

  </div>
</template>
