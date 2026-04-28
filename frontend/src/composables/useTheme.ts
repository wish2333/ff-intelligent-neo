/**
 * Theme management composable.
 *
 * Handles light/dark/auto theme switching via DaisyUI data-theme attribute.
 * Persists preference to settings.json via bridge.
 */

import { ref, onMounted, onUnmounted } from "vue"
import { call, waitForPyWebView } from "../bridge"

export type ThemeValue = "auto" | "light" | "dark"

export function useTheme() {
  const currentTheme = ref<ThemeValue>("auto")

  function resolveTheme(preference: ThemeValue): string {
    if (preference !== "auto") return preference
    return window.matchMedia("(prefers-color-scheme: light)").matches
      ? "light"
      : "dark"
  }

  function applyTheme(preference: ThemeValue): void {
    const resolved = resolveTheme(preference)
    document.documentElement.setAttribute("data-theme", resolved)
  }

  async function setTheme(theme: ThemeValue): Promise<void> {
    currentTheme.value = theme
    applyTheme(theme)
    try {
      await call<null>("save_settings", { theme })
    } catch {
      // Silent fail - theme is still applied locally
    }
  }

  function toggleTheme(): void {
    const resolved = resolveTheme(currentTheme.value)
    const next = resolved === "dark" ? "light" : "dark"
    setTheme(next).catch(() => { /* theme still applied locally */ })
  }

  let mediaQueryHandler: (() => void) | null = null

  onMounted(async () => {
    try {
      await waitForPyWebView()
      const res = await call<{ theme: string }>("get_settings")
      if (res.success && res.data) {
        const raw = res.data.theme ?? "auto"
        currentTheme.value = raw === "light" || raw === "dark" || raw === "auto" ? raw : "auto"
      }
    } catch {
      // Default to auto if settings unavailable
    }
    applyTheme(currentTheme.value)

    // Listen for system theme changes when in auto mode
    const mql = window.matchMedia("(prefers-color-scheme: light)")
    mediaQueryHandler = () => {
      if (currentTheme.value === "auto") {
        applyTheme("auto")
      }
    }
    mql.addEventListener("change", mediaQueryHandler)
  })

  onUnmounted(() => {
    if (mediaQueryHandler) {
      window.matchMedia("(prefers-color-scheme: light)")
        .removeEventListener("change", mediaQueryHandler)
    }
  })

  return {
    currentTheme,
    setTheme,
    toggleTheme,
    resolveTheme,
  }
}
