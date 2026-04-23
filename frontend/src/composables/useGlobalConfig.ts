/**
 * Global command configuration store.
 *
 * Module-level reactive singleton that persists across page navigation.
 * Both CommandConfigPage and TaskQueuePage share this same state.
 *
 * Usage:
 *   const { transcode, filters, toTaskConfig } = useGlobalConfig()
 */

import { reactive, computed } from "vue"
import type { TranscodeConfigDTO, FilterConfigDTO, TaskConfigDTO } from "../types/config"

const DEFAULT_TRANSCODE: TranscodeConfigDTO = {
  video_codec: "libx264",
  audio_codec: "aac",
  video_bitrate: "",
  audio_bitrate: "192k",
  resolution: "",
  framerate: "",
  output_extension: ".mp4",
}

const DEFAULT_FILTER: FilterConfigDTO = {
  rotate: "",
  crop: "",
  watermark_path: "",
  watermark_position: "bottom-right",
  watermark_margin: 10,
  volume: "",
  speed: "",
}

// Module-level reactive state -- shared by all importers
const transcode = reactive<TranscodeConfigDTO>({ ...DEFAULT_TRANSCODE })
const filters = reactive<FilterConfigDTO>({ ...DEFAULT_FILTER })

export function useGlobalConfig() {
  const configRef = computed<TaskConfigDTO>(() => ({
    transcode: { ...transcode },
    filters: { ...filters },
    output_dir: "",
  }))

  function toTaskConfig(): TaskConfigDTO {
    return {
      transcode: { ...transcode },
      filters: { ...filters },
      output_dir: "",
    }
  }

  function loadFromTaskConfig(config: TaskConfigDTO) {
    Object.assign(transcode, config.transcode)
    Object.assign(filters, config.filters)
  }

  function resetTranscode() {
    Object.assign(transcode, DEFAULT_TRANSCODE)
  }

  function resetFilters() {
    Object.assign(filters, DEFAULT_FILTER)
  }

  function resetAll() {
    resetTranscode()
    resetFilters()
  }

  return {
    transcode,
    filters,
    configRef,
    toTaskConfig,
    loadFromTaskConfig,
    resetTranscode,
    resetFilters,
    resetAll,
  }
}
