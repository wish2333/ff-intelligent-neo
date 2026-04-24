/** Application settings type definitions. */

export interface AppSettingsDTO {
  max_workers: number
  default_output_dir: string
  ffmpeg_path: string
  ffprobe_path: string
  theme: string
  language: string
}

export interface FfmpegInstallInfo {
  method: string
  command: string
  url?: string
}

