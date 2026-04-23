/** Configuration-related type definitions. */

export interface TranscodeConfigDTO {
  video_codec: string
  audio_codec: string
  video_bitrate: string
  audio_bitrate: string
  resolution: string
  framerate: string
  output_extension: string
}

export interface FilterConfigDTO {
  rotate: string
  crop: string
  watermark_path: string
  watermark_position: string
  watermark_margin: number
  volume: string
  speed: string
}

export interface TaskConfigDTO {
  transcode: TranscodeConfigDTO
  filters: FilterConfigDTO
  output_dir: string
}
