<script setup lang="ts">
/**
 * Transcode configuration form.
 *
 * Provides controls for video/audio codec, bitrate, resolution,
 * framerate, quality parameters, and output format selection.
 * Uses grouped EncoderSelect for codec selection with hardware detection.
 * Clears dependent fields when codec changes to copy/none.
 *
 * Phase 3.5.2: Resolution split to W/H, field reorder.
 */

import { computed, watch } from "vue"
import { useI18n } from "vue-i18n"
import type { TranscodeConfigDTO } from "../../types/config"
import { useGlobalConfig } from "../../composables/useGlobalConfig"
import EncoderSelect from "./EncoderSelect.vue"
import ComboInput from "../common/ComboInput.vue"

const { t } = useI18n()

const props = defineProps<{
  config: TranscodeConfigDTO
  platform?: string
}>()

const { supportedEncoders } = useGlobalConfig()

const OUTPUT_FORMAT_SUGGESTIONS = [
  ".mp4", ".mkv", ".avi", ".mov", ".mp3", ".m4a", ".aac", ".flac", ".wav",
]

const QUALITY_MODE_SUGGESTIONS = computed(() => [
  { value: "crf", label: t("config.transcode.qualityModes.crf") },
  { value: "cq", label: t("config.transcode.qualityModes.cq") },
  { value: "qp", label: t("config.transcode.qualityModes.qp") },
  { value: "q", label: t("config.transcode.qualityModes.q") },
])

const PRESET_SUGGESTIONS = [
  "ultrafast", "superfast", "veryfast", "faster", "fast",
  "medium", "slow", "slower", "veryslow",
]

const PIXEL_FORMAT_SUGGESTIONS = [
  "yuv420p", "yuv420p10le", "yuv422p", "yuv444p",
]

const isVideoReencode = () =>
  props.config.video_codec !== "copy" && props.config.video_codec !== "none"

const RESOLUTION_PRESETS = [
  { label: "4K (2160p)", value: "3840x2160" },
  { label: "2K (1440p)", value: "2560x1440" },
  { label: "1080p", value: "1920x1080" },
  { label: "720p", value: "1280x720" },
  { label: "480p", value: "854x480" },
  { label: "360p", value: "640x360" },
  { label: "1080x1920 (vertical)", value: "1080x1920" },
  { label: "720x1280 (vertical)", value: "720x1280" },
  { label: "1080x1080 (square)", value: "1080x1080" },
]

// Split resolution "WxH" into two number inputs
const resWidth = computed({
  get: () => {
    const res = props.config.resolution
    if (!res) return 0
    return parseInt(res.split("x")[0]) || 0
  },
  set: (val: number | undefined) => {
    const w = val || 0
    const h = resHeight.value || 0
    props.config.resolution = w && h ? `${w}x${h}` : ""
  },
})

const resHeight = computed({
  get: () => {
    const res = props.config.resolution
    if (!res) return 0
    return parseInt(res.split("x")[1]) || 0
  },
  set: (val: number | undefined) => {
    const w = resWidth.value || 0
    const h = val || 0
    props.config.resolution = w && h ? `${w}x${h}` : ""
  },
})

// Clear video-related fields when codec switches to copy/none (atomic batch)
watch(() => props.config.video_codec, (newVal) => {
  if (newVal === "copy" || newVal === "none") {
    Object.assign(props.config, {
      video_bitrate: "",
      resolution: "",
      framerate: "",
      quality_mode: "",
      quality_value: 0,
      preset: "",
      pixel_format: "",
      max_bitrate: "",
      bufsize: "",
    })
  }
})

// Clear audio bitrate when codec switches to copy/none
watch(() => props.config.audio_codec, (newVal) => {
  if (newVal === "copy" || newVal === "none") {
    props.config.audio_bitrate = ""
  }
})

function handleQualityChange(payload: { quality: number; mode: string } | null) {
  if (payload) {
    props.config.quality_mode = payload.mode
    props.config.quality_value = payload.quality
  }
  // null = custom encoder, don't auto-fill
}
</script>

