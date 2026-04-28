/**
 * Auto-editor state management and command preview.
 *
 * Provides reactive state for all auto-editor parameters,
 * status checking, encoder querying, debounced command preview,
 * and task submission.
 *
 * v2.2.0 Phase 2: Initial implementation.
 */

import { ref, watch } from "vue"
import { call, onEvent } from "../bridge"
import { EVENT_AUTO_EDITOR_VERSION_CHANGED } from "../utils/events"
import type { AeStatus, AdvancedOptions } from "../types/autoEditor"

const PREVIEW_DEBOUNCE_MS = 300

export function useAutoEditor() {
  // --- State ---
  const editMethod = ref<"audio" | "motion">("audio")
  const audioThreshold = ref(0.04)
  const motionThreshold = ref(0.02)
  const whenSilentAction = ref("cut")
  const whenNormalAction = ref("nil")
  const margin = ref("0.2s")
  const smooth = ref("0.2s,0.1s")
  const silentSpeedValue = ref(4)
  const silentVolumeValue = ref(0.5)
  const normalSpeedValue = ref(4)
  const normalVolumeValue = ref(0.5)

  const advancedOptions = ref<AdvancedOptions>({
    cutOutRanges: [],
    addInRange: [],
    setActionRanges: [],
    frameRate: "",
    sampleRate: "",
    resolution: "",
    vn: false,
    an: false,
    sn: false,
    dn: false,
    videoCodec: "",
    audioCodec: "",
    videoBitrate: "",
    audioBitrate: "",
    crf: "",
    audioLayout: "",
    audioNormalize: "",
    noCache: false,
    open: false,
    faststart: true,
    fragmented: false,
    outputExtension: ".mp4",
  })

  const commandPreview = ref("")
  const selectedFile = ref<string | null>(null)
  const initializing = ref(true)
  const autoEditorStatus = ref<AeStatus>({
    available: false,
    compatible: false,
    version: "",
    path: "",
  })
  const validating = ref(false)
  const alertMessage = ref("")
  const alertType = ref<"error" | "success">("error")

  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  let unsubscribeVersion: (() => void) | null = null

  // --- Methods ---

  async function fetchStatus(): Promise<void> {
    try {
      const res = await call<AeStatus>("get_auto_editor_status")
      if (res.success && res.data) {
        autoEditorStatus.value = res.data
      }
    } catch {
      // bridge not ready yet
    }
  }

  async function setPath(path: string): Promise<boolean> {
    const res = await call<{ version: string; path: string }>(
      "set_auto_editor_path",
      path,
    )
    if (res.success) {
      await fetchStatus()
      return true
    }
    alertMessage.value = res.error ?? "Failed to set path"
    alertType.value = "error"
    clearAlert()
    return false
  }

  function buildParams(overrideInputFile?: string): Record<string, unknown> {
    const inputFile = overrideInputFile ?? selectedFile.value ?? "_placeholder.mp4"
    const params: Record<string, unknown> = {
      edit: editMethod.value,
      input_file: inputFile,
    }

    // Threshold
    const threshold = editMethod.value === "audio"
      ? audioThreshold.value
      : motionThreshold.value
    params.threshold = threshold

    // When-silent action (only pass when not default "cut")
    if (whenSilentAction.value === "speed") {
      params.when_silent = `speed:${silentSpeedValue.value}`
    } else if (whenSilentAction.value === "volume") {
      params.when_silent = `volume:${silentVolumeValue.value}`
    } else if (whenSilentAction.value !== "cut") {
      params.when_silent = whenSilentAction.value
    }
    // Default "cut" is auto-editor's default, no need to pass

    // When-normal action (only pass when not default "nil")
    if (whenNormalAction.value === "cut") {
      params.when_normal = "cut"
    } else if (whenNormalAction.value === "speed") {
      params.when_normal = `speed:${normalSpeedValue.value}`
    } else if (whenNormalAction.value === "volume") {
      params.when_normal = `volume:${normalVolumeValue.value}`
    }
    // Default "nil" is auto-editor's default, no need to pass

    // Margin (only pass when not default "0.2s")
    if (margin.value && margin.value !== "0.2s") {
      params.margin = margin.value
    }

    // Smooth (only pass when not default "0.2s,0.1s")
    if (smooth.value && smooth.value !== "0.2s,0.1s") {
      params.smooth = smooth.value
    }

    const adv = advancedOptions.value
    if (adv.cutOutRanges.length > 0) params.cut_out = adv.cutOutRanges
    if (adv.addInRange.length > 0) params.add_in = adv.addInRange
    if (adv.setActionRanges.length > 0) params.set_action = adv.setActionRanges
    if (adv.frameRate) params.frame_rate = adv.frameRate
    if (adv.sampleRate) params.sample_rate = adv.sampleRate
    if (adv.resolution) params.resolution = adv.resolution
    if (adv.vn) params.vn = true
    if (adv.an) params.an = true
    if (adv.sn) params.sn = true
    if (adv.dn) params.dn = true
    if (adv.videoCodec) params.video_codec = adv.videoCodec
    if (adv.audioCodec) params.audio_codec = adv.audioCodec
    if (adv.videoBitrate) params["b:v"] = adv.videoBitrate
    if (adv.audioBitrate) params["b:a"] = adv.audioBitrate
    if (adv.crf) params.crf = adv.crf
    if (adv.audioLayout) params.audio_layout = adv.audioLayout
    if (adv.audioNormalize) params.audio_normalize = adv.audioNormalize
    if (adv.noCache) params.no_cache = true
    if (adv.open) params.open = true
    if (!adv.faststart) params.faststart = false
    if (adv.fragmented) params.fragmented = true
    if (adv.outputExtension) params.output_extension = adv.outputExtension

    return params
  }

  async function updatePreview(): Promise<void> {
    validating.value = true
    try {
      const params = buildParams()

      const res = await call<{ argv: string[]; display: string }>(
        "preview_auto_editor_command",
        params,
      )

      if (res.success && res.data) {
        commandPreview.value = res.data.display
      } else {
        commandPreview.value = ""
        if (res.error) {
          alertMessage.value = res.error
          alertType.value = "error"
          clearAlert()
        }
      }
    } catch {
      commandPreview.value = ""
    } finally {
      validating.value = false
    }
  }

  async function addToQueue(inputFile: string): Promise<boolean> {
    if (!inputFile) {
      alertMessage.value = "noFileSelected"
      alertType.value = "error"
      clearAlert()
      return false
    }

    const params = buildParams(inputFile)
    const res = await call<{ task_id: string }>(
      "add_auto_editor_task",
      inputFile,
      params,
    )

    if (res.success) {
      alertMessage.value = "addSuccess"
      alertType.value = "success"
      clearAlert()
      return true
    }

    alertMessage.value = res.error ?? "addFailed"
    alertType.value = "error"
    clearAlert()
    return false
  }

  // --- Watch for parameter changes -> debounced preview ---
  watch(
    [editMethod, audioThreshold, motionThreshold, whenSilentAction,
     whenNormalAction, margin, smooth, silentSpeedValue, silentVolumeValue,
     normalSpeedValue, normalVolumeValue,
     advancedOptions, selectedFile],
    () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(updatePreview, PREVIEW_DEBOUNCE_MS)
    },
    { immediate: true },
  )

  // --- Event listener for version changes ---
  function setupEventListeners(): () => void {
    return onEvent<{ version: string; path: string; status: string }>(
      EVENT_AUTO_EDITOR_VERSION_CHANGED,
      () => {
        fetchStatus()
      },
    )
  }

  // --- Alert cleanup ---
  let alertTimer: ReturnType<typeof setTimeout> | null = null
  function clearAlert() {
    if (alertTimer) clearTimeout(alertTimer)
    alertTimer = setTimeout(() => {
      alertMessage.value = ""
    }, 3000)
  }

  // --- Lifecycle ---
  async function init(): Promise<void> {
    try {
      await fetchStatus()
    } finally {
      initializing.value = false
    }
    unsubscribeVersion = setupEventListeners()
  }

  function dispose(): void {
    if (unsubscribeVersion) {
      unsubscribeVersion()
      unsubscribeVersion = null
    }
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    if (alertTimer) {
      clearTimeout(alertTimer)
      alertTimer = null
    }
  }

  return {
    // State
    editMethod,
    audioThreshold,
    motionThreshold,
    whenSilentAction,
    whenNormalAction,
    margin,
    smooth,
    silentSpeedValue,
    silentVolumeValue,
    normalSpeedValue,
    normalVolumeValue,
    advancedOptions,
    commandPreview,
    selectedFile,
    autoEditorStatus,
    initializing,
    validating,
    alertMessage,
    alertType,
    // Methods
    fetchStatus,
    setPath,
    updatePreview,
    addToQueue,
    buildParams,
    // Lifecycle
    init,
    dispose,
  }
}
