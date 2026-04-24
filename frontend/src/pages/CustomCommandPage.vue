<script setup lang="ts">
/**
 * Page: Custom Command
 *
 * Provides a textarea for raw FFmpeg parameters.
 * Uses the standard command preview pipeline via build_command_preview.
 * Custom command has highest priority and overrides all other settings.
 */

import { computed, onMounted } from "vue"
import { useI18n } from "vue-i18n"
import { useGlobalConfig } from "../composables/useGlobalConfig"
import { useCommandPreview } from "../composables/useCommandPreview"
import CommandPreview from "../components/config/CommandPreview.vue"

const { t } = useI18n()

const { customCommand, activeMode, toTaskConfig } = useGlobalConfig()

const configRef = computed(() => toTaskConfig())
const { commandText, errors, warnings, validating } = useCommandPreview(configRef)

onMounted(() => {
  activeMode.value = "custom"
})
</script>

<template>
  <div class="flex flex-1 flex-col gap-4 p-4 overflow-y-auto">
    <h1 class="text-xl font-bold">{{ t("custom.title") }}</h1>
    <p class="text-xs text-base-content/60">
      {{ t("custom.description") }}
    </p>
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
    <div class="card bg-base-200 shadow-sm">
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
