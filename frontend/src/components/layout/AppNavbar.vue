<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue"
import { call, onEvent, waitForPyWebView } from "../../bridge"
import { useTheme } from "../../composables/useTheme"
import { useLocale } from "../../composables/useLocale"
import { useI18n } from "vue-i18n"

const { t } = useI18n()
const ffmpegStatus = ref<"unknown" | "ready" | "not_found">("unknown")
const ffmpegVersion = ref("")
const ffmpegError = ref("")
const aeStatus = ref<"unknown" | "ready" | "not_found">("unknown")
const aeVersion = ref("")
const { resolveTheme, toggleTheme } = useTheme()
const { toggleLocale, currentLocale } = useLocale()

const navItems = computed(() => [
  { name: "TaskQueue", label: t("nav.queue"), path: "/task-queue" },
  { name: "CommandConfig", label: t("nav.config"), path: "/config" },
  { name: "AudioSubtitle", label: t("nav.avMix"), path: "/audio-subtitle" },
  { name: "AutoCut", label: t("nav.autoCut"), path: "/auto-cut" },
  { name: "Merge", label: t("nav.merge"), path: "/merge" },
  { name: "CustomCommand", label: t("nav.custom"), path: "/custom-command" },
  { name: "Settings", label: t("nav.settings"), path: "/settings" },
])

let cleanupVersionEvent: (() => void) | null = null
let cleanupAeVersionEvent: (() => void) | null = null

onMounted(async () => {
  await waitForPyWebView()

  const setupRes = await call<{ ready: boolean; ffmpeg_path: string }>(
    "setup_ffmpeg",
  )
  if (setupRes.success && setupRes.data) {
    ffmpegStatus.value = setupRes.data.ready ? "ready" : "not_found"
  } else {
    ffmpegError.value = setupRes.error ?? t("nav.ffmpegUnknownError")
  }

  call<{
    app_name: string
    app_version: string
    python_version: string
    ffmpeg_path: string
    ffmpeg_version: string | null
    ffprobe_path: string
    ffprobe_version: string | null
    is_packaged: boolean
    platform: string
  }>("get_app_info").then((res) => {
    if (res.success && res.data) {
      ffmpegVersion.value = res.data.ffmpeg_version ?? ""
    }
  })

  cleanupVersionEvent = onEvent<{
    version: string
    path: string
    status: string
  }>("ffmpeg_version_changed", (detail) => {
    ffmpegStatus.value = detail.status === "ready" ? "ready" : "not_found"
    ffmpegVersion.value = detail.version
    ffmpegError.value = ""
  })

  // Auto-editor status check
  call<{ available: boolean; compatible: boolean; version: string; path: string }>(
    "get_auto_editor_status",
  ).then((res) => {
    if (res.success && res.data) {
      aeStatus.value = res.data.available && res.data.compatible ? "ready" : "not_found"
      aeVersion.value = res.data.version
    }
  }).catch(() => {})

  cleanupAeVersionEvent = onEvent<{
    version: string
    path: string
    status: string
  }>("auto_editor_version_changed", (detail) => {
    aeStatus.value = detail.status === "ready" ? "ready" : "not_found"
    aeVersion.value = detail.version
  })
})

onUnmounted(() => {
  cleanupVersionEvent?.()
  cleanupAeVersionEvent?.()
})
</script>

<template>
  <div class="navbar bg-base-200 border-b border-base-300 px-4 shrink-0">
    <div class="navbar-start flex items-center gap-1">
      <span class="text-base font-bold tracking-tight mr-2">FF Neo</span>
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="item.path"
        class="btn btn-ghost btn-sm text-sm"
        active-class="btn-active"
      >
        {{ item.label }}
      </router-link>
    </div>

    <div class="navbar-end flex items-center gap-1.5">
      <!-- Language toggle -->
      <button
        class="btn btn-ghost btn-sm btn-square"
        @click="toggleLocale"
      >
        {{ currentLocale === "zh-CN" ? "EN" : "CN" }}
      </button>

      <!-- Theme toggle -->
      <button
        class="btn btn-ghost btn-sm btn-square"
        :title="resolveTheme('auto') === 'dark' ? t('nav.switchToLight') : t('nav.switchToDark')"
        @click="toggleTheme"
      >
        <svg v-if="resolveTheme('auto') === 'dark'" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
        </svg>
      </button>

      <!-- FFmpeg status badge -->
      <span
        class="badge badge-sm font-medium"
        :class="
          ffmpegStatus === 'ready'
            ? 'badge-success'
            : ffmpegStatus === 'not_found'
              ? ffmpegVersion
                ? 'badge-warning'
                : 'badge-error'
              : 'badge-ghost'
        "
      >
        {{ ffmpegStatus === 'ready'
          ? (ffmpegVersion ? `FFmpeg ${ffmpegVersion}` : t("nav.ffmpegReady"))
          : ffmpegStatus === 'not_found'
            ? (ffmpegError || t("nav.ffmpegNotFound"))
            : t("nav.ffmpegChecking")
        }}
      </span>

      <!-- Auto-editor status badge -->
      <span
        v-if="aeStatus !== 'unknown'"
        class="badge badge-sm font-medium"
        :class="aeStatus === 'ready' ? 'badge-success' : 'badge-warning'"
      >
        {{ aeStatus === 'ready' ? `AE ${aeVersion}` : t("nav.aeNotFound") }}
      </span>
    </div>
  </div>
</template>
