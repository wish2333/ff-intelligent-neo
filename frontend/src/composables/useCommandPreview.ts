/**
 * FFmpeg command preview and parameter validation.
 *
 * Debounces config changes and updates the preview command + validation
 * results by calling the backend build_command / validate_config APIs.
 */

import { ref, watch, type Ref } from "vue"
import { call } from "../bridge"
import type { TaskConfigDTO } from "../types/config"

export function useCommandPreview(configRef: Ref<TaskConfigDTO>) {
  const commandText = ref("")
  const errors = ref<string[]>([])
  const warnings = ref<string[]>([])
  const validating = ref(false)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  async function updatePreview() {
    validating.value = true
    try {
      const config = configRef.value

      // Run validation and preview in parallel
      const [valRes, cmdRes] = await Promise.all([
        call<{ errors: string[]; warnings: string[] }>("validate_config", config),
        call<string>("build_command", config),
      ])

      if (valRes.success && valRes.data) {
        errors.value = valRes.data.errors
        warnings.value = valRes.data.warnings
      } else {
        errors.value = valRes.error ? [valRes.error] : []
        warnings.value = []
      }

      if (cmdRes.success && cmdRes.data) {
        commandText.value = cmdRes.data
      } else {
        commandText.value = ""
      }
    } catch {
      commandText.value = ""
      errors.value = ["Failed to generate preview"]
      warnings.value = []
    } finally {
      validating.value = false
    }
  }

  function scheduleUpdate() {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }
    debounceTimer = setTimeout(updatePreview, 300)
  }

  // Watch for config changes with deep observation
  watch(configRef, scheduleUpdate, { deep: true, immediate: true })

  return {
    commandText,
    errors,
    warnings,
    validating,
    updatePreview,
  }
}
