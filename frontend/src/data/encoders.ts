/**
 * Encoder registry for FFmpeg command configuration.
 *
 * Grouped by priority (P0/P1/P2) and category (video/audio).
 * Hardware encoders require runtime detection via check_hw_encoders().
 */

import type { EncoderConfigDTO } from "../types/config"

export const VIDEO_ENCODERS: EncoderConfigDTO[] = [
  // P0: First choice recommendations
  { name: "av1_nvenc", displayName: "AV1 (NVIDIA)", category: "video", hardwareType: "nvidia", recommendedQuality: 36, qualityMode: "cq", description: "RTX 40+ recommended, best compression efficiency", priority: "P0" },
  { name: "libx265", displayName: "H.265/HEVC", category: "video", hardwareType: "cpu", recommendedQuality: 24, qualityMode: "crf", description: "Best quality/size balance, widely supported", priority: "P0" },
  { name: "libsvtav1", displayName: "SVT-AV1", category: "video", hardwareType: "cpu", recommendedQuality: 32, qualityMode: "crf", description: "Open source AV1, excellent compression", priority: "P0" },

  // P1: Good alternatives
  { name: "libx264", displayName: "H.264/AVC", category: "video", hardwareType: "cpu", recommendedQuality: 23, qualityMode: "crf", description: "Best compatibility, widely decoded", priority: "P1" },
  { name: "hevc_nvenc", displayName: "HEVC (NVIDIA)", category: "video", hardwareType: "nvidia", recommendedQuality: 28, qualityMode: "cq", description: "Fast H.265 encoding on NVIDIA GPUs", priority: "P1" },
  { name: "h264_nvenc", displayName: "H.264 (NVIDIA)", category: "video", hardwareType: "nvidia", recommendedQuality: 28, qualityMode: "cq", description: "Fast H.264 encoding on NVIDIA GPUs", priority: "P1" },
  { name: "libvpx-vp9", displayName: "VP9", category: "video", hardwareType: "cpu", recommendedQuality: 31, qualityMode: "crf", description: "Web-friendly format", priority: "P1" },

  // P2: Conditional (requires specific hardware)
  { name: "h264_amf", displayName: "H.264 (AMD)", category: "video", hardwareType: "amd", recommendedQuality: 34, qualityMode: "qp", description: "AMD GPU encoding, RX 7000+ series", priority: "P2" },
  { name: "hevc_amf", displayName: "HEVC (AMD)", category: "video", hardwareType: "amd", recommendedQuality: 32, qualityMode: "qp", description: "AMD GPU H.265 encoding", priority: "P2" },
  { name: "h264_qsv", displayName: "H.264 (Intel)", category: "video", hardwareType: "intel", recommendedQuality: 28, qualityMode: "qp", description: "Intel Quick Sync Video encoding", priority: "P2" },
  { name: "hevc_qsv", displayName: "HEVC (Intel)", category: "video", hardwareType: "intel", recommendedQuality: 30, qualityMode: "qp", description: "Intel Quick Sync H.265 encoding", priority: "P2" },

  // Special
  { name: "copy", displayName: "Copy (no re-encode)", category: "video", description: "Copy video stream without re-encoding", priority: "P1" },
  { name: "none", displayName: "No Video", category: "video", description: "Remove video stream", priority: "P1" },
]

export const AUDIO_ENCODERS: EncoderConfigDTO[] = [
  { name: "aac", displayName: "AAC", category: "audio", hardwareType: "cpu", recommendedQuality: undefined, description: "Universal audio codec, 192k recommended", priority: "P0" },
  { name: "opus", displayName: "Opus", category: "audio", hardwareType: "cpu", recommendedQuality: undefined, description: "Open source, best quality at 128k", priority: "P0" },
  { name: "flac", displayName: "FLAC", category: "audio", hardwareType: "cpu", recommendedQuality: undefined, description: "Lossless audio compression", priority: "P1" },
  { name: "libmp3lame", displayName: "MP3", category: "audio", hardwareType: "cpu", recommendedQuality: undefined, description: "Universal MP3 format, 320k recommended", priority: "P1" },
  { name: "alac", displayName: "ALAC", category: "audio", hardwareType: "cpu", recommendedQuality: undefined, description: "Apple Lossless Audio Codec", priority: "P2" },
  { name: "copy", displayName: "Copy (no re-encode)", category: "audio", description: "Copy audio stream without re-encoding", priority: "P0" },
  { name: "none", displayName: "No Audio", category: "audio", description: "Remove audio stream", priority: "P1" },
]

/** Priority labels for grouping display. */
export const PRIORITY_LABELS: Record<string, string> = {
  P0: "Recommended",
  P1: "Alternative",
  P2: "Hardware-specific",
}
