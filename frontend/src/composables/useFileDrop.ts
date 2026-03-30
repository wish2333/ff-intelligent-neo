import { ref, onMounted, onUnmounted } from "vue";

export function useFileDrop(onFilesDropped: (paths: string[]) => void) {
  const isDragging = ref(false);
  let dragCounter = 0;

  function onDragEnter(e: DragEvent) {
    e.preventDefault();
    dragCounter++;
    isDragging.value = true;
  }

  function onDragOver(e: DragEvent) {
    e.preventDefault();
  }

  function onDragLeave() {
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      isDragging.value = false;
    }
  }

  async function onDrop(e: DragEvent) {
    e.preventDefault();
    dragCounter = 0;
    isDragging.value = false;

    // Poll Python backend for file paths (pywebview processes drop asynchronously)
    const api = (window as any).pywebview?.api;
    if (!api) return;

    for (let attempt = 0; attempt < 30; attempt++) {
      try {
        const result = await api.get_dropped_files();
        if (result.success && result.data && result.data.length > 0) {
          onFilesDropped(result.data);
          return;
        }
      } catch {
        // bridge not ready yet
      }
      await new Promise((r) => setTimeout(r, 100));
    }
  }

  onMounted(() => {
    window.addEventListener("dragenter", onDragEnter);
    window.addEventListener("dragover", onDragOver);
    window.addEventListener("dragleave", onDragLeave);
    window.addEventListener("drop", onDrop);
  });

  onUnmounted(() => {
    window.removeEventListener("dragenter", onDragEnter);
    window.removeEventListener("dragover", onDragOver);
    window.removeEventListener("dragleave", onDragLeave);
    window.removeEventListener("drop", onDrop);
  });

  return { isDragging };
}
