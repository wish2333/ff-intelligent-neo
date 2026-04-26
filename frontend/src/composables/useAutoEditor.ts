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
import type { AeStatus, AdvancedOptions, EncoderLists } from "../types/autoEditor"

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
  const speedValue = ref(4)
  const volumeValue = ref(0.5)

  const encoderLists = ref<EncoderLists>({
    video: [],
    audio: [],
    subtitle: [],
    other: [],
  })

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
    const res = await call<AeStatus>("get_auto_editor_status")
    if (res.success && res.data) {
      autoEditorStatus.value = res.data
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

  async function fetchEncoders(format: string): Promise<void> {
    const res = await call<EncoderLists>("get_auto_editor_encoders", format)
    if (res.success && res.data) {
      encoderLists.value = res.data
    } else {
      encoderLists.value = { video: [], audio: [], subtitle: [], other: [] }
      if (res.error) {
        alertMessage.value = res.error
        alertType.value = "error"
        clearAlert()
      }
    }
  }

  function buildParams(): Record<string, unknown> {
    const params: Record<string, unknown> = {
      edit: editMethod.value,
      threshold: editMethod.value === "audio"
        ? audioThreshold.value
        : motionThreshold.value,
      when_silent: whenSilentAction.value === "cut"
        ? "cut"
        : whenSilentAction.value === "speed"
          ? `speed:${speedValue.value}`
          : whenSilentAction.value === "volume"
            ? `volume:${volumeValue.value}`
            : whenSilentAction.value,
      when_normal: whenNormalAction.value === "cut"
        ? "cut"
        : whenNormalAction.value === "speed"
          ? `speed:${speedValue.value}`
          : whenNormalAction.value === "volume"
            ? `volume:${volumeValue.value}`
            : whenNormalAction.value,
      margin: margin.value,
      smooth: smooth.value,
      input_file: selectedFile.value ?? "",
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
    if (!selectedFile.value) {
      commandPreview.value = ""
      return
    }

    validating.value = true
    const params = buildParams()

    const res = await call<{ argv: string[]; display: string }>(
      "preview_auto_editor_command",
      params,
    )

    validating.value = false

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
  }

  async function addToQueue(): Promise<boolean> {
    if (!selectedFile.value) {
      alertMessage.value = "noFileSelected"
      alertType.value = "error"
      clearAlert()
      return false
    }

    const params = buildParams()
    const res = await call<{ task_id: string }>(
      "add_auto_editor_task",
      selectedFile.value,
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
     whenNormalAction, margin, smooth, speedValue, volumeValue,
     selectedFile, advancedOptions],
    () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(updatePreview, PREVIEW_DEBOUNCE_MS)
    },
  )

  // --- Event listener for version changes ---
  function setupEventListeners(): () => void {
    return onEvent<{ version: string; path: string; status: string }>(
      "auto_editor_version_changed",
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
    await fetchStatus()
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
    speedValue,
    volumeValue,
    advancedOptions,
    encoderLists,
    commandPreview,
    selectedFile,
    autoEditorStatus,
    validating,
    alertMessage,
    alertType,
    // Methods
    fetchStatus,
    setPath,
    fetchEncoders,
    updatePreview,
    addToQueue,
    buildParams,
    // Lifecycle
    init,
    dispose,
  }
}
