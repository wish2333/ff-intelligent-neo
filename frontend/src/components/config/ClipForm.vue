<script setup lang="ts">
/**
 * Video clipping configuration form.
 *
 * Supports extract mode (remove head/tail) and cut mode (precise range).
 * Phase 3.5.2: Side-by-side Start/End, H:MM:SS:ms split inputs.
 */

import { computed, onUnmounted, ref, watch } from "vue"
import { useI18n } from "vue-i18n"
import { call } from "../../bridge"
import type { ClipConfigDTO } from "../../types/config"

const { t } = useI18n()

let alertTimer: ReturnType<typeof setTimeout> | null = null
onUnmounted(() => { if (alertTimer) clearTimeout(alertTimer) })

const props = defineProps<{
  config: ClipConfigDTO
  filePath?: string
}>()

const isExtractMode = computed(() => props.config.clip_mode === "extract" || props.config.clip_mode === "extract_no_accurate")
const endLabel = computed(() => {
  if (isExtractMode.value) return t("config.clip.tailDuration")
  return t("config.clip.endTime")
})

const fileDuration = ref(0)

// --- Time input split helpers ---
// Format stored in config: "H:MM:SS.mmm" (e.g. "0:01:30.500")

function parseTimeFields(timeStr: string): { h: number; mm: number; ss: number; ms: number } {
  if (!timeStr) return { h: 0, mm: 0, ss: 0, ms: 0 }
  const parts = timeStr.replace(".", ":").split(":")
  return {
    h: parseInt(parts[0]) || 0,
    mm: parseInt(parts[1]) || 0,
    ss: parseInt(parts[2]) || 0,
    ms: parseInt(parts[3]) || 0,
  }
}

function clamp(val: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, Math.round(val) || 0))
}

function buildTimeString(h: number, mm: number, ss: number, ms: number): string {
  if (!h && !mm && !ss && !ms) return ""
  return `${clamp(h, 0, 99)}:${String(clamp(mm, 0, 59)).padStart(2, "0")}:${String(clamp(ss, 0, 59)).padStart(2, "0")}.${String(clamp(ms, 0, 999)).padStart(3, "0")}`
}

function clearClipInputs() {
  props.config.start_time = ""
  props.config.end_time_or_duration = ""
}

// Start time fields
const startFields = computed({
  get: () => parseTimeFields(props.config.start_time),
  set: (val: { h: number; mm: number; ss: number; ms: number }) => {
    props.config.start_time = buildTimeString(val.h, val.mm, val.ss, val.ms)
  },
})
const startH = computed({
  get: () => startFields.value.h,
  set: (v: number | undefined) => { startFields.value = { ...startFields.value, h: v || 0 } },
})
const startMM = computed({
  get: () => startFields.value.mm,
  set: (v: number | undefined) => { startFields.value = { ...startFields.value, mm: v || 0 } },
})
const startSS = computed({
  get: () => startFields.value.ss,
  set: (v: number | undefined) => { startFields.value = { ...startFields.value, ss: v || 0 } },
})
const startMs = computed({
  get: () => startFields.value.ms,
  set: (v: number | undefined) => { startFields.value = { ...startFields.value, ms: v || 0 } },
})

// End time fields
const endFields = computed({
  get: () => parseTimeFields(props.config.end_time_or_duration),
  set: (val: { h: number; mm: number; ss: number; ms: number }) => {
    props.config.end_time_or_duration = buildTimeString(val.h, val.mm, val.ss, val.ms)
  },
})
const endH = computed({
  get: () => endFields.value.h,
  set: (v: number | undefined) => { endFields.value = { ...endFields.value, h: v || 0 } },
})
const endMM = computed({
  get: () => endFields.value.mm,
  set: (v: number | undefined) => { endFields.value = { ...endFields.value, mm: v || 0 } },
})
const endSS = computed({
  get: () => endFields.value.ss,
  set: (v: number | undefined) => { endFields.value = { ...endFields.value, ss: v || 0 } },
})
const endMs = computed({
  get: () => endFields.value.ms,
  set: (v: number | undefined) => { endFields.value = { ...endFields.value, ms: v || 0 } },
})

const fileDurationText = computed(() => {
  const minutes = Math.floor(fileDuration.value / 60)
  const seconds = Math.floor(fileDuration.value % 60)
  return t("config.clip.fileDuration", { minutes, seconds })
})

