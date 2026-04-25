/**
 * Locale management composable.
 *
 * Handles zh-CN/en language switching via vue-i18n.
 * Persists preference to settings.json via bridge.
 */

import { ref, onMounted } from "vue"
import { useI18n } from "vue-i18n"
import { call, waitForPyWebView } from "../bridge"

export type LocaleValue = "zh-CN" | "en"

const SUPPORTED_LOCALES: LocaleValue[] = ["zh-CN", "en"]

function resolveLocale(preference: string): LocaleValue {
  if (preference !== "auto") {
    return SUPPORTED_LOCALES.includes(preference as LocaleValue)
      ? (preference as LocaleValue)
      : "zh-CN"
  }
  const browserLang = navigator.language
  if (browserLang.startsWith("zh")) return "zh-CN"
  return "en"
}

export function useLocale() {
  const { locale } = useI18n({ useScope: "global" })
  const currentLocale = ref<LocaleValue>("zh-CN")

  async function setLocale(newLocale: LocaleValue): Promise<void> {
    currentLocale.value = newLocale
    locale.value = newLocale
    try {
      await call<null>("save_settings", { language: newLocale })
    } catch {
      // Silent fail - locale is still applied locally
    }
  }

  function toggleLocale(): void {
    const next = currentLocale.value === "zh-CN" ? "en" : "zh-CN"
    setLocale(next)
  }

  onMounted(async () => {
    try {
      await waitForPyWebView()
      const res = await call<{ language: string }>("get_settings")
      if (res.success && res.data) {
        const resolved = resolveLocale(res.data.language ?? "auto")
        currentLocale.value = resolved
        locale.value = resolved
      }
    } catch {
      // Default to zh-CN if settings unavailable
    }
  })

  return {
    currentLocale,
    setLocale,
    toggleLocale,
    resolveLocale,
  }
}
