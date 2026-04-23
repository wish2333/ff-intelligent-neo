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
