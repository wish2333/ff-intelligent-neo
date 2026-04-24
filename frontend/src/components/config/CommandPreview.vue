<script setup lang="ts">
/**
 * Command preview display with validation results.
 *
 * Shows the generated FFmpeg command in a read-only text area
 * and displays any validation errors/warnings below it.
 */

import { useI18n } from "vue-i18n"

const { t } = useI18n()

defineProps<{
  commandText: string
  errors: string[]
  warnings: string[]
  validating: boolean
}>()

function copyCommand() {
  const text = document.getElementById("command-preview-text")?.textContent
  if (text) {
    navigator.clipboard.writeText(text).catch(() => {
      // Fallback: select text for manual copy
    })
  }
}
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <div class="flex items-center justify-between mb-2">
        <h2 class="card-title text-sm font-semibold">{{ t("config.commandPreview.title") }}</h2>
        <button
          class="btn btn-ghost btn-xs"
          @click="copyCommand"
          :disabled="!commandText"
        >
          {{ t("config.commandPreview.copy") }}
        </button>
      </div>

      <!-- Command text -->
      <div
        class="relative rounded bg-base-300 p-3 font-mono text-xs overflow-x-auto whitespace-pre-wrap break-all min-h-[3rem]"
      >
        <span v-if="validating" class="loading loading-spinner loading-xs mr-2"></span>
        <span v-if="validating" class="text-base-content/50">{{ t("config.commandPreview.updating") }}</span>
        <span v-else-if="commandText" id="command-preview-text">{{ commandText }}</span>
        <span v-else class="text-base-content/50">
          {{ t("config.commandPreview.noConfig") }}
        </span>
      </div>

      <!-- Validation results -->
      <div v-if="errors.length > 0 || warnings.length > 0" class="mt-3 space-y-1">
        <!-- Errors -->
        <div
          v-for="(err, idx) in errors"
          :key="'err-' + idx"
          class="alert alert-error py-1 px-3 text-xs"
        >
          <span>{{ err }}</span>
        </div>

        <!-- Warnings -->
        <div
          v-for="(warn, idx) in warnings"
          :key="'warn-' + idx"
          class="alert alert-warning py-1 px-3 text-xs"
        >
          <span>{{ warn }}</span>
        </div>
      </div>

      <!-- Validation summary -->
      <div
        v-else-if="commandText && !validating"
        class="text-xs text-success mt-1"
      >
        {{ t("config.commandPreview.validationOk") }}
      </div>
    </div>
  </div>
</template>
