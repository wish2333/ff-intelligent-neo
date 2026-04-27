<script setup lang="ts">
import { onMounted, computed } from "vue"
import { waitForPyWebView, call } from "../bridge"
import { useSettings } from "../composables/useSettings"
import { useAutoEditor } from "../composables/useAutoEditor"
import { useI18n } from "vue-i18n"

import FFmpegSetup from "../components/settings/FFmpegSetup.vue"
import AutoEditorSetup from "../components/settings/AutoEditorSetup.vue"
import ThreadCountInput from "../components/settings/ThreadCountInput.vue"
import OutputFolderInput from "../components/settings/OutputFolderInput.vue"
import AppAbout from "../components/settings/AppAbout.vue"

const { t } = useI18n()
const s = useSettings()
const ae = useAutoEditor()

const currentVersion = computed(() => {
  const active = s.ffmpegVersions.value.find((v) => v.active)
  return active?.version ?? null
})

onMounted(async () => {
  try {
    await waitForPyWebView()
    s.fetchSettings()
    s.fetchFfmpegVersions()
    s.fetchAppInfo()
    await ae.fetchStatus()
  } catch (err) {
    console.error("[SettingsPage] mount failed:", err)
  }
})

async function handleThreadChange(value: number): Promise<void> {
  await s.saveSettings({ max_workers: value })
}

async function handleOutputDirChange(value: string): Promise<void> {
  await s.saveSettings({ default_output_dir: value })
}

async function handleSelectAutoEditorBinary(): Promise<void> {
  try {
    const res = await call<string>("select_file_filtered")
    if (res.success && res.data) {
      ae.setPath(res.data)
    }
  } catch {
    // silently fail
  }
}
</script>

<template>
  <div class="page-scroll flex flex-1 flex-col gap-4 p-4 overflow-auto">
    <h1 class="text-xl font-bold tracking-tight">{{ t("settings.title") }}</h1>

    <div class="grid gap-4 lg:grid-cols-2">
      <div class="card bg-base-200 shadow-sm border border-base-300">
        <div class="card-body">
          <FFmpegSetup
            :versions="s.ffmpegVersions.value"
            :status="s.ffmpegStatus.value"
            :current-version="currentVersion"
            :platform="s.appInfo.value?.platform ?? 'win32'"
            @detect="s.detectFfmpeg()"
            @select-binary="s.selectFfmpegBinary()"
            @switch="(path) => s.switchFfmpeg(path)"
            @download="s.downloadFfmpeg()"
          />
        </div>
      </div>

      <div class="space-y-4">
        <div class="card bg-base-200 shadow-sm border border-base-300">
          <div class="card-body">
            <AutoEditorSetup
              :status="ae.autoEditorStatus.value"
              :platform="s.appInfo.value?.platform ?? 'win32'"
              @select-binary="handleSelectAutoEditorBinary"
              @set-path="(path) => ae.setPath(path)"
            />
          </div>
        </div>
        <div class="card bg-base-200 shadow-sm border border-base-300">
          <div class="card-body">
            <ThreadCountInput
              :value="s.settings.max_workers"
              @change="handleThreadChange"
            />
          </div>
        </div>
        <div class="card bg-base-200 shadow-sm border border-base-300">
          <div class="card-body">
            <OutputFolderInput
              :value="s.settings.default_output_dir"
              @change="handleOutputDirChange"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="card bg-base-200 shadow-sm border border-base-300">
      <div class="card-body">
        <AppAbout :info="s.appInfo.value" />
      </div>
    </div>
  </div>
</template>
