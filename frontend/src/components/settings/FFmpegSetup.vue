<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue"
import type { FfmpegVersionDTO } from "../../composables/useSettings"
import type { FfmpegInstallInfo } from "../../types/settings"
import { useI18n } from "vue-i18n"
import { useBridge } from "../../composables/useBridge"

const props = defineProps<{
  versions: FfmpegVersionDTO[]
  status: "ready" | "not_found" | "detecting"
  currentVersion: string | null
  platform: string
}>()

const emit = defineEmits<{
  detect: []
  selectBinary: []
  switch: [path: string]
  download: []
}>()

const { t } = useI18n()
const { on } = useBridge()
const showConfirm = ref(false)
const isDownloading = ref(false)

const statusBadge = computed(() => {
  switch (props.status) {
    case "ready":
      return { class: "badge-success", text: t("ffmpeg.ready") }
    case "not_found":
      return { class: "badge-error", text: t("ffmpeg.notFound") }
    case "detecting":
      return { class: "badge-warning", text: t("ffmpeg.detecting") }
  }
})

const isWindows = computed(() => props.platform === "win32")
const isMacOS = computed(() => props.platform === "darwin")
const installInfo = ref<FfmpegInstallInfo | null>(null)

function onFfmpegVersionChanged(detail: unknown) {
  const payload = detail as Record<string, unknown>
  if (typeof payload.status === "string") {
    isDownloading.value = false
  }
}

onMounted(() => {
  on("ffmpeg_version_changed", onFfmpegVersionChanged)
})

onUnmounted(() => {
  // Event cleanup handled by useBridge
})

async function handleDownload(): Promise<void> {
  if (!isWindows.value && !isMacOS.value) {
    const res = await (await import("../../bridge")).call<{ platform: string; instructions: FfmpegInstallInfo }>("download_ffmpeg")
    if (res.success && res.data?.instructions) {
      installInfo.value = res.data.instructions
    }
    return
  }
  showConfirm.value = false
  isDownloading.value = true
  emit("download")
}
</script>

<template>
  <div class="space-y-3">
    <h3 class="text-lg font-semibold">{{ t("ffmpeg.title") }}</h3>

    <!-- Status bar -->
    <div class="flex items-center gap-3">
      <span :class="['badge badge-sm', statusBadge.class]">
        {{ statusBadge.text }}
      </span>
      <span v-if="currentVersion" class="text-sm opacity-70">
        v{{ currentVersion }}
      </span>
    </div>

    <!-- Actions -->
    <div class="flex flex-wrap gap-2">
      <button
        class="btn btn-xs btn-primary btn-outline"
        :disabled="status === 'detecting'"
        @click="emit('detect')"
      >
        {{ t("ffmpeg.autoDetect") }}
      </button>
      <button
        class="btn btn-xs btn-outline"
        @click="emit('selectBinary')"
      >
        {{ t("ffmpeg.select") }}
      </button>

      <!-- Windows: Download button -->
      <button
        v-if="isWindows"
        class="btn btn-xs btn-accent btn-outline"
        :disabled="status === 'detecting' || isDownloading"
        @click="showConfirm = true"
      >
        <span v-if="isDownloading" class="loading loading-spinner loading-xs" />
        {{ t("ffmpeg.downloadFfmpeg") }}
      </button>

      <!-- macOS: Open Homebrew page -->
      <a
        v-else-if="isMacOS"
        href="https://formulae.brew.sh/formula/ffmpeg"
        target="_blank"
        rel="noopener"
        class="btn btn-xs btn-accent btn-outline"
      >
        {{ t("ffmpeg.downloadFfmpeg") }}
      </a>

      <!-- Linux: Platform install info -->
      <button
        v-else
        class="btn btn-xs btn-accent btn-outline"
        :disabled="status === 'detecting'"
        @click="handleDownload"
      >
        {{ t("ffmpeg.downloadFfmpeg") }}
      </button>
    </div>

    <!-- Platform install instructions -->
    <div v-if="installInfo" class="text-xs space-y-1 mt-2">
      <p>{{ t("ffmpeg.notAvailable") }}</p>
      <code class="block mt-1 px-2 py-1 bg-base-300 rounded text-sm">{{ installInfo.command }}</code>
      <a
        v-if="installInfo.url"
        :href="installInfo.url"
        target="_blank"
        rel="noopener"
        class="link text-xs"
      >{{ installInfo.method }}</a>
    </div>

    <!-- Version list -->
    <div v-if="versions.length > 0" class="space-y-1">
      <p class="text-xs font-medium opacity-60">{{ t("ffmpeg.availableVersions") }}</p>
      <div
        v-for="ver in versions"
        :key="ver.path"
        class="flex items-center gap-3 rounded-lg px-3 py-2 cursor-pointer transition-colors"
        :class="ver.active ? 'bg-primary/10 border border-primary/30' : 'hover:bg-base-200'"
        @click="emit('switch', ver.path)"
      >
        <div
          class="h-4 w-4 rounded-full border-2 flex items-center justify-center"
          :class="ver.active ? 'border-primary bg-primary' : 'border-base-content/30'"
        >
          <div v-if="ver.active" class="h-1.5 w-1.5 rounded-full bg-base-100" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="badge badge-xs" :class="ver.active ? 'badge-primary' : 'badge-ghost'">
              {{ ver.source }}
            </span>
            <span class="text-sm font-medium">
              FFmpeg <template v-if="ver.version">v{{ ver.version }}</template>
            </span>
          </div>
          <p class="text-xs opacity-50 truncate" :title="ver.path">
            {{ ver.path }}
          </p>
        </div>
      </div>
    </div>

    <p v-else-if="status !== 'detecting'" class="text-xs opacity-40">
      {{ t("ffmpeg.noVersionsFound") }}
    </p>

    <!-- Download confirmation modal -->
    <dialog class="modal" :class="{ 'modal-open': showConfirm }">
      <div class="modal-box">
        <h3 class="text-lg font-bold">{{ t("ffmpeg.confirmDownload") }}</h3>
        <p class="py-4">{{ t("ffmpeg.confirmDownloadDesc") }}</p>
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