// Auto-fetch file duration for extract mode
const alertMessage = ref("")
watch(
  () => [isExtractMode.value, props.filePath],
  async ([isExtract, filePath]) => {
    if (isExtract && filePath) {
      try {
        const res = await call<number>("get_file_duration", filePath)
        if (res.success && res.data != null) {
          fileDuration.value = res.data
        }
      } catch (err) {
        alertMessage.value = t("common.operationFailed") + ": " + (err as Error).message
        if (alertTimer) clearTimeout(alertTimer)
        alertTimer = setTimeout(() => { alertMessage.value = "" }, 3000)
      }
    }
  },
  { immediate: true },
)
</script>

<template>
  <div class="card bg-base-200 shadow-sm border border-base-300">
    <div class="card-body p-4">
      <div v-if="alertMessage" class="alert alert-error py-1 px-3 text-xs mb-2">{{ alertMessage }}</div>
      <div class="flex items-center justify-between mb-3">
        <h2 class="card-title text-sm font-semibold">{{ t("config.clip.title") }}</h2>
        <button class="btn btn-ghost btn-xs text-base-content/50" @click="clearClipInputs">
          {{ t("config.clip.clearInputs") }}
        </button>
      </div>
      <p class="text-xs text-base-content/60 mb-3">
        {{ t("config.clip.description") }}
      </p>

      <!-- Clip Mode -->
      <div class="form-control mb-3">
        <label class="label py-1">
          <span class="label-text text-xs">{{ t("config.clip.clipMode") }}</span>
        </label>
        <select
          v-model="config.clip_mode"
          class="select select-bordered select-sm w-full"
        >
          <option value="cut">{{ t("config.clip.cutMode") }}</option>
          <option value="extract">{{ t("config.clip.extractMode") }}</option>
          <option value="cut_no_accurate">{{ t("config.clip.cutModeNoAccurate") }}</option>
          <option value="extract_no_accurate">{{ t("config.clip.extractModeNoAccurate") }}</option>
        </select>
      </div>

      <!-- Start Time / End Time side by side -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Start Time -->
        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ t("config.clip.startTime") }}</span>
          </label>
          <div class="flex items-center gap-1">
            <input v-model.number="startH" type="number" min="0" max="99" placeholder="H" class="input input-bordered input-sm w-14 text-center" />
            <span class="text-xs text-base-content/50">:</span>
            <input v-model.number="startMM" type="number" min="0" max="59" placeholder="MM" class="input input-bordered input-sm w-14 text-center" />
            <span class="text-xs text-base-content/50">:</span>
            <input v-model.number="startSS" type="number" min="0" max="59" placeholder="SS" class="input input-bordered input-sm w-14 text-center" />
            <span class="text-xs text-base-content/50">.</span>
            <input v-model.number="startMs" type="number" min="0" max="999" placeholder="ms" class="input input-bordered input-sm w-16 text-center" />
          </div>
          <label class="label py-0.5">
            <span class="label-text-alt text-xs text-base-content/50">{{ t("config.clip.leaveEmptyToSkip") }}</span>
          </label>
        </div>

        <!-- End Time / Duration -->
        <div class="form-control">
          <label class="label py-1">
            <span class="label-text text-xs">{{ endLabel }}</span>
          </label>
          <div class="flex items-center gap-1">
            <input v-model.number="endH" type="number" min="0" max="99" placeholder="H" class="input input-bordered input-sm w-14 text-center" />
            <span class="text-xs text-base-content/50">:</span>
            <input v-model.number="endMM" type="number" min="0" max="59" placeholder="MM" class="input input-bordered input-sm w-14 text-center" />
            <span class="text-xs text-base-content/50">:</span>
            <input v-model.number="endSS" type="number" min="0" max="59" placeholder="SS" class="input input-bordered input-sm w-14 text-center" />
            <span class="text-xs text-base-content/50">.</span>
            <input v-model.number="endMs" type="number" min="0" max="999" placeholder="ms" class="input input-bordered input-sm w-16 text-center" />
          </div>
          <label v-if="isExtractMode && fileDuration > 0" class="label py-0.5">
            <span class="label-text-alt text-xs text-base-content/50">
              {{ fileDurationText }}
            </span>
          </label>
          <label v-else class="label py-0.5">
            <span class="label-text-alt text-xs text-base-content/50">{{ t("config.clip.leaveEmptyToSkip") }}</span>
          </label>
        </div>
      </div>

      <!-- Copy Codec Toggle -->
      <div class="form-control mt-3">
        <label class="label cursor-pointer justify-start gap-2 py-1">
          <input
            v-model="config.use_copy_codec"
            type="checkbox"
            class="checkbox checkbox-sm checkbox-primary"
          />
          <div>
            <span class="label-text text-xs">{{ t("config.clip.copyCodec") }}</span>
            <p class="text-xs text-base-content/50 mt-0.5">
              {{ t("config.clip.copyCodecDesc") }}
            </p>
          </div>
        </label>
      </div>
    </div>
  </div>
</template>
