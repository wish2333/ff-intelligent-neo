/**
 * Settings composable.
 *
 * Manages application settings, FFmpeg version discovery,
 * and provides save/switch/detect operations.
 */

import { ref, reactive } from "vue"
import { call } from "../bridge"
import type { AppSettingsDTO } from "../types/settings"

export interface FfmpegVersionDTO {
  path: string
  version: string
  source: string
  active: boolean
}

export interface AppInfoDTO {
  app_name: string
  app_version: string
  python_version: string
  ffmpeg_path: string
  ffmpeg_version: string | null
  ffprobe_path: string
  ffprobe_version: string | null
  is_packaged: boolean
  platform: string
}

export function useSettings() {
  const settings = reactive<AppSettingsDTO>({
    max_workers: 2,
    default_output_dir: "",
    ffmpeg_path: "",
    ffprobe_path: "",
    theme: "auto",
    language: "auto",
  })

  const ffmpegVersions = ref<FfmpegVersionDTO[]>([])
  const appInfo = ref<AppInfoDTO | null>(null)
  const ffmpegStatus = ref<"ready" | "not_found" | "detecting">("detecting")

  async function fetchSettings(): Promise<void> {
    try {
      const res = await call<AppSettingsDTO>("get_settings")
      if (res.success && res.data) {
        Object.assign(settings, res.data)
      }
    } catch (err) {
      console.error("[useSettings] fetchSettings error:", err)
    }
  }

  async function saveSettings(partial: Partial<AppSettingsDTO>): Promise<boolean> {
    try {
      const merged = { ...settings, ...partial }
      const res = await call<null>("save_settings", merged)
      if (res.success) {
        Object.assign(settings, merged)
      }
      return res.success
    } catch (err) {
      console.error("[useSettings] saveSettings error:", err)
      return false
    }
  }

  async function fetchFfmpegVersions(): Promise<void> {
    try {
      const res = await call<FfmpegVersionDTO[]>("get_ffmpeg_versions")
      if (res.success && res.data) {
        ffmpegVersions.value = res.data
      }
    } catch (err) {
      console.error("[useSettings] fetchFfmpegVersions error:", err)
    }
  }

  async function switchFfmpeg(path: string): Promise<boolean> {
    try {
      const res = await call<{ path: string; version: string; ffprobe_path: string }>(
        "switch_ffmpeg",
        path,
      )
      if (res.success && res.data) {
        settings.ffmpeg_path = res.data.path
        // Refresh versions list to reflect new active
        await fetchFfmpegVersions()
        await fetchAppInfo()
      }
      return res.success
    } catch (err) {
      console.error("[useSettings] switchFfmpeg error:", err)
      return false
    }
  }

  async function selectFfmpegBinary(): Promise<string | null> {
    try {
      const res = await call<string>("select_ffmpeg_binary")
      if (res.success && res.data) {
        // Auto-switch to selected binary
        await switchFfmpeg(res.data)
        return res.data
      }
      return null
    } catch (err) {
      console.error("[useSettings] selectFfmpegBinary error:", err)
      return null
    }
  }

  async function detectFfmpeg(): Promise<boolean> {
    ffmpegStatus.value = "detecting"
    try {
      const res = await call<{ ready: boolean; ffmpeg_path: string }>("setup_ffmpeg")
      if (res.success && res.data) {
        ffmpegStatus.value = res.data.ready ? "ready" : "not_found"
      } else {
        ffmpegStatus.value = "not_found"
      }
      await fetchFfmpegVersions()
      await fetchAppInfo()
      return ffmpegStatus.value === "ready"
    } catch (err) {
      console.error("[useSettings] detectFfmpeg error:", err)
      ffmpegStatus.value = "not_found"
      return false
    }
  }

  async function fetchAppInfo(): Promise<void> {
    try {
      const res = await call<AppInfoDTO>("get_app_info")
      if (res.success && res.data) {
        appInfo.value = res.data
        ffmpegStatus.value = res.data.ffmpeg_path ? "ready" : "not_found"
      }
    } catch (err) {
      console.error("[useSettings] fetchAppInfo error:", err)
    }
  }

  async function downloadFfmpeg(): Promise<boolean> {
    ffmpegStatus.value = "detecting"
    try {
      const res = await call<{ ffmpeg_path: string }>("download_ffmpeg")
      if (res.success && res.data) {
        ffmpegStatus.value = "ready"
        await fetchFfmpegVersions()
        await fetchAppInfo()
        return true
      }
      ffmpegStatus.value = "not_found"
      return false
    } catch (err) {
      console.error("[useSettings] downloadFfmpeg error:", err)
      ffmpegStatus.value = "not_found"
      return false
    }
  }

  return {
    settings,
    ffmpegVersions,
    appInfo,
    ffmpegStatus,
    fetchSettings,
    saveSettings,
    fetchFfmpegVersions,
    switchFfmpeg,
    selectFfmpegBinary,
    detectFfmpeg,
    fetchAppInfo,
    downloadFfmpeg,
  }
}
