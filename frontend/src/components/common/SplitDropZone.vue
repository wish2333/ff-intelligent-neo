<script setup lang="ts">
/**
 * Split-screen fullscreen drag-drop overlay.
 *
 * Wraps two FileDropInput instances (left/right) with a shared
 * document-level drag handler. When dragging starts, a fullscreen
 * split overlay appears. The drop position (left/right half) determines
 * which zone receives the file.
 *
 * Usage:
 *   <SplitDropZone
 *     left-label="Intro Video"
 *     right-label="Outro Video"
 *     left-accept=".mp4,.mkv"
 *     right-accept=".mp4,.mkv"
 *     @drop-left="introPath = $event"
 *     @drop-right="outroPath = $event"
 *   >
 *     <template #left>
 *       <FileDropInput :model-value="introPath" ... />
 *     </template>
 *     <template #right>
 *       <FileDropInput :model-value="outroPath" ... />
 *     </template>
 *   </SplitDropZone>
 */

import { ref, onMounted, onUnmounted } from "vue"
import { call } from "../../bridge"

const props = withDefaults(defineProps<{
  leftLabel?: string
  rightLabel?: string
  leftAccept?: string
  rightAccept?: string
}>(), {
  leftLabel: "Left",
  rightLabel: "Right",
  leftAccept: "",
  rightAccept: "",
})

const emit = defineEmits<{
  "drop-left": [path: string]
  "drop-right": [path: string]
}>()

const isDragging = ref(false)
let dragCounter = 0

function parseExts(accept: string): Set<string> | null {
  if (!accept) return null
  return new Set(accept.split(",").map(e => e.trim().toLowerCase()).filter(Boolean))
}

function validateExtension(path: string, accept: string): boolean {
  const exts = parseExts(accept)
  if (!exts || exts.size === 0) return true
  const dotIdx = path.lastIndexOf(".")
  if (dotIdx === -1) return false
  return exts.has(path.slice(dotIdx).toLowerCase())
}

function onDragEnter(e: DragEvent) {
  e.preventDefault()
  dragCounter++
  if (dragCounter === 1) isDragging.value = true
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
}

function onDragLeave(e: DragEvent) {
  e.preventDefault()
  dragCounter--
  if (dragCounter === 0) isDragging.value = false
}

async function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
  dragCounter = 0

  // Wait for pywebvue's document-level _on_drop to process
  await new Promise(resolve => setTimeout(resolve, 80))
  const res = await call<string[]>("get_dropped_files")
  if (res.success && res.data && res.data.length > 0) {
    const path = res.data[0]
    const clientX = e.clientX ?? (e as any).x ?? 0
    const windowWidth = window.innerWidth
    const isLeft = clientX < windowWidth / 2

    if (isLeft) {
      if (validateExtension(path, props.leftAccept)) {
        emit("drop-left", path)
      }
    } else {
      if (validateExtension(path, props.rightAccept)) {
        emit("drop-right", path)
      }
    }
  }
}

onMounted(() => {
  document.addEventListener("dragenter", onDragEnter)
  document.addEventListener("dragover", onDragOver)
  document.addEventListener("dragleave", onDragLeave)
  document.addEventListener("drop", onDrop)
})

onUnmounted(() => {
  dragCounter = 0
  document.removeEventListener("dragenter", onDragEnter)
  document.removeEventListener("dragover", onDragOver)
  document.removeEventListener("dragleave", onDragLeave)
  document.removeEventListener("drop", onDrop)
})
</script>

<template>
  <div class="relative">
    <!-- Fullscreen split overlay -->
    <div
      v-if="isDragging"
      class="pointer-events-none fixed inset-0 z-50 flex"
    >
      <!-- Left half -->
      <div class="flex-1 flex items-center justify-center border-r-2 border-dashed border-base-content/20 bg-primary/5">
        <div class="rounded-xl border-2 border-dashed border-primary bg-base-100/80 px-8 py-6 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-8 w-8 text-primary mb-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <p class="text-sm font-semibold text-primary">{{ leftLabel }}</p>
        </div>
      </div>
      <!-- Right half -->
      <div class="flex-1 flex items-center justify-center">
        <div class="rounded-xl border-2 border-dashed border-secondary bg-base-100/80 px-8 py-6 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-8 w-8 text-secondary mb-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <p class="text-sm font-semibold text-secondary">{{ rightLabel }}</p>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <slot name="left" />
      <slot name="right" />
    </div>
  </div>
</template>
