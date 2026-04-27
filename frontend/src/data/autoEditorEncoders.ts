/**
 * Curated encoder lists for auto-editor AdvancedTab.
 *
 * auto-editor --video-codec / --audio-codec pass directly to FFmpeg,
 * so any FFmpeg encoder can be used. Listed here are commonly-used ones.
 *
 * Hardware encoders require a compatible GPU and FFmpeg build.
 *
 * Based on auto-editor v30.1.x official documentation:
 * https://auto-editor.com/ref/options
 */

export interface AeEncoder {
  name: string
  displayName: string
  description: string
}

export interface AeEncoderGroup {
  priority: string
  labelKey: string
  encoders: AeEncoder[]
}

export const AE_VIDEO_ENCODER_GROUPS: AeEncoderGroup[] = [
  {
    priority: "recommended",
    labelKey: "autoCut.encoderGroups.recommended",
    encoders: [
      { name: "libx264", displayName: "H.264 (libx264)", description: "Software, best compatibility everywhere" },
      { name: "libx265", displayName: "H.265/HEVC (libx265)", description: "Software, better compression" },
    ],
  },
  {
    priority: "hardware",
    labelKey: "autoCut.encoderGroups.hardware",
    encoders: [
      { name: "h264_nvenc", displayName: "H.264 (NVIDIA NVENC)", description: "NVIDIA GPU hardware encoder" },
      { name: "hevc_nvenc", displayName: "HEVC (NVIDIA NVENC)", description: "NVIDIA GPU HEVC hardware encoder" },
      { name: "av1_nvenc", displayName: "AV1 (NVIDIA NVENC)", description: "NVIDIA RTX 40+ only" },
      { name: "h264_amf", displayName: "H.264 (AMD AMF)", description: "AMD GPU hardware encoder" },
      { name: "hevc_amf", displayName: "HEVC (AMD AMF)", description: "AMD GPU HEVC hardware encoder" },
      { name: "h264_qsv", displayName: "H.264 (Intel QSV)", description: "Intel Quick Sync Video encoder" },
      { name: "hevc_qsv", displayName: "HEVC (Intel QSV)", description: "Intel Quick Sync HEVC encoder" },
      { name: "h264_videotoolbox", displayName: "H.264 (Apple VT)", description: "macOS VideoToolbox encoder" },
      { name: "hevc_videotoolbox", displayName: "HEVC (Apple VT)", description: "macOS VideoToolbox HEVC encoder" },
    ],
  },
  {
    priority: "other",
    labelKey: "autoCut.encoderGroups.other",
    encoders: [
      { name: "libsvtav1", displayName: "AV1 (libsvtav1)", description: "Software, best compression, slower" },
      { name: "libvpx-vp9", displayName: "VP9 (libvpx)", description: "Software, web-optimized" },
      { name: "mpeg4", displayName: "MPEG-4", description: "Legacy format, wide compatibility" },
    ],
  },
]

export const AE_AUDIO_ENCODER_GROUPS: AeEncoderGroup[] = [
  {
    priority: "recommended",
    labelKey: "autoCut.encoderGroups.recommended",
    encoders: [
      { name: "aac", displayName: "AAC", description: "Built-in FFmpeg AAC, universal compatibility" },
      { name: "libmp3lame", displayName: "MP3 (libmp3lame)", description: "Universal MP3 format" },
    ],
  },
  {
    priority: "other",
    labelKey: "autoCut.encoderGroups.other",
    encoders: [
      { name: "libopus", displayName: "Opus (libopus)", description: "Open source, high quality at low bitrates" },
      { name: "flac", displayName: "FLAC", description: "Lossless compression" },
      { name: "libfdk_aac", displayName: "AAC (libfdk_aac)", description: "Higher quality AAC, may not be available" },
    ],
  },
]
