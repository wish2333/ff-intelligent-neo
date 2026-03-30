import { ref } from "vue";
import { call } from "../bridge";

export interface FileItemDTO {
  path: string;
  name: string;
  size_bytes: number;
  duration_seconds: number;
  video_codec: string;
  audio_codec: string;
  width: number;
  height: number;
  format_name: string;
}

export function useFileQueue() {
  const files = ref<FileItemDTO[]>([]);
  const selectedIndices = ref<Set<number>>(new Set());

  async function addFiles(paths: string[]) {
    const res = await call<{ files: FileItemDTO[]; added: number }>("add_files", paths);
    if (res.success && res.data) {
      files.value = res.data.files;
    }
  }

  async function removeSelected() {
    const indices = Array.from(selectedIndices.value).sort((a, b) => b - a);
    if (indices.length === 0) return;
    const res = await call<FileItemDTO[]>("remove_files", indices);
    if (res.success && res.data) {
      files.value = res.data;
    }
    selectedIndices.value.clear();
  }

  async function clearFiles() {
    await call<null>("clear_files");
    files.value = [];
    selectedIndices.value.clear();
  }

  async function refreshFiles() {
    const res = await call<FileItemDTO[]>("get_files");
    if (res.success && res.data) {
      files.value = res.data;
    }
  }

  function toggleSelect(index: number, shiftKey: boolean, ctrlKey: boolean) {
    if (shiftKey && selectedIndices.value.size > 0) {
      const last = Math.max(...selectedIndices.value);
      const start = Math.min(last, index);
      const end = Math.max(last, index);
      for (let i = start; i <= end; i++) {
        selectedIndices.value.add(i);
      }
    } else if (ctrlKey) {
      if (selectedIndices.value.has(index)) {
        selectedIndices.value.delete(index);
      } else {
        selectedIndices.value.add(index);
      }
    } else {
      selectedIndices.value.clear();
      selectedIndices.value.add(index);
    }
    // trigger reactivity
    selectedIndices.value = new Set(selectedIndices.value);
  }

  return {
    files,
    selectedIndices,
    addFiles,
    removeSelected,
    clearFiles,
    refreshFiles,
    toggleSelect,
  };
}
