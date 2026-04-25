<script setup lang="ts">
/**
 * Preset editor dialog.
 *
 * Modal dialog for creating or editing a preset with name
 * and description fields.
 */

import { ref, watch } from "vue"
import { useI18n } from "vue-i18n"

const { t } = useI18n()

const props = defineProps<{
  open: boolean
  presetName?: string
  presetDescription?: string
}>()

const emit = defineEmits<{
  (e: "save", data: { name: string; description: string }): void
  (e: "close"): void
}>()

const name = ref("")
const description = ref("")

watch(
  () => props.open,
  (val) => {
    if (val) {
      name.value = props.presetName || ""
      description.value = props.presetDescription || ""
    }
  }
)

function handleSave() {
  if (!name.value.trim()) return
  emit("save", {
    name: name.value.trim(),
    description: description.value.trim(),
  })
}

function handleClose() {
  emit("close")
}
</script>

<template>
  <dialog
    :class="{ 'modal': true, 'modal-open': open }"
    @close="handleClose"
  >
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-4">{{ t("config.presetEditor.title") }}</h3>

      <!-- Name -->
      <div class="form-control mb-4">
        <label class="label">
          <span class="label-text">{{ t("config.presetEditor.name") }}</span>
        </label>
        <input
          v-model="name"
          type="text"
          :placeholder="t('config.presetEditor.namePlaceholder')"
          class="input input-bordered w-full"
          @keydown.enter="handleSave"
        />
      </div>

      <!-- Description -->
      <div class="form-control mb-4">
        <label class="label">
          <span class="label-text">{{ t("config.presetEditor.description") }}</span>
        </label>
        <textarea
          v-model="description"
          class="textarea textarea-bordered w-full h-20"
          :placeholder="t('config.presetEditor.descriptionPlaceholder')"
        ></textarea>
      </div>

      <!-- Actions -->
      <div class="modal-action">
        <button class="btn btn-ghost" @click="handleClose">{{ t("common.cancel") }}</button>
        <button
          class="btn btn-primary"
          :disabled="!name.trim()"
          @click="handleSave"
        >
          {{ t("common.save") }}
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button>{{ t("common.close") }}</button>
    </form>
  </dialog>
</template>
