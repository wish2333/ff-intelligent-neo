<script setup lang="ts">
/**
 * Auto-Editor path configuration component.
 *
 * Allows users to set/select the auto-editor binary path.
 * Validates via --version, displays compatibility status.
 * Mirrors FFmpegSetup.vue style (badge + action buttons).
 *
 * v2.2.0 Phase 5.
 */
import { ref, computed, onMounted, onUnmounted } from "vue"
import { useI18n } from "vue-i18n"
import { call } from "../../bridge"
import { useBridge } from "../../composables/useBridge"
import { EVENT_AUTO_EDITOR_VERSION_CHANGED } from "../../utils/events"
import type { AeStatus } from "../../types/autoEditor"

const props = defineProps<{
  status: AeStatus
  platform: string
}>()

const emit = defineEmits<{
  "select-binary": []
  "set-path": [path: string]
}>()

const { t } = useI18n()
const { on } = useBridge()
const isLoading = ref(false)
const isDownloading = ref(false)
const showConfirm = ref(false)

const isWindows = computed(() => props.platform === "win32")

const statusBadge = computed(() => {
  if (!props.status.available) {
    return { class: "badge-ghost", text: t("settings.autoEditor.notConfigured") }
  }
  if (!props.status.compatible) {
    return {
      class: "badge-warning",
      text: t("settings.autoEditor.versionIncompatible", {
        version: props.status.version,
      }),
    }
  }
  return { class: "badge-success", text: t("settings.autoEditor.ready") }
})

function onVersionChanged(): void {
  isLoading.value = false
  isDownloading.value = false
}

onMounted(() => {
  on(EVENT_AUTO_EDITOR_VERSION_CHANGED, onVersionChanged)
})

onUnmounted(() => {
  // Event cleanup handled by useBridge
})

async function handleSelectBinary(): Promise<void> {
  emit("select-binary")
}

function openConfirmDialog(): void {
  showConfirm.value = true
}

async function handleDownload(): Promise<void> {
  showConfirm.value = false
  isDownloading.value = true
  try {
    const res = await call<{ path: string }>("download_auto_editor")
    if (res.success && res.data?.path) {
      emit("set-path", res.data.path)
    }
  } catch {
    // silently fail
  } finally {
    isDownloading.value = false
  }
}

async function handleAutoDetect(): Promise<void> {
  isLoading.value = true
  try {
    const res = await call<AeStatus>("get_auto_editor_status")
    if (res.success && res.data?.path) {
      emit("set-path", res.data.path)
    }
  } catch {
    // silently fail
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="space-y-3">
    <h3 class="text-lg font-semibold">{{ t("settings.autoEditor.title") }}</h3>

    <!-- Status bar -->
    <div class="flex items-center gap-3">
      <span :class="['badge badge-sm', statusBadge.class]">
        {{ statusBadge.text }}
      </span>
      <span v-if="status.available && status.version" class="text-sm opacity-70">
        v{{ status.version }}
      </span>
    </div>

    <!-- Compatibility warning -->
    <div
      v-if="status.available && !status.compatible"
      class="text-xs text-warning"
    >
      {{ t("settings.autoEditor.versionIncompatible", { version: status.version }) }}
    </div>

    <!-- Actions -->
    <div class="flex flex-wrap gap-2">
      <button
        class="btn btn-xs btn-primary btn-outline"
        :disabled="isLoading"
        @click="handleAutoDetect"
      >
        <span v-if="isLoading" class="loading loading-spinner loading-xs" />
        {{ t("settings.autoEditor.autoDetect") }}
      </button>

      <!-- Windows: download button with confirm dialog -->
      <button
        v-if="isWindows"
        class="btn btn-xs btn-accent btn-outline"
        :disabled="isDownloading"
        @click="openConfirmDialog"
      >
        <span v-if="isDownloading" class="loading loading-spinner loading-xs" />
        {{ t("settings.autoEditor.downloadAutoEditor") }}
      </button>

      <!-- macOS/Linux: external download link -->
      <a
        v-else
        href="https://auto-editor.com/installing"
        target="_blank"
        rel="noopener"
        class="btn btn-xs btn-accent btn-outline"
      >
        {{ t("settings.autoEditor.downloadAutoEditor") }}
      </a>

      <button
        class="btn btn-xs btn-outline"
        @click="handleSelectBinary"
      >
        {{ t("settings.autoEditor.selectBinary") }}
      </button>
    </div>

    <!-- Current path (space reserved to avoid layout shift) -->
    <div class="text-xs space-y-1 min-h-[2.5rem]">
      <template v-if="status.available && status.path">
        <p class="font-medium opacity-60">{{ t("settings.autoEditor.currentPath") }}</p>
        <p class="truncate opacity-50" :title="status.path">{{ status.path }}</p>
      </template>
    </div>

    <!-- Download confirmation modal -->
    <dialog class="modal" :class="{ 'modal-open': showConfirm }">
      <div class="modal-box">
        <h3 class="text-lg font-bold">{{ t("settings.autoEditor.confirmDownload") }}</h3>
        <p class="py-4">
          {{ status.available
            ? t("settings.autoEditor.confirmRedownloadDesc", { version: status.version })
            : t("settings.autoEditor.confirmDownloadDesc")
          }}
        </p>
        <div class="modal-action">
          <button class="btn btn-sm btn-ghost" @click="showConfirm = false">{{ t("common.cancel") }}</button>
          <button class="btn btn-sm btn-accent" @click="handleDownload">{{ t("common.confirm") }}</button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="showConfirm = false">{{ t("common.close") }}</button>
      </form>
    </dialog>
  </div>
</template>
