<script setup lang="ts">
/**
 * Read-only application information display.
 */
import type { AppInfoDTO } from "../../composables/useSettings"

defineProps<{
  info: AppInfoDTO | null
}>()

const items: { label: string; key: keyof AppInfoDTO }[] = [
  { label: "App Version", key: "app_version" },
  { label: "Python Version", key: "python_version" },
  { label: "FFmpeg Version", key: "ffmpeg_version" },
  { label: "FFprobe Version", key: "ffprobe_version" },
  { label: "Platform", key: "is_packaged" },
]
</script>

<template>
  <div class="space-y-3">
    <h3 class="text-lg font-semibold">About</h3>

    <div v-if="info" class="space-y-1.5">
      <div v-for="item in items" :key="item.key" class="flex justify-between text-sm">
        <span class="opacity-60">{{ item.label }}</span>
        <span class="font-mono">
          <template v-if="item.key === 'is_packaged'">
            {{ info[item.key] ? "Packaged" : "Dev" }}
          </template>
          <template v-else-if="info[item.key]">
            {{ info[item.key] }}
          </template>
          <span v-else class="opacity-40">N/A</span>
        </span>
      </div>
    </div>

    <p v-else class="text-xs opacity-40">Loading...</p>
  </div>
</template>
