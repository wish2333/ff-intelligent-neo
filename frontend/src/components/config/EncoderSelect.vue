<script setup lang="ts">
/**
 * Grouped encoder selector with hardware detection and custom input support.
 *
 * Encoders are grouped by priority (P0/P1/P2).
 * Hardware encoders not in supportedEncoders are grayed out.
 * Bottom option "Other (custom name)..." reveals text input for arbitrary encoder.
 */

import { ref, computed } from "vue"
import { useI18n } from "vue-i18n"
import type { EncoderConfigDTO } from "../../types/config"
import { VIDEO_ENCODERS, AUDIO_ENCODERS, PRIORITY_LABELS } from "../../data/encoders"

const { t } = useI18n()

const PRIORITY_I18N_KEYS: Record<string, string> = {
  P0: "config.encoder.priorityLabels.recommended",
  P1: "config.encoder.priorityLabels.alternative",
  P2: "config.encoder.priorityLabels.hardwareSpecific",
}

const OTHER_KEY = "__other__"

const props = defineProps<{
  modelValue: string
  category: "video" | "audio"
  supportedEncoders?: string[]
}>()

const emit = defineEmits<{
  "update:modelValue": [value: string]
  "qualityChange": [config: { quality: number; mode: string } | null]
}>()

const customName = ref("")

const isCustomMode = computed(() => props.modelValue && !isPresetEncoder(props.modelValue))

const encoders = computed<EncoderConfigDTO[]>(() =>
  props.category === "video" ? VIDEO_ENCODERS : AUDIO_ENCODERS,
)

const groups = computed(() => {
  const list = encoders.value
  const seen = new Set<string>()
  return list
    .filter((e: EncoderConfigDTO) => {
      if (seen.has(e.priority)) return false
      seen.add(e.priority)
      return true
    })
    .map((e: EncoderConfigDTO) => ({
      priority: e.priority,
      label: t(PRIORITY_I18N_KEYS[e.priority] || "") || PRIORITY_LABELS[e.priority] || e.priority,
      encoders: list.filter((enc: EncoderConfigDTO) => enc.priority === e.priority),
    }))
    .sort((a: { priority: string }, b: { priority: string }) => a.priority.localeCompare(b.priority))
})

function isPresetEncoder(name: string): boolean {
  return encoders.value.some((e: EncoderConfigDTO) => e.name === name)
}

function isSupported(encoder: EncoderConfigDTO): boolean {
  if (!props.supportedEncoders?.length) return true
  return props.supportedEncoders.includes(encoder.name)
}

function handleSelect(encoderName: string) {
  if (encoderName === OTHER_KEY) {
    customName.value = ""
    emit("update:modelValue", "")
    emit("qualityChange", null)
    return
  }
  emit("update:modelValue", encoderName)
  customName.value = ""
  const enc = encoders.value.find((e: EncoderConfigDTO) => e.name === encoderName)
  if (enc?.recommendedQuality != null && enc?.qualityMode) {
    emit("qualityChange", { quality: enc.recommendedQuality, mode: enc.qualityMode })
  } else {
    emit("qualityChange", null)
  }
}

function handleCustomInput(value: string) {
  customName.value = value
  emit("update:modelValue", value)
  emit("qualityChange", null)
}
</script>

<template>
  <div>
    <select
      :value="isCustomMode ? OTHER_KEY : modelValue"
      class="select select-bordered select-sm w-full"
      @change="(e) => handleSelect((e.target as HTMLSelectElement).value)"
    >
      <option value="" disabled>{{ t("config.encoder.selectEncoder") }}</option>
      <optgroup
        v-for="group in groups"
        :key="group.priority"
        :label="group.label"
      >
        <option
          v-for="enc in group.encoders"
          :key="enc.name"
          :value="enc.name"
          :disabled="!isSupported(enc)"
          :title="!isSupported(enc) ? t('config.encoder.hwNotDetected') : `${enc.description} (recommended: ${enc.recommendedQuality ?? 'auto'})`"
        >
          {{ enc.displayName }} ({{ enc.name }})
        </option>
      </optgroup>
      <option :value="OTHER_KEY">{{ t("config.encoder.other") }}</option>
    </select>

    <!-- Custom encoder text input -->
    <input
      v-if="modelValue === '' && customName === ''"
      v-model="customName"
      type="text"
      :placeholder="t('config.encoder.customPlaceholder')"
      class="input input-bordered input-sm w-full mt-1"
      @input="handleCustomInput(($event.target as HTMLInputElement).value)"
    />
  </div>
</template>
