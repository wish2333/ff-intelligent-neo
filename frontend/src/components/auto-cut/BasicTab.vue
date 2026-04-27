<script setup lang="ts">
/**
 * BasicTab - Auto-editor basic parameters.
 *
 * Edit method, threshold, when-silent/when-normal actions
 * with independent speed/volume value inputs (always visible, disabled when not applicable).
 *
 * v2.2.0 Phase 3.
 */

import { ref, computed } from "vue"
import { useI18n } from "vue-i18n"

const { t } = useI18n()
import {
  AE_VIDEO_ENCODER_GROUPS,
  AE_AUDIO_ENCODER_GROUPS,
} from "../../data/autoEditorEncoders"

const props = defineProps<{
  editMethod: "audio" | "motion"
  audioThreshold: number
  motionThreshold: number
  whenSilentAction: string
  whenNormalAction: string
  margin: string
  smooth: string
  silentSpeedValue: number
  silentVolumeValue: number
  normalSpeedValue: number
  normalVolumeValue: number
  videoCodec: string
  audioCodec: string
}>()

const emit = defineEmits<{
  "update:editMethod": [value: "audio" | "motion"]
  "update:audioThreshold": [value: number]
  "update:motionThreshold": [value: number]
  "update:whenSilentAction": [value: string]
  "update:whenNormalAction": [value: string]
  "update:margin": [value: string]
  "update:smooth": [value: string]
  "update:silentSpeedValue": [value: number]
  "update:silentVolumeValue": [value: number]
  "update:normalSpeedValue": [value: number]
  "update:normalVolumeValue": [value: number]
  "update:videoCodec": [value: string]
  "update:audioCodec": [value: string]
}>()

const CUSTOM_KEY = "__custom__"
const videoCustom = ref("")
const audioCustom = ref("")

function isPresetVideo(name: string): boolean {
  if (!name) return true
  return AE_VIDEO_ENCODER_GROUPS.some((g) => g.encoders.some((e) => e.name === name))
}
function isPresetAudio(name: string): boolean {
  if (!name) return true
  return AE_AUDIO_ENCODER_GROUPS.some((g) => g.encoders.some((e) => e.name === name))
}

const videoSelectValue = computed(() =>
  isPresetVideo(props.videoCodec) ? props.videoCodec : CUSTOM_KEY,
)
const audioSelectValue = computed(() =>
  isPresetAudio(props.audioCodec) ? props.audioCodec : CUSTOM_KEY,
)
const videoCustomActive = computed(() => videoSelectValue.value === CUSTOM_KEY)
const audioCustomActive = computed(() => audioSelectValue.value === CUSTOM_KEY)

function handleVideoEncoderSelect(value: string) {
  if (value === CUSTOM_KEY) {
    videoCustom.value = props.videoCodec || ""
  } else {
    videoCustom.value = ""
    emit("update:videoCodec", value)
  }
}
function handleAudioEncoderSelect(value: string) {
  if (value === CUSTOM_KEY) {
    audioCustom.value = props.audioCodec || ""
  } else {
    audioCustom.value = ""
    emit("update:audioCodec", value)
  }
}
function handleVideoCustomInput(value: string) {
  videoCustom.value = value
  emit("update:videoCodec", value)
}
function handleAudioCustomInput(value: string) {
  audioCustom.value = value
  emit("update:audioCodec", value)
}

const currentThreshold = computed({
  get: () => props.editMethod === "audio" ? props.audioThreshold : props.motionThreshold,
  set: (v: number) => {
    if (props.editMethod === "audio") {
      emit("update:audioThreshold", v)
    } else {
      emit("update:motionThreshold", v)
    }
  },
})

const thresholdDisplay = computed(() => currentThreshold.value.toFixed(2))