<template>
  <div class="card bg-base-200 shadow-sm border border-base-300">
    <div class="card-body p-4">
      <h2 class="card-title text-sm font-semibold mb-3">{{ t("config.encodingConfig") }}</h2>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-x-6 gap-y-2">
        <!-- Row 1: VC | Resolution | AC -->
        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.videoCodec") }}</span>
          </label>
          <EncoderSelect
            :model-value="config.video_codec"
            category="video"
            :supported-encoders="supportedEncoders"
            :platform="platform"
            @update:model-value="config.video_codec = $event"
            @quality-change="handleQualityChange"
          />
        </div>

        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.resolution") }}</span>
          </label>
          <select
            :value="config.resolution ? '__custom__' : ''"
            class="select select-bordered select-sm w-full mb-1"
            :disabled="!isVideoReencode()"
            @change="(e) => {
              const v = (e.target as HTMLSelectElement).value
              if (v && v !== '__custom__') props.config.resolution = v
              else props.config.resolution = ''
            }"
          >
            <option value="">{{ t("config.transcode.placeholders.resolutionPreset") }}</option>
            <option v-for="rp in RESOLUTION_PRESETS" :key="rp.value" :value="rp.value">
              {{ rp.label }} ({{ rp.value }})
            </option>
            <option v-if="config.resolution" value="__custom__" disabled>
              {{ config.resolution }}
            </option>
          </select>
          <div class="flex items-center gap-2">
            <input
              v-model.number="resWidth"
              type="number"
              :placeholder="t('config.transcode.placeholders.resolutionW')"
              class="input input-bordered input-sm flex-1"
              :disabled="!isVideoReencode()"
              min="1"
            />
            <span class="text-xs text-base-content/50">x</span>
            <input
              v-model.number="resHeight"
              type="number"
              :placeholder="t('config.transcode.placeholders.resolutionH')"
              class="input input-bordered input-sm flex-1"
              :disabled="!isVideoReencode()"
              min="1"
            />
          </div>
        </div>

        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.audioCodec") }}</span>
          </label>
          <EncoderSelect
            :model-value="config.audio_codec"
            category="audio"
            :supported-encoders="supportedEncoders"
            :platform="platform"
            @update:model-value="config.audio_codec = $event"
          />
        </div>

        <!-- Row 2: QM | Framerate | AB -->
        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.qualityMode") }}</span>
          </label>
          <select
            :value="config.quality_mode"
            class="select select-bordered select-sm w-full"
            :disabled="!isVideoReencode()"
            @change="(e) => {
              const v = (e.target as HTMLSelectElement).value
              if (v) {
                config.quality_mode = v
              } else {
                config.quality_mode = ''
                config.quality_value = 0
              }
            }"
          >
            <option value="">{{ t("config.transcode.selectQualityMode") }}</option>
            <option v-for="q in QUALITY_MODE_SUGGESTIONS" :key="q.value" :value="q.value">
              {{ q.label }}
            </option>
          </select>
        </div>

        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.framerate") }}</span>
          </label>
          <input
            v-model="config.framerate"
            type="text"
            :placeholder="t('config.transcode.placeholders.framerate')"
            class="input input-bordered input-sm w-full"
            :disabled="!isVideoReencode()"
          />
        </div>

        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.audioBitrate") }}</span>
          </label>
          <input
            v-model="config.audio_bitrate"
            type="text"
            :placeholder="t('config.transcode.placeholders.audioBitrate')"
            class="input input-bordered input-sm w-full"
            :disabled="config.audio_codec === 'copy' || config.audio_codec === 'none'"
          />
        </div>

        <!-- Row 3: QV | VB | OutputFormat -->
        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.qualityValue") }}</span>
          </label>
          <input
            v-model.number="config.quality_value"
            type="number"
            min="0"
            max="51"
            :placeholder="t('config.transcode.placeholders.qualityValue')"
            class="input input-bordered input-sm w-full"
            :disabled="!isVideoReencode()"
          />
        </div>

        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.videoBitrate") }}</span>
          </label>
          <input
            v-model="config.video_bitrate"
            type="text"
            :placeholder="t('config.transcode.placeholders.videoBitrate')"
            class="input input-bordered input-sm w-full"
            :disabled="!isVideoReencode()"
          />
        </div>

        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.outputFormat") }}</span>
          </label>
          <ComboInput
            :model-value="config.output_extension"
            :suggestions="OUTPUT_FORMAT_SUGGESTIONS"
            :placeholder="t('config.transcode.placeholders.outputFormat')"
            @update:model-value="config.output_extension = $event"
          />
        </div>

        <!-- Row 4: EP | MB -->
        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.encodingPreset") }}</span>
          </label>
          <ComboInput
            :model-value="config.preset"
            :suggestions="PRESET_SUGGESTIONS"
            :placeholder="t('config.transcode.placeholders.encodingPreset')"
            @update:model-value="config.preset = $event"
            :disabled="!isVideoReencode()"
          />
        </div>

        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.maxBitrate") }}</span>
          </label>
          <input
            v-model="config.max_bitrate"
            type="text"
            :placeholder="t('config.transcode.placeholders.maxBitrate')"
            class="input input-bordered input-sm w-full"
            :disabled="!isVideoReencode()"
          />
        </div>

        <div class="invisible" aria-hidden="true"></div>

        <!-- Row 5: PF | Bufsize -->
        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.pixelFormat") }}</span>
          </label>
          <ComboInput
            :model-value="config.pixel_format"
            :suggestions="PIXEL_FORMAT_SUGGESTIONS"
            :placeholder="t('config.transcode.placeholders.pixelFormat')"
            @update:model-value="config.pixel_format = $event"
            :disabled="!isVideoReencode()"
          />
        </div>

        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.transcode.bufferSize") }}</span>
          </label>
          <input
            v-model="config.bufsize"
            type="text"
            :placeholder="t('config.transcode.placeholders.bufferSize')"
            class="input input-bordered input-sm w-full"
            :disabled="!isVideoReencode()"
          />
        </div>

        <div class="invisible" aria-hidden="true"></div>
      </div>
    </div>
  </div>
</template>
