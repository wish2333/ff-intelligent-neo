<script setup lang="ts">
/**
 * Page: Video Merge
 *
 * Independent page for multi-video concatenation.
 * Uses its own local merge config (independent from Config page's merge settings).
 * Inherits only transcode encoder settings from the shared Config state.
 * Default merge mode: concat_protocol.
 */

import { reactive, computed, onMounted } from "vue"
import { useI18n } from "vue-i18n"
import { useRouter } from "vue-router"
import { useGlobalConfig } from "../composables/useGlobalConfig"
import { useCommandPreview } from "../composables/useCommandPreview"
import { useTaskQueue } from "../composables/useTaskQueue"
import MergePanel from "../components/config/MergePanel.vue"
import CommandPreview from "../components/config/CommandPreview.vue"
import type { MergeConfigDTO, TaskConfigDTO } from "../types/config"

const { t } = useI18n()

const router = useRouter()
const { transcode, filters, activeMode } = useGlobalConfig()
const queue = useTaskQueue()

// Local merge config - independent from Config page's merge settings
const mergeConfig = reactive<MergeConfigDTO>({
  merge_mode: "concat_protocol",
  target_resolution: "1920x1080",
  target_fps: 30,
  file_list: [],
  intro_path: "",
  outro_path: "",
})

// Merge page builds its own preview config:
// inherits transcode + filters from shared state, adds its own merge-specific config
const mergePreviewConfig = computed<TaskConfigDTO>(() => ({
  transcode: { ...transcode },
  filters: { ...filters },
  merge: { ...mergeConfig },
  output_dir: "",
}))
const { commandText, errors, warnings, validating } = useCommandPreview(mergePreviewConfig)

const canAddToQueue = computed(() => mergeConfig.file_list.length >= 2)

onMounted(() => {
  activeMode.value = "merge"
})

async function handleAddToQueue(): Promise<void> {
  if (!canAddToQueue.value) return
  // Build CLEAN merge-only config: inherits transcode/filters but NOT global merge (intro/outro)
  // MergePage uses its OWN merge config completely independently
  const taskCfg: TaskConfigDTO = {
    transcode: { ...transcode },
    filters: { ...filters },
    merge: { ...mergeConfig },
    output_dir: "",
  }
  // Merge adds ONE task with the merge.file_list embedded in the config
  const added = await queue.addTasks([mergeConfig.file_list[0]], taskCfg)
  if (added.length > 0) {
    router.push("/task-queue")
  }
}
</script>

<template>
  <div class="flex flex-1 flex-col gap-4 p-4 overflow-y-auto">
    <h1 class="text-xl font-bold tracking-tight">{{ t("mergePage.title") }}</h1>
    <p class="text-sm text-base-content/60">
      {{ t("mergePage.description") }}
    </p>

    <CommandPreview
      :command-text="commandText"
      :errors="errors"
      :warnings="warnings"
      :validating="validating"
    />

    <MergePanel :config="mergeConfig" />

    <!-- Add to Queue -->
    <div class="flex justify-end">
      <button
        class="btn btn-primary btn-sm"
        :disabled="!canAddToQueue"
        @click="handleAddToQueue"
      >
        {{ t("mergePage.addToQueue", { count: mergeConfig.file_list.length }) }}
      </button>
    </div>
  </div>
</template>
