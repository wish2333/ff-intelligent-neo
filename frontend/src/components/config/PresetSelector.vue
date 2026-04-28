<script setup lang="ts">
/**
 * Preset selector with save/delete buttons.
 *
 * Dropdown to select from available presets, with buttons
 * to save current config or delete the selected preset.
 */

import { onUnmounted, ref, computed, onMounted } from "vue"
import { useI18n } from "vue-i18n"
import { call } from "../../bridge"
import type { PresetDTO } from "../../types/preset"

const { t } = useI18n()
let alertTimer: ReturnType<typeof setTimeout> | null = null
onUnmounted(() => { if (alertTimer) clearTimeout(alertTimer) })

const emit = defineEmits<{
  (e: "select", preset: PresetDTO): void
  (e: "save"): void
}>()

const presets = ref<PresetDTO[]>([])
const loading = ref(false)
const selectedId = ref("")
const alertMessage = ref("")
const confirmDialog = ref<HTMLDialogElement | null>(null)
const pendingDeleteId = ref("")

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
  } catch (err) {
    alertMessage.value = t("common.operationFailed") + ": " + (err as Error).message
    if (alertTimer) clearTimeout(alertTimer)
    alertTimer = setTimeout(() => { alertMessage.value = "" }, 3000)
  } finally {
    loading.value = false
  }
}

function handleSelect() {
  if (selectedPreset.value) {
    emit("select", selectedPreset.value)
  }
}

function requestDelete() {
  if (!selectedPreset.value || !canDelete.value) return
  pendingDeleteId.value = selectedPreset.value.id
  confirmDialog.value?.showModal()
}

async function confirmDelete() {
  confirmDialog.value?.close()
  if (!pendingDeleteId.value) return
  const res = await call<null>("delete_preset", pendingDeleteId.value)
  if (res.success) {
    selectedId.value = ""
    pendingDeleteId.value = ""
    await fetchPresets()
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
  <div class="card bg-base-200 shadow-sm border border-base-300">
    <div class="card-body p-4">
      <div v-if="alertMessage" class="alert alert-error py-1 px-3 text-xs mb-2">{{ alertMessage }}</div>
      <h2 class="card-title text-sm font-semibold mb-2">
        {{ t("config.preset.title") }}
        <span v-if="loading" class="loading loading-spinner loading-xs"></span>
      </h2>

      <!-- Preset dropdown -->
      <div class="flex items-center gap-2 mb-2">
        <select
          v-model="selectedId"
          @change="handleSelect"
          class="select select-bordered select-sm flex-1"
          :disabled="loading"
        >
          <option value="" disabled>{{ t("config.preset.selectPreset") }}</option>
          <optgroup
            v-if="groupPresets(presets).defaults.length"
            :label="t('config.preset.builtIn')"
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
            :label="t('config.preset.custom')"
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
        <slot name="dropdown-actions" />
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
          {{ t("config.preset.saveAsPreset") }}
        </button>
        <button
          class="btn btn-ghost btn-sm btn-error"
          :disabled="!canDelete"
          @click="requestDelete"
        >
          {{ t("config.preset.delete") }}
        </button>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <dialog ref="confirmDialog" class="modal">
      <div class="modal-box">
        <h3 class="font-bold text-lg">{{ t("common.delete") }}</h3>
        <p class="py-4">{{ t("common.deletePresetConfirm", { name: selectedPreset?.name || "" }) }}</p>
        <div class="modal-action">
          <button class="btn btn-ghost" @click="confirmDialog?.close()">{{ t("common.cancel") }}</button>
          <button class="btn btn-error" @click="confirmDelete()">{{ t("common.confirm") }}</button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop"><button>close</button></form>
    </dialog>
  </div>
</template>
