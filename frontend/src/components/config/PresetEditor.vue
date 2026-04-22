<script setup lang="ts">
/**
 * Preset editor dialog.
 *
 * Modal dialog for creating or editing a preset with name
 * and description fields.
 */

import { ref, watch } from "vue"

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
      <h3 class="font-bold text-lg mb-4">Save Preset</h3>

      <!-- Name -->
      <div class="form-control mb-4">
        <label class="label">
          <span class="label-text">Preset Name</span>
        </label>
        <input
          v-model="name"
          type="text"
          placeholder="e.g. My Custom H.264"
          class="input input-bordered w-full"
          @keydown.enter="handleSave"
        />
      </div>

      <!-- Description -->
      <div class="form-control mb-4">
        <label class="label">
          <span class="label-text">Description (optional)</span>
        </label>
        <textarea
          v-model="description"
          class="textarea textarea-bordered w-full h-20"
          placeholder="Brief description of this preset..."
        ></textarea>
      </div>

      <!-- Actions -->
      <div class="modal-action">
        <button class="btn btn-ghost" @click="handleClose">Cancel</button>
        <button
          class="btn btn-primary"
          :disabled="!name.trim()"
          @click="handleSave"
        >
          Save
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button>close</button>
    </form>
  </dialog>
</template>
