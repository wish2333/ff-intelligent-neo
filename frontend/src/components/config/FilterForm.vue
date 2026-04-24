<script setup lang="ts">
/**
 * Filter configuration form.
 *
 * Controls for rotate, crop, watermark, volume, speed,
 * audio normalization, and aspect ratio conversion.
 * Phase 3.5.2: Freeze watermark + clear on aspect_convert,
 * fullscreen-drop for watermark, context-dependent bg_image.
 */

import { computed, watch } from "vue"
import { useI18n } from "vue-i18n"
import type { FilterConfigDTO } from "../../types/config"
import FileDropInput from "../common/FileDropInput.vue"

const { t } = useI18n()

const props = defineProps<{
  config: FilterConfigDTO
}>()

const ROTATE_OPTIONS = computed(() => [
  { value: "", label: t("config.filters.rotateOptions.none") },
  { value: "transpose=1", label: t("config.filters.rotateOptions.cw90") },
  { value: "transpose=2", label: t("config.filters.rotateOptions.cw180") },
  { value: "transpose=3", label: t("config.filters.rotateOptions.cw270") },
])

const WATERMARK_POSITIONS = computed(() => [
  { value: "top-left", label: t("config.filters.watermarkPositions.topLeft") },
  { value: "top-right", label: t("config.filters.watermarkPositions.topRight") },
  { value: "bottom-left", label: t("config.filters.watermarkPositions.bottomLeft") },
  { value: "bottom-right", label: t("config.filters.watermarkPositions.bottomRight") },
])

const ASPECT_MODES = computed(() => [
  { value: "", label: t("config.filters.aspectModes.none") },
  { value: "H2V-I", label: t("config.filters.aspectModes.h2vI") },
  { value: "H2V-T", label: t("config.filters.aspectModes.h2vT") },
  { value: "H2V-B", label: t("config.filters.aspectModes.h2vB") },
  { value: "V2H-I", label: t("config.filters.aspectModes.v2hI") },
  { value: "V2H-T", label: t("config.filters.aspectModes.v2hT") },
  { value: "V2H-B", label: t("config.filters.aspectModes.v2hB") },
])

const hasAspectConvert = computed(() => !!props.config.aspect_convert)
const hasAudioNormalize = computed(() => props.config.audio_normalize)

// I modes need background image, T/B modes don't
const needsBgImage = computed(() => {
  const mode = props.config.aspect_convert
  return mode === "H2V-I" || mode === "V2H-I"
})

// Determine fullscreen drop target based on context
const fullscreenDropTarget = computed(() => {
  if (!hasAspectConvert.value) return "watermark"
  if (needsBgImage.value) return "bg_image"
  return null // T/B modes: no fullscreen drop needed
})

// Auto-fill default target_resolution when aspect_convert is selected
watch(() => props.config.aspect_convert, (val) => {
  if (val) {
    props.config.rotate = ""
    props.config.watermark_path = ""
    // Auto-fill a default target_resolution if empty
    if (!props.config.target_resolution) {
      // Determine default: if mode starts with "H" (horizontal), default to 1080x1920
      // if starts with "V" (vertical), default to 1920x1080
      props.config.target_resolution = val.startsWith("H") ? "1080x1920" : "1920x1080"
    }
  }
})
watch(() => props.config.rotate, (val) => {
  if (val) props.config.aspect_convert = ""
})

const speedWarningText = computed(() => {
  const val = props.config.speed
  if (!val) return ""
  const num = parseFloat(val)
  if (isNaN(num)) return t("config.filters.speed.invalidSpeed")
  if (num < 0.25 || num > 4) return t("config.filters.speed.speedOutOfRange")
  if (num < 0.5 || num > 2) return t("config.filters.speed.speedDesync")
  return ""
})

const speedWarningSeverity = computed<"error" | "warning" | "">(() => {
  const val = props.config.speed
  if (!val) return ""
  const num = parseFloat(val)
  if (isNaN(num)) return "error"
  if (num < 0.25 || num > 4) return "error"
  if (num < 0.5 || num > 2) return "warning"
  return ""
})

