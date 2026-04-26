<script setup lang="ts">
/**
 * BasicTab - Auto-editor basic parameters.
 *
 * Edit method, threshold, when-silent/when-normal actions
 * with dynamic speed/volume value inputs.
 *
 * v2.2.0 Phase 3.
 */

import { computed } from "vue"
import { useI18n } from "vue-i18n"

const { t } = useI18n()

const props = defineProps<{
  editMethod: "audio" | "motion"
  audioThreshold: number
  motionThreshold: number
  whenSilentAction: string
  whenNormalAction: string
  margin: string
  smooth: string
  speedValue: number
  volumeValue: number
}>()

const emit = defineEmits<{
  "update:editMethod": [value: "audio" | "motion"]
  "update:audioThreshold": [value: number]
  "update:motionThreshold": [value: number]
  "update:whenSilentAction": [value: string]
  "update:whenNormalAction": [value: string]
  "update:margin": [value: string]
  "update:smooth": [value: string]
  "update:speedValue": [value: number]
  "update:volumeValue": [value: number]
}>()

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

const silentIsSpeed = computed(() => props.whenSilentAction === "speed")
const silentIsVolume = computed(() => props.whenSilentAction === "volume")
const normalIsSpeed = computed(() => props.whenNormalAction === "speed")
const normalIsVolume = computed(() => props.whenNormalAction === "volume")

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
        <span class="label-text-alt">{{ currentThreshold }}</span>
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
        v-if="silentIsSpeed"
        :value="speedValue"
        type="number"
        class="input input-bordered input-sm w-full mt-1"
        :placeholder="t('autoCut.speedHint')"
        min="0.5"
        max="100"
        step="0.5"
        @input="emit('update:speedValue', Number(($event.target as HTMLInputElement).value))"
      />
      <input
        v-if="silentIsVolume"
        :value="volumeValue"
        type="number"
        class="input input-bordered input-sm w-full mt-1"
        :placeholder="t('autoCut.volumeHint')"
        min="0"
        max="1"
        step="0.1"
        @input="emit('update:volumeValue', Number(($event.target as HTMLInputElement).value))"
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
        v-if="normalIsSpeed"
        :value="speedValue"
        type="number"
        class="input input-bordered input-sm w-full mt-1"
        :placeholder="t('autoCut.speedHint')"
        min="0.5"
        max="100"
        step="0.5"
        @input="emit('update:speedValue', Number(($event.target as HTMLInputElement).value))"
      />
      <input
        v-if="normalIsVolume"
        :value="volumeValue"
        type="number"
        class="input input-bordered input-sm w-full mt-1"
        :placeholder="t('autoCut.volumeHint')"
        min="0"
        max="1"
        step="0.1"
        @input="emit('update:volumeValue', Number(($event.target as HTMLInputElement).value))"
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
  </div>
</template>
