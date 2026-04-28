/** TypeScript types for ffprobe media file analysis. */

/** Parsed general/format metadata from ffprobe. */
export interface ProbeGeneralInfo {
  file_name: string
  file_path: string
  file_size_bytes: number
  duration_seconds: number
  format_name: string
  format_long_name: string
  bit_rate: string
  nb_streams: number
  probe_score: number
}

/** Parsed video stream metadata. */
export interface ProbeVideoStream {
  codec_name: string
  codec_long_name: string
  width: number
  height: number
  resolution: string
  bit_rate: string
  fps: string
  pix_fmt: string
  color_space: string
  color_range: string
  profile: string
  level: number
  sample_aspect_ratio: string
  display_aspect_ratio: string
  field_order: string
  language: string
  index: number
}

/** Parsed audio stream metadata. */
export interface ProbeAudioStream {
  codec_name: string
  codec_long_name: string
  sample_rate: string
  channels: number
  channel_layout: string
  bit_rate: string
  language: string
  index: number
}

/** Parsed subtitle stream metadata. */
export interface ProbeSubtitleStream {
  codec_name: string
  language: string
  index: number
}

/** Full parsed probe result organized by category. */
export interface ProbeParsedInfo {
  general: ProbeGeneralInfo
  video: ProbeVideoStream[]
  audio: ProbeAudioStream[]
  subtitle: ProbeSubtitleStream[]
}

/** Complete probe API response data. */
export interface ProbeResult {
  parsed: ProbeParsedInfo
  raw: string
}

/** Display mode for probe results. */
export type ProbeDisplayMode = "parsed" | "raw"
