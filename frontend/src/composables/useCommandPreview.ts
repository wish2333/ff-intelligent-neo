/**
 * FFmpeg command preview and parameter validation.
 *
 * Debounces config changes and updates the preview command + validation
 * results by calling the merged preview_command backend API.
 *
 * v2.1.1: Single IPC call (preview_command), race condition protection,
 * in-flight guard, removed deep:true watch.
 */

import { ref, watch, onScopeDispose, type Ref } from "vue"
import { call } from "../bridge"
import type { TaskConfigDTO } from "../types/config"

interface ValidationItem {
  param: string
  message: string
}

interface PreviewResult {
  command: string
  errors: ValidationItem[]
  warnings: ValidationItem[]
}

export function useCommandPreview(configRef: Ref<TaskConfigDTO>) {
  const commandText = ref("")
  const errors = ref<ValidationItem[]>([])
  const warnings = ref<ValidationItem[]>([])
  const validating = ref(false)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  let requestId = 0
  let pendingUpdate = false
  let validatingFlag = false

  async function updatePreview() {
    validatingFlag = true
    validating.value = true
    const myId = ++requestId
    try {
      const config = configRef.value
      const res = await call<PreviewResult>("preview_command", config)

      // Discard stale responses
      if (myId !== requestId) return

      if (res.success && res.data) {
        commandText.value = res.data.command
        errors.value = res.data.errors
        warnings.value = res.data.warnings
      } else {
        commandText.value = ""
        errors.value = res.error ? [{ param: "", message: res.error }] : []
        warnings.value = []
      }
    } catch {
      if (myId !== requestId) return
      commandText.value = ""
      errors.value = [{ param: "", message: "Failed to generate preview" }]
      warnings.value = []
    } finally {
      validatingFlag = false
      validating.value = false
      // If a config change arrived while we were validating, schedule another update
      if (pendingUpdate) {
        pendingUpdate = false
        scheduleUpdate()
      }
    }
  }

  function scheduleUpdate() {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }
    // If a request is in-flight, mark pending instead of scheduling
    if (validatingFlag) {
      pendingUpdate = true
      return
    }
    debounceTimer = setTimeout(updatePreview, 500)
  }

  // Watch config changes without deep:true (configRef is computed, Vue tracks deps)
  watch(configRef, scheduleUpdate, { immediate: true })

  onScopeDispose(() => {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    requestId += 1
    validatingFlag = false
  })

  return {
    commandText,
    errors,
    warnings,
    validating,
    updatePreview,
  }
}
