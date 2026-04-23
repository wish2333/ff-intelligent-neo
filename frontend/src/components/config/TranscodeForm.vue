<script setup lang="ts">
/**
 * Transcode configuration form.
 *
 * Provides controls for video/audio codec, bitrate, resolution,
 * framerate, and output format selection.
 * Codec and output fields support custom input via ComboInput.
 * Clears dependent fields when codec changes to copy/none.
 */

import { watch } from "vue"
import type { TranscodeConfigDTO } from "../../types/config"
import ComboInput from "../common/ComboInput.vue"

const props = defineProps<{
  config: TranscodeConfigDTO
}>()

const VIDEO_CODEC_SUGGESTIONS = [
  "libx264", "libx265", "copy", "none",
]

const AUDIO_CODEC_SUGGESTIONS = [
  "aac", "libmp3lame", "copy", "none",
]

const OUTPUT_FORMAT_SUGGESTIONS = [
  ".mp4", ".mkv", ".avi", ".mov", ".mp3", ".aac", ".flac", ".wav",
]

// Clear video-related fields when codec switches to copy/none
watch(() => props.config.video_codec, (newVal) => {
  if (newVal === "copy" || newVal === "none") {
    props.config.video_bitrate = ""
    props.config.resolution = ""
    props.config.framerate = ""
  }
})

// Clear audio bitrate when codec switches to copy/none
watch(() => props.config.audio_codec, (newVal) => {
  if (newVal === "copy" || newVal === "none") {
    props.config.audio_bitrate = ""
  }
})
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title text-sm font-semibold mb-3">Encoding Config</h2>

      <!-- Video Codec -->
      <div class="form-control mb-3">
        <label class="label py-1">
          <span class="label-text text-xs">Video Codec</span>
        </label>
        <ComboInput
          :model-value="config.video_codec"
          :suggestions="VIDEO_CODEC_SUGGESTIONS"
          placeholder="e.g. libx264, libx265, copy, none..."
          @update:model-value="config.video_codec = $event"
        />
      </div>

      <!-- Video Bitrate -->
      <div
        v-if="config.video_codec !== 'copy' && config.video_codec !== 'none'"
        class="form-control mb-3"
      >
        <label class="label py-1">
          <span class="label-text text-xs">Video Bitrate</span>
        </label>
        <input
          v-model="config.video_bitrate"
          type="text"
          placeholder="e.g. 5M, 8000k (auto if empty)"
          class="input input-bordered input-sm w-full"
        />
      </div>

      <!-- Resolution -->
      <div
        v-if="config.video_codec !== 'copy' && config.video_codec !== 'none'"
        class="form-control mb-3"
      >
        <label class="label py-1">
          <span class="label-text text-xs">Resolution</span>
        </label>
        <input
          v-model="config.resolution"
          type="text"
          placeholder="e.g. 1920x1080 (original if empty)"
          class="input input-bordered input-sm w-full"
        />
      </div>

      <!-- Framerate -->
      <div
        v-if="config.video_codec !== 'copy' && config.video_codec !== 'none'"
        class="form-control mb-3"
      >
        <label class="label py-1">
          <span class="label-text text-xs">Framerate</span>
        </label>
        <input
          v-model="config.framerate"
          type="text"
          placeholder="e.g. 30, 60 (original if empty)"
          class="input input-bordered input-sm w-full"
        />
      </div>

      <!-- Divider -->
      <div class="divider my-2 text-xs">Audio</div>

      <!-- Audio Codec -->
      <div class="form-control mb-3">
        <label class="label py-1">
          <span class="label-text text-xs">Audio Codec</span>
        </label>
        <ComboInput
          :model-value="config.audio_codec"
          :suggestions="AUDIO_CODEC_SUGGESTIONS"
          placeholder="e.g. aac, libmp3lame, copy, none..."
          @update:model-value="config.audio_codec = $event"
        />
      </div>

      <!-- Audio Bitrate -->
      <div
        v-if="config.audio_codec !== 'copy' && config.audio_codec !== 'none'"
        class="form-control mb-3"
      >
        <label class="label py-1">
          <span class="label-text text-xs">Audio Bitrate</span>
        </label>
        <input
          v-model="config.audio_bitrate"
          type="text"
          placeholder="e.g. 192k, 320k"
          class="input input-bordered input-sm w-full"
        />
      </div>

      <!-- Divider -->
      <div class="divider my-2 text-xs">Output</div>

      <!-- Output Format -->
      <div class="form-control">
        <label class="label py-1">
          <span class="label-text text-xs">Output Format</span>
        </label>
        <ComboInput
          :model-value="config.output_extension"
          :suggestions="OUTPUT_FORMAT_SUGGESTIONS"
          placeholder="e.g. .mp4, .mkv, .mp3..."
          @update:model-value="config.output_extension = $event"
        />
      </div>
    </div>
  </div>
</template>
