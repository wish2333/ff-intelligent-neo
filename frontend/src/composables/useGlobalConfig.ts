/**
 * Global command configuration store.
 *
 * Module-level reactive singleton that persists across page navigation.
 * Both CommandConfigPage and TaskQueuePage share this same state.
 *
 * Usage:
 *   const { transcode, filters, activeMode, toTaskConfig } = useGlobalConfig()
 */

import { reactive, ref, computed, watch } from "vue"
import type {
  TranscodeConfigDTO, FilterConfigDTO, TaskConfigDTO,
  ClipConfigDTO, MergeConfigDTO, AudioSubtitleConfigDTO,
  CustomCommandConfigDTO,
} from "../types/config"

const DEFAULT_TRANSCODE: TranscodeConfigDTO = {
  video_codec: "libx264",
  audio_codec: "aac",
  video_bitrate: "",
  audio_bitrate: "128k",
  resolution: "",
  framerate: "",
  output_extension: ".mp4",
  // Phase 3.5: quality parameters
  quality_mode: "",
  quality_value: 0,
  preset: "",
  pixel_format: "",
  max_bitrate: "",
  bufsize: "",
}

const DEFAULT_FILTER: FilterConfigDTO = {
  rotate: "",
  crop: "",
  watermark_path: "",
  watermark_position: "bottom-right",
  watermark_margin: 10,
  volume: "",
  speed: "",
  audio_normalize: false,
  target_loudness: -16,
  true_peak: -1,
  lra: 11,
  aspect_convert: "",
  target_resolution: "",
  bg_image_path: "",
}

const DEFAULT_CLIP: ClipConfigDTO = {
  clip_mode: "cut",
  start_time: "",
  end_time_or_duration: "",
  use_copy_codec: true,
}

const DEFAULT_MERGE: MergeConfigDTO = {
  merge_mode: "ts_concat",
  target_resolution: "1920x1080",
  target_fps: 30,
  file_list: [],
  // Phase 3.5: intro/outro
  intro_path: "",
  outro_path: "",
}

const DEFAULT_AVSMIX: AudioSubtitleConfigDTO = {
  external_audio_path: "",
  subtitle_path: "",
  subtitle_language: "",
  replace_audio: true,
}

// Phase 3.5: custom command defaults
const DEFAULT_CUSTOM: CustomCommandConfigDTO = {
  raw_args: "",
  output_extension: ".mp4",
}

// Module-level reactive state -- shared by all importers
const transcode = reactive<TranscodeConfigDTO>({ ...DEFAULT_TRANSCODE })
const filters = reactive<FilterConfigDTO>({ ...DEFAULT_FILTER })
const clip = reactive<ClipConfigDTO>({ ...DEFAULT_CLIP })
const merge = reactive<MergeConfigDTO>({ ...DEFAULT_MERGE })
const avsmix = reactive<AudioSubtitleConfigDTO>({ ...DEFAULT_AVSMIX })
const customCommand = reactive<CustomCommandConfigDTO>({ ...DEFAULT_CUSTOM })
const activeMode = ref<string>("transcode")
const supportedEncoders = ref<string[]>([])

// Auto-switch merge_mode to filter_complex when intro/outro is set
watch(
  () => [merge.intro_path, merge.outro_path],
  ([intro, outro]) => {
    if (intro || outro) {
      merge.merge_mode = "filter_complex"
    }
  },
)

export function useGlobalConfig() {
  const configRef = computed<TaskConfigDTO>(() => {
    const mode = activeMode.value
    // Always include transcode + filters as base
    const base: TaskConfigDTO = {
      transcode: { ...transcode },
      filters: { ...filters },
      output_dir: "",
    }
    // Custom command always overrides when raw_args is set, regardless of mode
    if (customCommand.raw_args.trim()) {
      base.custom_command = { ...customCommand }
    }
    // Global intro/outro: always include when set (applies to ALL queue tasks)
    if (merge.intro_path || merge.outro_path) {
      base.merge = { ...merge }
    }
    // Clip is an auxiliary config that layers onto transcode/filters.
    // Include it whenever data is filled, unless in merge or custom mode.
    if (clip.start_time || clip.end_time_or_duration) {
      if (mode !== "merge" && mode !== "custom") {
        base.clip = { ...clip }
      }
    }
    // Only include the mode-specific sub-config based on active mode
    if (mode === "merge") {
      // Only set merge if not already set by intro/outro above
      if (!base.merge) {
        base.merge = { ...merge }
      }
    } else if (mode === "avsmix") {
      base.avsmix = { ...avsmix }
    } else if (mode === "custom") {
      base.custom_command = { ...customCommand }
    }
    // mode === "transcode" / "filters" / "clip" -> transcode + filters + optional clip
    return base
  })

  function toTaskConfig(): TaskConfigDTO {
    return configRef.value
  }

  function loadFromTaskConfig(config: TaskConfigDTO) {
    // Use spread defaults to prevent stale fields from partial configs
    if (config.transcode) Object.assign(transcode, { ...DEFAULT_TRANSCODE, ...config.transcode })
    if (config.filters) Object.assign(filters, { ...DEFAULT_FILTER, ...config.filters })
    if (config.clip) {
      Object.assign(clip, { ...DEFAULT_CLIP, ...config.clip })
      activeMode.value = "clip"
    }
    if (config.merge) {
      Object.assign(merge, { ...DEFAULT_MERGE, ...config.merge })
      activeMode.value = "merge"
    }
    if (config.avsmix) {
      Object.assign(avsmix, { ...DEFAULT_AVSMIX, ...config.avsmix })
      activeMode.value = "avsmix"
    }
    // Phase 3.5: load custom command config
    if (config.custom_command) {
      Object.assign(customCommand, { ...DEFAULT_CUSTOM, ...config.custom_command })
      activeMode.value = "custom"
    }
  }

  function resetTranscode() {
    Object.assign(transcode, DEFAULT_TRANSCODE)
  }

  function resetFilters() {
    Object.assign(filters, DEFAULT_FILTER)
  }

  function resetClip() {
    Object.assign(clip, DEFAULT_CLIP)
  }

  function resetMerge() {
    Object.assign(merge, DEFAULT_MERGE)
  }

  function resetAvsmix() {
    Object.assign(avsmix, DEFAULT_AVSMIX)
  }

  function resetCustom() {
    Object.assign(customCommand, DEFAULT_CUSTOM)
  }

  function resetAll() {
    resetTranscode()
    resetFilters()
    resetClip()
    resetMerge()
    resetAvsmix()
    resetCustom()
    activeMode.value = "transcode"
  }

  return {
    transcode,
    filters,
    clip,
    merge,
    avsmix,
    customCommand,
    activeMode,
    supportedEncoders,
    configRef,
    toTaskConfig,
    loadFromTaskConfig,
    resetTranscode,
    resetFilters,
    resetClip,
    resetMerge,
    resetAvsmix,
    resetCustom,
    resetAll,
  }
}
