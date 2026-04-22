<script setup lang="ts">
/**
 * Preset selector with save/delete buttons.
 *
 * Dropdown to select from available presets, with buttons
 * to save current config or delete the selected preset.
 */

import { ref, computed, onMounted } from "vue"
import { call } from "../../bridge"
import type { PresetDTO } from "../../types/preset"

const emit = defineEmits<{
  (e: "select", preset: PresetDTO): void
  (e: "save"): void
}>()

const presets = ref<PresetDTO[]>([])
const loading = ref(false)
const selectedId = ref("")

const selectedPreset = computed(() => {
  return presets.value.find((p) => p.id === selectedId.value) || null
})

const canDelete = computed(() => {
  if (!selectedPreset.value) return false
  return !selectedPreset.value.is_default
})

async function fetchPresets() {
  loading.value = true
  try {
    const res = await call<PresetDTO[]>("get_presets")
    if (res.success && res.data) {
      presets.value = res.data
    }
  } catch {
    // silently fail
  } finally {
    loading.value = false
  }
}

function handleSelect() {
  if (selectedPreset.value) {
    emit("select", selectedPreset.value)
  }
}

async function handleDelete() {
  if (!selectedPreset.value || !canDelete.value) return
  if (confirm(`Delete preset "${selectedPreset.value.name}"?`)) {
    const res = await call<null>("delete_preset", selectedPreset.value.id)
    if (res.success) {
      selectedId.value = ""
      await fetchPresets()
    }
  }
}

function groupPresets(presetList: PresetDTO[]) {
  const defaults = presetList.filter((p) => p.is_default)
  const users = presetList.filter((p) => !p.is_default)
  return { defaults, users }
}

onMounted(fetchPresets)

defineExpose({ fetchPresets, setSelectedId: (id: string) => { selectedId.value = id } })
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title text-sm font-semibold mb-2">Presets</h2>

      <!-- Preset dropdown -->
      <div class="flex gap-2 mb-2">
        <select
          v-model="selectedId"
          @change="handleSelect"
          class="select select-bordered select-sm flex-1"
        >
          <option value="" disabled>-- Select Preset --</option>
          <optgroup
            v-if="groupPresets(presets).defaults.length"
            label="Built-in"
          >
            <option
              v-for="p in groupPresets(presets).defaults"
              :key="p.id"
              :value="p.id"
            >
              {{ p.name }}
            </option>
          </optgroup>
          <optgroup
            v-if="groupPresets(presets).users.length"
            label="Custom"
          >
            <option
              v-for="p in groupPresets(presets).users"
              :key="p.id"
              :value="p.id"
            >
              {{ p.name }}
            </option>
          </optgroup>
        </select>
      </div>

      <!-- Selected preset description -->
      <div
        v-if="selectedPreset"
        class="text-xs text-base-content/60 mb-2"
      >
        {{ selectedPreset.description }}
      </div>

      <!-- Action buttons -->
      <div class="flex gap-2">
        <button
          class="btn btn-primary btn-sm flex-1"
          @click="$emit('save')"
        >
          Save as Preset
        </button>
        <button
          class="btn btn-ghost btn-sm btn-error"
          :disabled="!canDelete"
          @click="handleDelete"
        >
          Delete
        </button>
      </div>
    </div>
  </div>
</template>
