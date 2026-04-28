/**
 * Preset CRUD composable.
 *
 * Loads presets from backend, provides save/delete/load operations.
 */

import { ref } from "vue"
import { call } from "../bridge"
import type { PresetDTO } from "../types/preset"
import type { TaskConfigDTO } from "../types/config"

export function usePresets() {
  const presets = ref<PresetDTO[]>([])
  const loading = ref(false)
  const error = ref("")

  async function fetchPresets() {
    loading.value = true
    error.value = ""
    try {
      const res = await call<PresetDTO[]>("get_presets")
      if (res.success && res.data) {
        presets.value = res.data
      } else {
        error.value = res.error || "Failed to load presets"
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : "Failed to load presets"
    } finally {
      loading.value = false
    }
  }

  async function savePreset(preset: {
    id?: string
    name: string
    description: string
    config: TaskConfigDTO
  }): Promise<PresetDTO | null> {
    loading.value = true
    error.value = ""
    try {
      const res = await call<PresetDTO>("save_preset", preset)
      if (res.success && res.data) {
        await fetchPresets()
        return res.data
      }
      error.value = res.error || "Failed to save preset"
      return null
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : "Failed to save preset"
      return null
    } finally {
      loading.value = false
    }
  }

  async function deletePreset(presetId: string): Promise<boolean> {
    loading.value = true
    error.value = ""
    try {
      const res = await call<null>("delete_preset", presetId)
      if (res.success) {
        await fetchPresets()
        return true
      }
      error.value = res.error || "Failed to delete preset"
      return false
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : "Failed to delete preset"
      return false
    } finally {
      loading.value = false
    }
  }

  function getPresetConfig(presetId: string): TaskConfigDTO | null {
    const preset = presets.value.find((p) => p.id === presetId)
    return preset?.config ?? null
  }

  return {
    presets,
    loading,
    error,
    fetchPresets,
    savePreset,
    deletePreset,
    getPresetConfig,
  }
}
