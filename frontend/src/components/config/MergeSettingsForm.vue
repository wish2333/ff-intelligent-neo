<script setup lang="ts">
/**
 * Merge settings form for Config page.
 *
 * Batch intro/outro configuration.
 * When set, ALL tasks added to the queue will have intro/outro prepended/appended.
 */

import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { call } from "../../bridge"
import type { MergeConfigDTO } from "../../types/config"
import SplitDropZone from "../common/SplitDropZone.vue"

const { t } = useI18n()

const props = defineProps<{
  config: MergeConfigDTO
}>()

// Split target_resolution "WxH" into two number inputs
const mergeWidth = computed({
  get: () => {
    const res = props.config.target_resolution
    if (!res) return 1920
    return parseInt(res.split("x")[0]) || 1920
  },
  set: (val: number | undefined) => {
    const w = val || 1920
    const h = mergeHeight.value || 1080
    props.config.target_resolution = `${w}x${h}`
  },
})

const mergeHeight = computed({
  get: () => {
    const res = props.config.target_resolution
    if (!res) return 1080
    return parseInt(res.split("x")[1]) || 1080
  },
  set: (val: number | undefined) => {
    const w = mergeWidth.value || 1920
    const h = val || 1080
    props.config.target_resolution = `${w}x${h}`
  },
})

function handleDropIntro(path: string) {
  props.config.intro_path = path
}

function handleDropOutro(path: string) {
  props.config.outro_path = path
}

async function handleClickIntro() {
  const res = await call<string[]>("select_files")
  if (res.success && res.data && res.data.length > 0) {
    props.config.intro_path = res.data[0]
  }
}

async function handleClickOutro() {
  const res = await call<string[]>("select_files")
  if (res.success && res.data && res.data.length > 0) {
    props.config.outro_path = res.data[0]
  }
}
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title text-sm font-semibold mb-3">{{ t("config.mergeSettings.title") }}</h2>
      <p class="text-xs text-base-content/60 mb-3">
        {{ t("config.mergeSettings.description") }}
      </p>

      <!-- Intro / Outro -->
      <SplitDropZone
        :left-label="t('config.mergeSettings.introVideo')"
        :right-label="t('config.mergeSettings.outroVideo')"
        left-accept=".mp4,.mkv,.avi,.mov,.ts,.m2ts"
        right-accept=".mp4,.mkv,.avi,.mov,.ts,.m2ts"
        @drop-left="handleDropIntro"
        @drop-right="handleDropOutro"
      >
        <template #left>
          <div class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">{{ t("config.mergeSettings.introVideo") }}</span>
            </label>
            <div
              class="rounded-lg border border-dashed px-3 py-6 text-center text-sm cursor-pointer border-base-300 hover:border-primary/50 hover:bg-base-200/50 transition-colors"
              @click="handleClickIntro"
            >
              <span v-if="config.intro_path" class="truncate block" :title="config.intro_path">
                {{ config.intro_path.split(/[/\\]/).pop() }}
              </span>
              <span v-else class="opacity-40">
                {{ t("config.mergeSettings.clickOrDragIntro") }}
              </span>
            </div>
            <div v-if="config.intro_path" class="flex justify-end mt-1">
              <button class="btn btn-xs btn-ghost text-error" @click.stop="config.intro_path = ''">{{ t("common.clear") }}</button>
            </div>
          </div>
        </template>
        <template #right>
          <div class="form-control">
            <label class="label py-1">
              <span class="label-text text-xs">{{ t("config.mergeSettings.outroVideo") }}</span>
            </label>
            <div
              class="rounded-lg border border-dashed px-3 py-6 text-center text-sm cursor-pointer border-base-300 hover:border-primary/50 hover:bg-base-200/50 transition-colors"
              @click="handleClickOutro"
            >
              <span v-if="config.outro_path" class="truncate block" :title="config.outro_path">
                {{ config.outro_path.split(/[/\\]/).pop() }}
              </span>
              <span v-else class="opacity-40">
                {{ t("config.mergeSettings.clickOrDragOutro") }}
              </span>
            </div>
            <div v-if="config.outro_path" class="flex justify-end mt-1">
              <button class="btn btn-xs btn-ghost text-error" @click.stop="config.outro_path = ''">{{ t("common.clear") }}</button>
            </div>
          </div>
        </template>
      </SplitDropZone>

      <div class="mt-3 text-xs text-base-content/50">
        <p v-if="config.intro_path || config.outro_path" class="text-primary">
          {{ t("config.mergeSettings.activeNotice") }}
        </p>
        <p v-else>
          {{ t("config.mergeSettings.inactiveNotice") }}
        </p>
      </div>
    </div>
  </div>
</template>
