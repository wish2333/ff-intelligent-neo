import { ref } from "vue";
import { call } from "../bridge";

export interface PresetDTO {
  id: string;
  name: string;
  description: string;
  output_extension: string;
  command_template: string;
  is_default: boolean;
}

export function usePresets() {
  const presets = ref<PresetDTO[]>([]);
  const currentPresetId = ref<string>("");

  async function loadPresets() {
    const res = await call<PresetDTO[]>("get_presets");
    if (res.success && res.data) {
      presets.value = res.data;
      if (presets.value.length > 0) {
        const exists = presets.value.some((p) => p.id === currentPresetId.value);
        if (!exists) {
          currentPresetId.value = presets.value[0].id;
        }
      }
    }
    return res;
  }

  function currentPreset(): PresetDTO | undefined {
    return presets.value.find((p) => p.id === currentPresetId.value);
  }

  async function savePreset(preset: Omit<PresetDTO, "is_default">) {
    const res = await call<PresetDTO>("save_preset", {
      ...preset,
      is_default: false,
    });
    if (res.success) {
      await loadPresets();
    }
    return res;
  }

  async function deletePreset(presetId: string) {
    const res = await call<null>("delete_preset", presetId);
    if (res.success) {
      await loadPresets();
      if (currentPresetId.value === presetId && presets.value.length > 0) {
        currentPresetId.value = presets.value[0].id;
      }
    }
    return res;
  }

  return {
    presets,
    currentPresetId,
    currentPreset,
    loadPresets,
    savePreset,
    deletePreset,
  };
}
