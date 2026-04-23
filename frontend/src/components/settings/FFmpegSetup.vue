<script setup lang="ts">
/**
 * FFmpeg status display and version management.
 *
 * Shows current FFmpeg status, version list for switching,
 * auto-detect and manual select buttons.
 */
import { computed } from "vue"
import type { FfmpegVersionDTO } from "../../composables/useSettings"

const props = defineProps<{
  versions: FfmpegVersionDTO[]
  status: "ready" | "not_found" | "detecting"
  currentVersion: string | null
}>()

const emit = defineEmits<{
  detect: []
  selectBinary: []
  switch: [path: string]
  download: []
}>()

const statusBadge = computed(() => {
  switch (props.status) {
    case "ready":
      return { class: "badge-success", text: "Ready" }
    case "not_found":
      return { class: "badge-error", text: "Not Found" }
    case "detecting":
      return { class: "badge-warning", text: "Detecting..." }
  }
})
</script>

<template>
  <div class="space-y-3">
    <h3 class="text-lg font-semibold">FFmpeg</h3>

    <!-- Status bar -->
    <div class="flex items-center gap-3">
      <span :class="['badge badge-sm', statusBadge.class]">
        {{ statusBadge.text }}
      </span>
      <span v-if="currentVersion" class="text-sm opacity-70">
        v{{ currentVersion }}
      </span>
    </div>

    <!-- Actions -->
    <div class="flex flex-wrap gap-2">
      <button
        class="btn btn-xs btn-primary btn-outline"
        :disabled="status === 'detecting'"
        @click="emit('detect')"
      >
        Auto Detect
      </button>
      <button
        class="btn btn-xs btn-outline"
        @click="emit('selectBinary')"
      >
        Select...
      </button>
      <button
        v-if="versions.length === 0 && status !== 'detecting'"
        class="btn btn-xs btn-accent btn-outline"
        @click="emit('download')"
      >
        Download FFmpeg
      </button>
    </div>

    <!-- Version list -->
    <div v-if="versions.length > 0" class="space-y-1">
      <p class="text-xs font-medium opacity-60">Available versions:</p>
      <div
        v-for="ver in versions"
        :key="ver.path"
        class="flex items-center gap-3 rounded-lg px-3 py-2 cursor-pointer transition-colors"
        :class="ver.active ? 'bg-primary/10 border border-primary/30' : 'hover:bg-base-200'"
        @click="emit('switch', ver.path)"
      >
        <!-- Radio indicator -->
        <div
          class="h-4 w-4 rounded-full border-2 flex items-center justify-center"
          :class="ver.active ? 'border-primary bg-primary' : 'border-base-content/30'"
        >
          <div v-if="ver.active" class="h-1.5 w-1.5 rounded-full bg-base-100" />
        </div>

        <!-- Info -->
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="badge badge-xs" :class="ver.active ? 'badge-primary' : 'badge-ghost'">
              {{ ver.source }}
            </span>
            <span class="text-sm font-medium">
              FFmpeg {{ ver.version }}
            </span>
          </div>
          <p class="text-xs opacity-50 truncate" :title="ver.path">
            {{ ver.path }}
          </p>
        </div>
      </div>
    </div>

    <p v-else-if="status !== 'detecting'" class="text-xs opacity-40">
      No FFmpeg versions found. Click "Auto Detect" or "Select..." to set up FFmpeg.
    </p>
  </div>
</template>
