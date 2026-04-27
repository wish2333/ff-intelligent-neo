/**
 * Media file probe composable.
 *
 * Manages the lifecycle of a file probe: trigger, loading state,
 * parsed/raw result, display mode toggle, and cleanup.
 */

import { ref, computed } from "vue"
import { call } from "../bridge"
import type { ProbeResult, ProbeDisplayMode } from "../types/probe"

export function useFileProbe() {
  const filePath = ref("")
  const result = ref<ProbeResult | null>(null)
  const loading = ref(false)
  const error = ref("")
  const displayMode = ref<ProbeDisplayMode>("parsed")

  const hasResult = computed(() => result.value !== null)

  async function probe(path: string): Promise<void> {
    if (!path) return
    filePath.value = path
    loading.value = true
    error.value = ""
    result.value = null

    try {
      const res = await call<ProbeResult>("probe_media_file", path)
      if (res.success && res.data) {
        result.value = res.data
      } else {
        error.value = res.error ?? "Probe failed"
      }
    } catch {
      error.value = "Bridge call failed"
    } finally {
      loading.value = false
    }
  }

  function clear(): void {
    filePath.value = ""
    result.value = null
    error.value = ""
    loading.value = false
    displayMode.value = "parsed"
  }

  function toggleMode(): void {
    displayMode.value = displayMode.value === "parsed" ? "raw" : "parsed"
  }

  return {
    filePath,
    result,
    loading,
    error,
    displayMode,
    hasResult,
    probe,
    clear,
    toggleMode,
  }
}
