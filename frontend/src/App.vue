<script setup lang="ts">
import { ref, onMounted, provide } from "vue";
import { call, waitForPyWebView } from "./bridge";

// IMMEDIATE log to verify this script executes
console.log("[App.vue] ✅ Script setup BEGINNING");
import { useFileDrop } from "./composables/useFileDrop";
import { useFileQueue } from "./composables/useFileQueue";
import { usePresets } from "./composables/usePresets";
import { useBatchProcess } from "./composables/useBatchProcess";
import Navbar from "./components/Navbar.vue";
import FileDropZone from "./components/FileDropZone.vue";
import Toolbar from "./components/Toolbar.vue";
import FileList from "./components/FileList.vue";
import PresetPanel from "./components/PresetPanel.vue";
import BatchControls from "./components/BatchControls.vue";
import ProgressPanel from "./components/ProgressPanel.vue";
import SettingsModal from "./components/SettingsModal.vue";

const ffmpegReady = ref(false);
const ffmpegVersion = ref("");
const showSettings = ref(false);
const appInfo = ref<import("./components/SettingsModal.vue").AppInfo | null>(null);

const {
  files,
  selectedIndices,
  addFiles,
  removeSelected,
  clearFiles,
  toggleSelect,
} = useFileQueue();

const presets = usePresets();
const batchProcess = useBatchProcess();
const { processing, taskProgressMap, reset: resetBatchProcess, setProcessing } = batchProcess;

// Provide shared state to children
provide("presets", presets);
provide("batchProcess", batchProcess);

const { isDragging } = useFileDrop(async (paths: string[]) => {
  await addFiles(paths);
});

onMounted(async () => {
  console.log("[App] onMounted - waiting for PyWebView");
  await waitForPyWebView();
  console.log("[App] PyWebView ready");

  // Debug: Listen to ALL pywebvue events to verify event system
  window.addEventListener('pywebvue:task_start', (e) => console.log('[App] GLOBAL task_start:', e.detail));
  window.addEventListener('pywebvue:batch_progress', (e) => console.log('[App] GLOBAL batch_progress:', e.detail));
  window.addEventListener('pywebvue:task_progress', (e) => console.log('[App] GLOBAL task_progress:', e.detail));
  window.addEventListener('pywebvue:task_complete', (e) => console.log('[App] GLOBAL task_complete:', e.detail));
  window.addEventListener('pywebvue:task_error', (e) => console.log('[App] GLOBAL task_error:', e.detail));
  window.addEventListener('pywebvue:batch_complete', (e) => console.log('[App] GLOBAL batch_complete:', e.detail));
  window.addEventListener('pywebvue:log_line', (e) => console.log('[App] GLOBAL log_line:', e.detail));

  // Setup FFmpeg (critical)
  console.log("[App] Calling setup_ffmpeg...");
  const setupRes = await call<{ ready: boolean; ffmpeg_path: string }>("setup_ffmpeg");
  console.log("[App] setup_ffmpeg result:", setupRes);
  if (setupRes.success && setupRes.data) {
    ffmpegReady.value = setupRes.data.ready;
    console.log("[App] ffmpegReady set to:", ffmpegReady.value);
  }

  // Load presets (critical, don't block on get_app_info)
  console.log("[App] Loading presets...");
  await presets.loadPresets();
  console.log("[App] Presets loaded, count:", presets.presets.value.length);

  // Get app info (non-critical, fire-and-forget)
  console.log("[App] Getting app info...");
  call<import("./components/SettingsModal.vue").AppInfo>("get_app_info")
    .then((infoRes) => {
      console.log("[App] get_app_info result:", infoRes);
      if (infoRes.success && infoRes.data) {
        appInfo.value = infoRes.data;
        ffmpegVersion.value = infoRes.data.ffmpeg_version ?? "";
      } else {
        const errorMsg = infoRes.error || "Failed to get app info (empty response)";
        console.error("[get_app_info] error:", errorMsg);
        // Set a minimal default to avoid infinite loading state in SettingsModal
        appInfo.value = {
          app_name: "FF Intelligent",
          app_version: "unknown",
          python_version: "",
          ffmpeg_path: "",
          ffmpeg_version: null,
          ffprobe_path: "",
          ffprobe_version: null,
          is_packaged: false,
        };
      }
    })
    .catch((e) => {
      console.error("[get_app_info] exception:", e);
      // Set a minimal default to avoid infinite loading state
      appInfo.value = {
        app_name: "FF Intelligent",
        app_version: "unknown",
        python_version: "",
        ffmpeg_path: "",
        ffmpeg_version: null,
        ffprobe_path: "",
        ffprobe_version: null,
        is_packaged: false,
      };
    });
});

function handleFilesAdded(paths: string[]) {
  addFiles(paths);
}

function handleClearAll() {
  clearFiles();
}

function handleRemoveSelected() {
  removeSelected();
}

async function handleStartBatch(presetId: string, outputDir: string, maxWorkers: number) {
  console.log("[App] handleStartBatch called", { presetId, outputDir, maxWorkers });
  // Reset progress state before starting new batch
  resetBatchProcess();
  const res = await call<null>("start_batch", presetId, outputDir, maxWorkers);
  if (!res.success) {
    console.error("[App] start_batch failed:", res.error);
    // If start_batch fails, ensure processing is reset
    // Note: resetBatchProcess already set processing to false
  } else {
    console.log("[App] start_batch succeeded, forcing processing=true as fallback");
    // Manually set processing=true as a fallback in case task_start event is missed
    setProcessing(true);
  }
}

function handleCancelBatch() {
  call("cancel_batch");
}

function handleOpenSettings() {
  showSettings.value = true;
}

function handleCloseSettings() {
  showSettings.value = false;
}
</script>

<template>
  <div class="flex h-screen flex-col bg-base-100 text-base-content">
    <Navbar
      :ffmpeg-ready="ffmpegReady"
      :ffmpeg-version="ffmpegVersion"
      @open-settings="handleOpenSettings"
    />

    <Toolbar @files-added="handleFilesAdded" @clear-all="handleClearAll" @remove-selected="handleRemoveSelected" />

    <PresetPanel />

    <FileList
      :files="files"
      :selected-indices="selectedIndices"
      :task-progress-map="taskProgressMap"
      @toggle="toggleSelect"
    />

    <BatchControls
      :processing="processing"
      :has-files="files.length > 0"
      @start="handleStartBatch"
      @cancel="handleCancelBatch"
    />

    <ProgressPanel />

    <FileDropZone :dragging="isDragging" />

    <SettingsModal
      :visible="showSettings"
      :app-info="appInfo"
      @close="handleCloseSettings"
    />
  </div>
</template>
