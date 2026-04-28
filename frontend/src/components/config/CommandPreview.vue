<script setup lang="ts">
/**
 * Command preview display with validation results.
 *
 * Shows the generated FFmpeg command in a read-only text area
 * and displays any validation errors/warnings below it.
 */

import { onUnmounted, ref } from "vue"
import { useI18n } from "vue-i18n"

const { t } = useI18n()
let copyTimer: ReturnType<typeof setTimeout> | null = null
onUnmounted(() => { if (copyTimer) clearTimeout(copyTimer) })

interface ValidationItem {
  param: string
  message: string
}

defineProps<{
  commandText: string
  errors: ValidationItem[]
  warnings: ValidationItem[]
  validating: boolean
  type?: "ffmpeg" | "auto-editor"
}>()

const copied = ref(false)

function copyCommand(commandText: string) {
  if (!commandText) return
  const fallback = () => {
    const textarea = document.createElement("textarea")
    textarea.value = commandText
    textarea.style.position = "fixed"
    textarea.style.opacity = "0"
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand("copy")
    document.body.removeChild(textarea)
    showCopied()
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(commandText).then(showCopied).catch(fallback)
  } else {
    fallback()
  }
}

function showCopied() {
  copied.value = true
  if (copyTimer) clearTimeout(copyTimer)
  copyTimer = setTimeout(() => { copied.value = false }, 1500)
}

function formatItem(item: ValidationItem): string {
  return item.param ? `${item.param}: ${item.message}` : item.message
}
</script>

<template>
  <div class="card bg-base-200 shadow-sm border border-base-300">
    <div class="card-body px-4 py-3">
      <div class="flex items-center justify-between mb-1">
        <h2 class="card-title text-sm font-semibold">{{ t("config.commandPreview.title") }}</h2>
        <button
          class="btn btn-ghost btn-xs"
          @click="copyCommand(commandText)"
          :disabled="!commandText"
        >
          <span v-if="copied">{{ t("common.copied") }}</span>
          <span v-else>{{ t("config.commandPreview.copy") }}</span>
        </button>
      </div>

      <!-- Command text -->
      <div
        class="relative rounded bg-base-300 px-3 py-2 font-mono text-xs overflow-x-auto whitespace-pre-wrap break-all min-h-[2.5rem]"
      >
        <!-- Keep existing command while validating to avoid flash -->
        <span v-if="commandText">{{ commandText }}</span>
        <span v-else class="text-base-content/30 font-mono">{{ type === 'auto-editor' ? 'auto-editor' : 'ffmpeg' }}</span>
        <!-- Small inline spinner during validation -->
        <span
          v-if="validating"
          class="absolute top-2 right-2 loading loading-spinner loading-xs text-base-content/40"
        ></span>
      </div>

      <!-- Validation results: always reserve space to prevent layout shift -->
      <div class="mt-2 min-h-[2rem]">
        <div v-if="errors.length > 0 || warnings.length > 0" class="space-y-1">
          <!-- Errors -->
          <div
            v-for="(err, idx) in errors"
            :key="'err-' + idx"
            class="alert alert-error py-1 px-3 text-xs"
          >
            <span>{{ formatItem(err) }}</span>
          </div>

          <!-- Warnings -->
          <div
            v-for="(warn, idx) in warnings"
            :key="'warn-' + idx"
            class="alert alert-warning py-1 px-3 text-xs"
          >
            <span>{{ formatItem(warn) }}</span>
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
  </div>
</template>