const silentNeedsValue = computed(() => props.whenSilentAction === "speed" || props.whenSilentAction === "volume")
const silentValueKind = computed((): "speed" | "volume" | null => {
  if (props.whenSilentAction === "speed") return "speed"
  if (props.whenSilentAction === "volume") return "volume"
  return null
})
const normalNeedsValue = computed(() => props.whenNormalAction === "speed" || props.whenNormalAction === "volume")
const normalValueKind = computed((): "speed" | "volume" | null => {
  if (props.whenNormalAction === "speed") return "speed"
  if (props.whenNormalAction === "volume") return "volume"
  return null
})

const smoothParts = computed(() => {
  const parts = props.smooth.split(",")
  return {
    mincut: parts[0]?.trim() ?? "",
    minclip: parts[1]?.trim() ?? "",
  }
})

const smoothMincut = computed({
  get: () => smoothParts.value.mincut,
  set: (v: string) => {
    emit("update:smooth", `${v},${smoothParts.value.minclip}`)
  },
})

const smoothMinclip = computed({
  get: () => smoothParts.value.minclip,
  set: (v: string) => {
    emit("update:smooth", `${smoothParts.value.mincut},${v}`)
  },
})
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- Edit method -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.editMethod") }}</span>
      </label>
      <select
        :value="editMethod"
        class="select select-bordered select-sm w-full"
        @change="emit('update:editMethod', ($event.target as HTMLSelectElement).value as 'audio' | 'motion')"
      >
        <option value="audio">{{ t("autoCut.audio") }}</option>
        <option value="motion">{{ t("autoCut.motion") }}</option>
      </select>
    </div>

    <!-- Threshold -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.threshold") }}</span>
        <span class="label-text-alt">{{ thresholdDisplay }}</span>
      </label>
      <input
        :value="currentThreshold"
        type="range"
        min="0.01"
        max="0.20"
        step="0.01"
        class="range range-sm range-primary"
        @input="currentThreshold = Number(($event.target as HTMLInputElement).value)"
      />
    </div>

    <!-- When silent action + value -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.whenSilent") }}</span>
      </label>
      <select
        :value="whenSilentAction"
        class="select select-bordered select-sm w-full"
        @change="emit('update:whenSilentAction', ($event.target as HTMLSelectElement).value)"
      >
        <option value="cut">cut</option>
        <option value="speed">speed</option>
        <option value="volume">volume</option>
        <option value="nil">nil</option>
      </select>
      <input
        v-if="silentValueKind === 'speed'"
        :value="silentSpeedValue"
        type="number"
        class="input input-bordered input-sm w-full mt-1"
        :placeholder="t('autoCut.speedHint')"
        min="0.5"
        max="100"
        step="0.5"
        @input="emit('update:silentSpeedValue', Number(($event.target as HTMLInputElement).value))"
      />
      <input
        v-if="silentValueKind === 'volume'"
        :value="silentVolumeValue"
        type="number"
        class="input input-bordered input-sm w-full mt-1"
        :placeholder="t('autoCut.volumeHint')"
        min="0"
        max="1"
        step="0.1"
        @input="emit('update:silentVolumeValue', Number(($event.target as HTMLInputElement).value))"
      />
      <input
        v-if="!silentNeedsValue"
        type="number"
        disabled
        class="input input-bordered input-sm w-full mt-1 opacity-50"
        :placeholder="t('autoCut.noValueNeeded')"
      />
    </div>

    <!-- When normal action + value -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.whenNormal") }}</span>
      </label>
      <select
        :value="whenNormalAction"
        class="select select-bordered select-sm w-full"
        @change="emit('update:whenNormalAction', ($event.target as HTMLSelectElement).value)"
      >
        <option value="nil">nil</option>
        <option value="cut">cut</option>
        <option value="speed">speed</option>
        <option value="volume">volume</option>
      </select>
      <input
        v-if="normalValueKind === 'speed'"
        :value="normalSpeedValue"
        type="number"
        class="input input-bordered input-sm w-full mt-1"
        :placeholder="t('autoCut.speedHint')"
        min="0.5"
        max="100"
        step="0.5"
        @input="emit('update:normalSpeedValue', Number(($event.target as HTMLInputElement).value))"
      />
      <input
        v-if="normalValueKind === 'volume'"
        :value="normalVolumeValue"
        type="number"
        class="input input-bordered input-sm w-full mt-1"
        :placeholder="t('autoCut.volumeHint')"
        min="0"
        max="1"
        step="0.1"
        @input="emit('update:normalVolumeValue', Number(($event.target as HTMLInputElement).value))"
      />
      <input
        v-if="!normalNeedsValue"
        type="number"
        disabled
        class="input input-bordered input-sm w-full mt-1 opacity-50"
        :placeholder="t('autoCut.noValueNeeded')"
      />
    </div>

    <!-- Margin -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.margin") }}</span>
      </label>
      <input
        :value="margin"
        type="text"
        class="input input-bordered input-sm w-full"
        placeholder="0.2s"
        @input="emit('update:margin', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <!-- Smooth mincut -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.smoothMincut") }}</span>
      </label>
      <input
        :value="smoothMincut"
        type="text"
        class="input input-bordered input-sm w-full"
        placeholder="0.2s"
        @input="smoothMincut = ($event.target as HTMLInputElement).value"
      />
    </div>

    <!-- Smooth minclip -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.smoothMinclip") }}</span>
      </label>
      <input
        :value="smoothMinclip"
        type="text"
        class="input input-bordered input-sm w-full"
        placeholder="0.1s"
        @input="smoothMinclip = ($event.target as HTMLInputElement).value"
      />
    </div>

    <!-- Video codec -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.videoCodec") }}</span>
      </label>
      <select
        :value="videoSelectValue"
        class="select select-bordered select-sm w-full"
        @change="handleVideoEncoderSelect(($event.target as HTMLSelectElement).value)"
      >
        <option value="">{{ t("autoCut.encoderAuto") }}</option>
        <optgroup
          v-for="group in AE_VIDEO_ENCODER_GROUPS"
          :key="'bv-' + group.priority"
          :label="t(group.labelKey)"
        >
          <option
            v-for="enc in group.encoders"
            :key="'bv-' + enc.name"
            :value="enc.name"
            :title="enc.description"
          >{{ enc.displayName }}</option>
        </optgroup>
        <option :value="CUSTOM_KEY">{{ t("autoCut.encoderCustom") }}</option>
      </select>
      <input
        v-if="videoCustomActive"
        :value="videoCustom"
        type="text"
        class="input input-bordered input-sm w-full mt-1"
        :placeholder="t('autoCut.encoderCustomHint')"
        @input="handleVideoCustomInput(($event.target as HTMLInputElement).value)"
      />
    </div>

    <!-- Audio codec -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.audioCodec") }}</span>
      </label>
      <select
        :value="audioSelectValue"
        class="select select-bordered select-sm w-full"
        @change="handleAudioEncoderSelect(($event.target as HTMLSelectElement).value)"
      >
        <option value="">{{ t("autoCut.encoderAuto") }}</option>
        <optgroup
          v-for="group in AE_AUDIO_ENCODER_GROUPS"
          :key="'ba-' + group.priority"
          :label="t(group.labelKey)"
        >
          <option
            v-for="enc in group.encoders"
            :key="'ba-' + enc.name"
            :value="enc.name"
            :title="enc.description"
          >{{ enc.displayName }}</option>
        </optgroup>
        <option :value="CUSTOM_KEY">{{ t("autoCut.encoderCustom") }}</option>
      </select>
      <input
        v-if="audioCustomActive"
        :value="audioCustom"
        type="text"
        class="input input-bordered input-sm w-full mt-1"
        :placeholder="t('autoCut.encoderCustomHint')"
        @input="handleAudioCustomInput(($event.target as HTMLInputElement).value)"
      />
    </div>
  </div>
</template>
