<script setup lang="ts">
import type { FileItemDTO } from "../composables/useFileQueue";
import type { TaskProgressData } from "../composables/useBatchProcess";

defineProps<{
  file: FileItemDTO;
  index: number;
  selected: boolean;
  taskProgress: TaskProgressData | null;
}>();

const emit = defineEmits<{
  toggle: [index: number, shiftKey: boolean, ctrlKey: boolean];
}>();

function formatDuration(seconds: number): string {
  if (!seconds) return "--:--";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatSize(bytes: number): string {
  if (!bytes) return "--";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let size = bytes;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i++;
  }
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function resolution(f: FileItemDTO): string {
  if (f.width && f.height) return `${f.width}x${f.height}`;
  return "--";
}

function codecs(f: FileItemDTO): string {
  const parts: string[] = [];
  if (f.video_codec) parts.push(f.video_codec);
  if (f.audio_codec) parts.push(f.audio_codec);
  return parts.length ? parts.join(" / ") : "--";
}
</script>

<template>
  <tr
    class="hover cursor-pointer"
    :class="{ 'bg-primary/10': selected }"
    @click="emit('toggle', index, $event.shiftKey, $event.ctrlKey || $event.metaKey)"
  >
    <td>
      <input
        type="checkbox"
        class="checkbox checkbox-sm checkbox-primary"
        :checked="selected"
        @click.stop
        @change="emit('toggle', index, ($event as MouseEvent).shiftKey, ($event as MouseEvent).ctrlKey)"
      />
    </td>
    <td class="max-w-xs truncate" :title="file.path">{{ file.name }}</td>
    <td>{{ formatDuration(file.duration_seconds) }}</td>
    <td>{{ codecs(file) }}</td>
    <td>{{ resolution(file) }}</td>
    <td class="text-right">{{ formatSize(file.size_bytes) }}</td>
    <td>
      <!-- Done status -->
      <span v-if="taskProgress?.status === 'done'" class="badge badge-success badge-sm gap-1">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        Done
      </span>
      <!-- Error status -->
      <span v-else-if="taskProgress?.status === 'error'" class="badge badge-error badge-sm gap-1">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
        Error
      </span>
      <!-- Running status -->
      <span v-else-if="taskProgress?.status === 'running'" class="badge badge-info badge-sm gap-1">
        <span class="loading loading-spinner loading-xs"></span>
        {{ taskProgress.percent.toFixed(0) }}%
      </span>
    </td>
  </tr>
</template>
