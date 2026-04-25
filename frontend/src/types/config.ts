/** Configuration-related type definitions. */

export interface TranscodeConfigDTO {
  video_codec: string
  audio_codec: string
  video_bitrate: string
  audio_bitrate: string
  resolution: string
  framerate: string
  output_extension: string
  // Phase 3.5: quality parameters
  quality_mode: string
  quality_value: number
  preset: string
  pixel_format: string
  max_bitrate: string
  bufsize: string
}

export interface FilterConfigDTO {
  rotate: string
  crop: string
  watermark_path: string
  watermark_position: string
  watermark_margin: number
  volume: string
  speed: string
  audio_normalize: boolean
  target_loudness: number
  true_peak: number
  lra: number
  aspect_convert: string
  target_resolution: string
  bg_image_path: string
}

export interface ClipConfigDTO {
  clip_mode: "extract" | "cut"
  start_time: string
  end_time_or_duration: string
  use_copy_codec: boolean
}

export interface MergeConfigDTO {
  merge_mode: "ts_concat" | "concat_protocol" | "filter_complex"
  target_resolution: string
  target_fps: number
  file_list: string[]
  // Phase 3.5: intro/outro
  intro_path: string
  outro_path: string
}

export interface AudioSubtitleConfigDTO {
  external_audio_path: string
  subtitle_path: string
  subtitle_language: string
  replace_audio: boolean
}

// Phase 3.5: custom command
export interface CustomCommandConfigDTO {
  raw_args: string
  output_extension: string
}

export interface TaskConfigDTO {
  transcode: TranscodeConfigDTO
  filters: FilterConfigDTO
  clip?: ClipConfigDTO
  merge?: MergeConfigDTO
  avsmix?: AudioSubtitleConfigDTO
  custom_command?: CustomCommandConfigDTO
  output_dir: string
}

export type ActiveMode = "transcode" | "filters" | "clip" | "avsmix" | "merge" | "custom"

export interface EncoderConfigDTO {
  name: string
  displayName: string
  category: "video" | "audio"
  hardwareType?: "cpu" | "nvidia" | "amd" | "intel"
  recommendedQuality?: number
  qualityMode?: "crf" | "cq" | "qp"
  description: string
  priority: "P0" | "P1" | "P2"
}