const bgInfoText = computed(() => {
  if (typeof props.config.aspect_convert === "string" && props.config.aspect_convert.endsWith("-T")) {
    return t("config.filters.blurredBg")
  }
  return t("config.filters.blackPaddingBg")
})
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title text-sm font-semibold mb-3">{{ t("config.filters.title") }}</h2>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Column 1: Aspect Convert, Rotate, Crop -->
        <div class="space-y-3">
          <!-- Aspect Convert -->
          <div class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">{{ t("config.filters.aspectRatioConvert") }}</span>
            </label>
            <select
              v-model="config.aspect_convert"
              class="select select-bordered select-sm w-full"
              :disabled="!!config.rotate"
            >
              <option
                v-for="mode in ASPECT_MODES"
                :key="mode.value"
                :value="mode.value"
              >
                {{ mode.label }}
              </option>
            </select>
            <label v-if="hasAspectConvert" class="label py-0.5">
              <span class="label-text-alt text-xs text-warning">
                {{ t("config.filters.aspectConvertWarning") }}
              </span>
            </label>
          </div>

          <!-- Aspect Convert: Target Resolution -->
          <div v-if="hasAspectConvert" class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">{{ t("config.filters.targetResolution") }}</span>
            </label>
            <input
              v-model="config.target_resolution"
              type="text"
              :placeholder="t('config.filters.targetResPlaceholder')"
              class="input input-bordered input-sm w-full"
            />
          </div>

          <!-- Aspect Convert: Background Image (only for I modes) -->
          <div v-if="hasAspectConvert && needsBgImage" class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">{{ t("config.filters.backgroundImage") }}</span>
            </label>
            <FileDropInput
              :model-value="config.bg_image_path"
              accept=".png,.jpg,.jpeg,.bmp,.webp"
              :placeholder="t('config.filters.bgPlaceholder')"
              :fullscreen-drop="fullscreenDropTarget === 'bg_image'"
              @update:model-value="config.bg_image_path = $event"
            />
          </div>

          <!-- Aspect Convert: Info for T/B modes (no bg image needed) -->
          <div v-if="hasAspectConvert && !needsBgImage" class="form-control">
            <div class="rounded-lg border border-base-300 bg-base-300/30 px-3 py-3 text-center">
              <p class="text-xs text-base-content/50">
                {{ bgInfoText }}
              </p>
            </div>
          </div>

          <!-- Rotate -->
          <div class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">{{ t("config.filters.rotate") }}</span>
            </label>
            <select
              v-model="config.rotate"
              class="select select-bordered select-sm w-full"
              :disabled="hasAspectConvert"
            >
              <option
                v-for="opt in ROTATE_OPTIONS"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </option>
            </select>
          </div>

          <!-- Crop -->
          <div class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">{{ t("config.filters.crop") }}</span>
            </label>
            <input
              v-model="config.crop"
              type="text"
              :placeholder="t('config.filters.cropPlaceholder')"
              class="input input-bordered input-sm w-full"
              :disabled="hasAspectConvert"
            />
            <label class="label py-0.5">
              <span class="label-text-alt text-xs text-base-content/50">
                {{ t("config.filters.cropFormat") }}
              </span>
            </label>
            <div class="pl-4 space-y-0.5">
              <span class="block text-xs text-base-content/40">{{ t("config.filters.cropW") }}</span>
              <span class="block text-xs text-base-content/40">{{ t("config.filters.cropH") }}</span>
              <span class="block text-xs text-base-content/40">{{ t("config.filters.cropX") }}</span>
              <span class="block text-xs text-base-content/40">{{ t("config.filters.cropY") }}</span>
            </div>
          </div>
        </div>

        <!-- Column 2: Watermark -->
        <div class="space-y-3">
          <div class="divider my-0 text-xs">{{ t("config.filters.watermark.title") }}</div>

          <!-- Watermark Path (hidden when aspect_convert active) -->
          <div v-if="!hasAspectConvert">
            <div class="form-control">
              <label class="label py-1">
                <span class="label-text text-xs">{{ t("config.filters.watermark.image") }}</span>
              </label>
              <FileDropInput
                :model-value="config.watermark_path"
                accept=".png,.jpg,.jpeg,.bmp,.webp"
                :placeholder="t('config.filters.watermark.placeholder')"
                :fullscreen-drop="fullscreenDropTarget === 'watermark'"
                @update:model-value="config.watermark_path = $event"
              />
            </div>

            <!-- Watermark Position -->
            <div v-if="config.watermark_path" class="form-control">
              <label class="label py-1">
                <span class="label-text text-xs">{{ t("config.filters.watermark.position") }}</span>
              </label>
              <select
                v-model="config.watermark_position"
                class="select select-bordered select-sm w-full"
              >
                <option
                  v-for="pos in WATERMARK_POSITIONS"
                  :key="pos.value"
                  :value="pos.value"
                >
                  {{ pos.label }}
                </option>
              </select>
            </div>

            <!-- Watermark Margin -->
            <div v-if="config.watermark_path" class="form-control">
              <label class="label py-1">
                <span class="label-text text-xs">{{ t("config.filters.watermark.margin") }}</span>
              </label>
              <input
                v-model.number="config.watermark_margin"
                type="number"
                min="0"
                max="100"
                class="input input-bordered input-sm w-full"
              />
            </div>
          </div>
        </div>

        <!-- Column 3: Audio -->
        <div class="space-y-3">
          <div class="divider my-0 text-xs">{{ t("config.filters.audio.title") }}</div>

          <!-- Volume -->
          <div class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">{{ t("config.filters.audio.volume") }}</span>
            </label>
            <input
              v-model="config.volume"
              type="text"
              :placeholder="t('config.filters.audio.volumePlaceholder')"
              class="input input-bordered input-sm w-full"
              :disabled="hasAudioNormalize"
            />
            <label class="label py-0.5">
              <span class="label-text-alt text-xs text-base-content/50">
                {{ t("config.filters.audio.volumeHint") }}
                <span v-if="hasAudioNormalize" class="text-warning">{{ t("config.filters.audio.volumeDisabledWhenNormalize") }}</span>
              </span>
            </label>
          </div>

          <!-- Audio Normalization -->
          <div class="form-control">
            <label class="label cursor-pointer justify-start gap-2 py-1">
              <input
                v-model="config.audio_normalize"
                type="checkbox"
                class="checkbox checkbox-sm checkbox-primary"
              />
              <div>
                <span class="label-text text-xs">{{ t("config.filters.audio.normalize") }}</span>
                <p class="text-xs text-base-content/50 mt-0.5">{{ t("config.filters.audio.normalizeDesc") }}</p>
              </div>
            </label>
          </div>

          <!-- Normalize Params -->
          <div v-if="config.audio_normalize" class="ml-4 space-y-2">
            <div class="form-control">
              <label class="label py-0">
                <span class="label-text text-xs">{{ t("config.filters.audio.integratedLoudness") }}</span>
              </label>
              <input
                v-model.number="config.target_loudness"
                type="number"
                min="-70"
                max="-5"
                class="input input-bordered input-sm w-full"
              />
            </div>
            <div class="form-control">
              <label class="label py-0">
                <span class="label-text text-xs">{{ t("config.filters.audio.truePeak") }}</span>
              </label>
              <input
                v-model.number="config.true_peak"
                type="number"
                min="-9"
                max="0"
                class="input input-bordered input-sm w-full"
              />
            </div>
            <div class="form-control">
              <label class="label py-0">
                <span class="label-text text-xs">{{ t("config.filters.audio.lra") }}</span>
              </label>
              <input
                v-model.number="config.lra"
                type="number"
                min="1"
                max="50"
                class="input input-bordered input-sm w-full"
              />
            </div>
          </div>

          <div class="divider my-0 text-xs">{{ t("config.filters.speed.title") }}</div>

          <!-- Speed -->
          <div class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">{{ t("config.filters.speed.speed") }}</span>
            </label>
            <input
              v-model="config.speed"
              type="text"
              :placeholder="t('config.filters.speed.placeholder')"
              class="input input-bordered input-sm w-full"
            />
            <label class="label py-0.5">
              <span
                class="label-text-alt text-xs"
                :class="speedWarningSeverity === 'error' ? 'text-error' : speedWarningSeverity === 'warning' ? 'text-warning' : 'text-base-content/50'"
              >
                {{ speedWarningText || t("config.filters.speed.defaultHint") }}
              </span>
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
