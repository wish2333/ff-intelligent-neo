<script setup lang="ts">
import { ref, computed, inject, type Ref } from "vue";
import type { PresetDTO } from "../composables/usePresets";

const emit = defineEmits<{
  presetSelected: [presetId: string];
}>();

const presets = inject<ReturnType<typeof import("../composables/usePresets").usePresets>>("presets")!;

const showModal = ref(false);
const editMode = ref(false);
const editName = ref("");
const editDescription = ref("");
const editExtension = ref("");
const editCommand = ref("");

const commandPreview = computed(() => {
  const p = presets.currentPreset();
  if (!p) return "";
  return p.command_template
    .replace("{input}", "input.mp4")
    .replace("{output}", "output.mp4");
});

function openNewPreset() {
  editMode.value = false;
  editName.value = "";
  editDescription.value = "";
  editExtension.value = ".mp4";
  editCommand.value = "-i {input} -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k {output}";
  showModal.value = true;
}

function openEditPreset() {
  const p = presets.currentPreset();
  if (!p || p.is_default) return;
  editMode.value = true;
  editName.value = p.name;
  editDescription.value = p.description;
  editExtension.value = p.output_extension;
  editCommand.value = p.command_template;
  showModal.value = true;
}

function generateId(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    + "-custom";
}

async function handleSave() {
  const id = editMode.value ? presets.currentPresetId.value : generateId(editName.value);
  if (!editName.value.trim() || !editCommand.value.trim()) return;

  await presets.savePreset({
    id,
    name: editName.value.trim(),
    description: editDescription.value.trim(),
    output_extension: editExtension.value.trim() || ".mp4",
    command_template: editCommand.value.trim(),
  });
  showModal.value = false;
}

async function handleDelete() {
  const p = presets.currentPreset();
  if (!p || p.is_default) return;
  await presets.deletePreset(p.id);
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 border-b border-base-300 px-4 py-2">
    <select
      v-model="presets.currentPresetId.value"
      class="select select-bordered select-sm w-56"
      @change="emit('presetSelected', presets.currentPresetId.value)"
    >
      <option
        v-for="p in presets.presets.value"
        :key="p.id"
        :value="p.id"
      >
        {{ p.name }}
      </option>
    </select>

    <button
      class="btn btn-ghost btn-sm"
      @click="openEditPreset"
      :disabled="!presets.currentPreset() || presets.currentPreset()!.is_default"
    >
      Edit
    </button>
    <button
      class="btn btn-ghost btn-sm"
      @click="handleDelete"
      :disabled="!presets.currentPreset() || presets.currentPreset()!.is_default"
    >
      Delete
    </button>
    <button class="btn btn-ghost btn-sm" @click="openNewPreset">
      + New
    </button>

    <div class="badge badge-ghost badge-sm ml-auto text-base-content/50">
      {{ commandPreview }}
    </div>
  </div>

  <!-- Modal -->
  <dialog class="modal" :class="{ 'modal-open': showModal }">
    <div class="modal-box">
      <h3 class="text-lg font-bold">{{ editMode ? "Edit Preset" : "New Preset" }}</h3>

      <div class="py-4 flex flex-col gap-3">
        <label class="form-control w-full">
          <div class="label"><span class="label-text">Name</span></div>
          <input v-model="editName" type="text" placeholder="Preset name" class="input input-bordered input-sm w-full" />
        </label>

        <label class="form-control w-full">
          <div class="label"><span class="label-text">Description</span></div>
          <input v-model="editDescription" type="text" placeholder="Optional description" class="input input-bordered input-sm w-full" />
        </label>

        <label class="form-control w-full">
          <div class="label"><span class="label-text">Output Extension</span></div>
          <input v-model="editExtension" type="text" placeholder=".mp4" class="input input-bordered input-sm w-full" />
        </label>

        <label class="form-control w-full">
          <div class="label"><span class="label-text">Command Template</span></div>
          <textarea
            v-model="editCommand"
            class="textarea textarea-bordered textarea-sm font-mono w-full"
            rows="3"
            placeholder="-i {input} -c:v libx264 -preset fast -crf 23 {output}"
          ></textarea>
          <div class="label"><span class="label-text-alt">Use {input} and {output} as placeholders</span></div>
        </label>
      </div>

      <div class="modal-action">
        <button class="btn btn-ghost btn-sm" @click="showModal = false">Cancel</button>
        <button class="btn btn-primary btn-sm" @click="handleSave" :disabled="!editName.trim() || !editCommand.trim()">
          Save
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="showModal = false">close</button>
    </form>
  </dialog>
</template>
