<script setup lang="ts">
/**
 * File list with drag-and-drop reordering.
 *
 * Supports add, remove, move up/down, and HTML5 drag-and-drop.
 * Phase 3.5.2: add deduplication, fullscreen drag-drop.
 */

import { ref, onMounted, onUnmounted, watch } from "vue"
import { useI18n } from "vue-i18n"
import { call } from "../../bridge"

const { t } = useI18n()

let alertTimer: ReturnType<typeof setTimeout> | null = null

const props = defineProps<{
  modelValue: string[]
}>()

const emit = defineEmits<{
  "update:modelValue": [value: string[]]
}>()

const draggedIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
const isFullscreenDragging = ref(false)
let fsDragCounter = 0
let nextKeyId = 0
const fileKeyMap = new Map<string, number>()

function getFileKey(path: string): number {
  if (!fileKeyMap.has(path)) {
    fileKeyMap.set(path, ++nextKeyId)
  }
  return fileKeyMap.get(path)!
}

// Clean up keys for removed files
watch(() => props.modelValue, (list) => {
  const currentPaths = new Set(list)
  for (const path of fileKeyMap.keys()) {
    if (!currentPaths.has(path)) {
      fileKeyMap.delete(path)
    }
  }
})

function emitUpdate(list: string[]) {
  emit("update:modelValue", [...list])
}

const alertMessage = ref("")

async function addFiles() {
  try {
    const res = await call<string[]>("select_files")
    if (res.success && res.data && res.data.length > 0) {
      emitUpdate([...props.modelValue, ...res.data])
    }
  } catch (err) {
    alertMessage.value = t("common.operationFailed") + ": " + (err as Error).message
    if (alertTimer) clearTimeout(alertTimer)
    alertTimer = setTimeout(() => { alertMessage.value = "" }, 3000)
  }
}

function removeFile(index: number) {
  const list = [...props.modelValue]
  list.splice(index, 1)
  emitUpdate(list)
}

function moveUp(index: number) {
  if (index <= 0) return
  const list = [...props.modelValue]
  ;[list[index - 1], list[index]] = [list[index], list[index - 1]]
  emitUpdate(list)
}

function moveDown(index: number) {
  if (index >= props.modelValue.length - 1) return
  const list = [...props.modelValue]
  ;[list[index], list[index + 1]] = [list[index + 1], list[index]]
  emitUpdate(list)
}

function onDragStart(index: number) {
  draggedIndex.value = index
  dragOverIndex.value = null
}

function onDragOver(e: DragEvent, index: number) {
  e.preventDefault()
  if (draggedIndex.value === null || draggedIndex.value === index) return
  // Only update visual indicator, don't modify reactive data during dragover
  dragOverIndex.value = index
}

function onDragEnd() {
  // Only emit the final position when drag ends
  if (draggedIndex.value !== null && dragOverIndex.value !== null && draggedIndex.value !== dragOverIndex.value) {
    const list = [...props.modelValue]
    const item = list.splice(draggedIndex.value, 1)[0]
    list.splice(dragOverIndex.value, 0, item)
    emitUpdate(list)
  }
  draggedIndex.value = null
  dragOverIndex.value = null
}

function getFileName(path: string): string {
  return path.split(/[/\\]/).pop() ?? path
}

// Fullscreen drag-drop handlers
function onFsDragEnter(e: DragEvent) {
  e.preventDefault()
  fsDragCounter++
  if (fsDragCounter === 1) isFullscreenDragging.value = true
}

function onFsDragOver(e: DragEvent) {
  e.preventDefault()
}

function onFsDragLeave(e: DragEvent) {
  e.preventDefault()
  fsDragCounter--
  if (fsDragCounter === 0) isFullscreenDragging.value = false
}

async function onFsDrop(e: DragEvent) {
  e.preventDefault()
  isFullscreenDragging.value = false
  fsDragCounter = 0
  // Wait for pywebvue's document-level _on_drop to process
  await new Promise((resolve) => setTimeout(resolve, 80))
  const res = await call<string[]>("get_dropped_files")
  if (res.success && res.data && res.data.length > 0) {
    emitUpdate([...props.modelValue, ...res.data])
  }
}

onMounted(() => {
  document.addEventListener("dragenter", onFsDragEnter)
  document.addEventListener("dragover", onFsDragOver)
  document.addEventListener("dragleave", onFsDragLeave)
  document.addEventListener("drop", onFsDrop)
})

onUnmounted(() => {
  if (alertTimer) clearTimeout(alertTimer)
  fsDragCounter = 0
  document.removeEventListener("dragenter", onFsDragEnter)
  document.removeEventListener("dragover", onFsDragOver)
  document.removeEventListener("dragleave", onFsDragLeave)
  document.removeEventListener("drop", onFsDrop)
})
</script>

<template>
  <div class="space-y-1">
    <div v-if="alertMessage" class="alert alert-error py-1 px-3 text-xs">{{ alertMessage }}</div>
    <!-- Fullscreen drag overlay -->
    <div
      v-if="isFullscreenDragging"
      class="pointer-events-none fixed inset-0 z-50 flex items-center justify-center bg-primary/10"
    >
      <div class="rounded-xl border-2 border-dashed border-primary bg-base-100/80 px-12 py-8 text-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-10 w-10 text-primary mb-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p class="text-lg font-semibold text-primary">{{ t("mergePage.fileList.dropVideoFilesHere") }}</p>
      </div>
    </div>

    <!-- File list -->
    <div class="space-y-1">
      <div
        v-for="(file, index) in modelValue"
        :key="getFileKey(file)"
        class="flex items-center gap-2 rounded-lg border border-base-300 px-3 py-1.5 text-sm transition-colors"
        :class="{
          'opacity-50': draggedIndex === index && dragOverIndex !== index,
          'bg-primary/10 border-primary/30': dragOverIndex === index && draggedIndex !== index,
        }"
        draggable="true"
        @dragstart="onDragStart(index)"
        @dragover="onDragOver($event, index)"
        @dragend="onDragEnd"
      >
        <span class="text-xs text-base-content/40 w-6 text-right shrink-0">
          {{ index + 1 }}.
        </span>
        <span
          class="flex-1 truncate"
          :title="file"
        >
          {{ getFileName(file) }}
        </span>
        <div class="flex gap-0.5 shrink-0">
          <button
            class="btn btn-xs btn-ghost btn-square"
            :title="t('mergePage.fileList.moveUp')"
            :disabled="index === 0"
            @click="moveUp(index)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd" />
            </svg>
          </button>
          <button
            class="btn btn-xs btn-ghost btn-square"
            :title="t('mergePage.fileList.moveDown')"
            :disabled="index === modelValue.length - 1"
            @click="moveDown(index)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
          <button
            class="btn btn-xs btn-ghost btn-square text-error"
            :title="t('mergePage.fileList.remove')"
            @click="removeFile(index)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Add button -->
    <button
      class="btn btn-sm btn-outline btn-primary w-full"
      @click="addFiles"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
      </svg>
      {{ t("mergePage.fileList.addFiles") }}
    </button>

    <!-- Hint -->
    <p v-if="modelValue.length < 2" class="text-xs text-warning">
      {{ t("mergePage.fileList.minFilesWarning") }}
    </p>
    <p class="text-xs text-base-content/40 mt-1">
      {{ t("mergePage.fileList.dragDropHint") }}
    </p>
  </div>
</template>
