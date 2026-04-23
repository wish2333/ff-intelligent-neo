<script setup lang="ts">
import { ref, onMounted } from "vue"
import { call, waitForPyWebView } from "../../bridge"

const ffmpegReady = ref(false)
const ffmpegVersion = ref("")
const ffmpegError = ref("")

const navItems = [
  { name: "TaskQueue", label: "Task Queue", path: "/task-queue" },
  { name: "CommandConfig", label: "Command Config", path: "/command-config" },
  { name: "Settings", label: "Settings", path: "/settings" },
]

onMounted(async () => {
  await waitForPyWebView()

  const setupRes = await call<{ ready: boolean; ffmpeg_path: string }>(
    "setup_ffmpeg",
  )
  if (setupRes.success && setupRes.data) {
    ffmpegReady.value = setupRes.data.ready
  } else {
    ffmpegError.value = setupRes.error ?? "Unknown error"
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
  }>("get_app_info").then((res) => {
    if (res.success && res.data) {
      ffmpegVersion.value = res.data.ffmpeg_version ?? ""
    }
  })
})
</script>

<template>
  <div class="navbar bg-base-200 px-4">
    <div class="navbar-start">
      <span class="text-lg font-bold">FF Intelligent Neo</span>
    </div>

    <div class="navbar-center flex gap-1">
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="item.path"
        class="btn btn-ghost btn-sm"
        active-class="btn-active"
      >
        {{ item.label }}
      </router-link>
    </div>

    <div class="navbar-end">
      <span
        class="badge badge-sm"
        :class="
          ffmpegReady ? 'badge-success' : ffmpegVersion ? 'badge-warning' : 'badge-error'
        "
      >
        {{ ffmpegReady ? (ffmpegVersion ? `FFmpeg ${ffmpegVersion}` : "FFmpeg Ready") : (ffmpegError || "FFmpeg Not Found") }}
      </span>
    </div>
  </div>
</template>
