/** Formatting utility functions for displaying task data. */

/**
 * Format seconds into HH:MM:SS or MM:SS string.
 */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return "00:00"
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  const pad = (n: number) => String(n).padStart(2, "0")
  if (h > 0) return `${pad(h)}:${pad(m)}:${pad(s)}`
  return `${pad(m)}:${pad(s)}`
}

/**
 * Format bytes into human-readable file size.
 */
export function formatFileSize(bytes: number): string {
  if (!bytes || bytes <= 0) return "0 B"
  const units = ["B", "KB", "MB", "GB", "TB"]
  let unitIndex = 0
  let size = bytes
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

/**
 * Format progress percent (0-100) to a display string.
 */
export function formatPercent(percent: number): string {
  if (percent === undefined || percent === null) return "0%"
  return `${Math.round(percent)}%`
}

/**
 * Format resolution string for display.
 */
export function formatResolution(width: number | undefined, height: number | undefined): string {
  if (!width || !height) return ""
  return `${width}x${height}`
}

/**
 * Format bit rate string (e.g. "5000000" -> "5.0 Mbps").
 */
export function formatBitRate(bitRate: string): string {
  if (!bitRate) return ""
  const bps = parseInt(bitRate, 10)
  if (isNaN(bps) || bps <= 0) return bitRate
  if (bps >= 1_000_000) return `${(bps / 1_000_000).toFixed(1)} Mbps`
  if (bps >= 1_000) return `${(bps / 1_000).toFixed(0)} kbps`
  return `${bps} bps`
}

/**
 * Format channel count to display string (e.g. 2 -> "stereo", 6 -> "5.1").
 */
export function formatChannels(channels: number): string {
  if (!channels || channels <= 0) return ""
  const names: Record<number, string> = {
    1: "mono",
    2: "stereo",
    6: "5.1",
    8: "7.1",
  }
  return names[channels] ?? `${channels} ch`
}
