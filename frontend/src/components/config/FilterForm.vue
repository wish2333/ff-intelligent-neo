<script setup lang="ts">
/**
 * Filter configuration form.
 *
 * Controls for rotate, crop, watermark, volume, and speed adjustments.
 */

import type { FilterConfigDTO } from "../../types/config"

defineProps<{
  config: FilterConfigDTO
}>()

const ROTATE_OPTIONS = [
  { value: "", label: "None" },
  { value: "transpose=1", label: "Clockwise 90" },
  { value: "transpose=2", label: "Clockwise 180" },
  { value: "transpose=3", label: "Clockwise 270" },
]

const WATERMARK_POSITIONS = [
  { value: "top-left", label: "Top Left" },
  { value: "top-right", label: "Top Right" },
  { value: "bottom-left", label: "Bottom Left" },
  { value: "bottom-right", label: "Bottom Right" },
]
</script>

<template>
  <div class="card bg-base-200 shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title text-sm font-semibold mb-3">Filters</h2>

      <!-- Rotate -->
      <div class="form-control mb-3">
        <label class="label py-1">
          <span class="label-text text-xs">Rotate</span>
        </label>
        <select
          v-model="config.rotate"
          class="select select-bordered select-sm w-full"
        >
          <option
            v-for="opt in ROTATE_OPTIONS"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </option>
        </select>
      </div>

      <!-- Crop -->
      <div class="form-control mb-3">
        <label class="label py-1">
          <span class="label-text text-xs">Crop</span>
        </label>
        <input
          v-model="config.crop"
          type="text"
          placeholder="W:H:X:Y e.g. 1920:800:0:140"
          class="input input-bordered input-sm w-full"
        />
        <label class="label py-0.5">
          <span class="label-text-alt text-xs text-base-content/50">
            Leave empty to skip cropping
          </span>
        </label>
      </div>

      <!-- Divider -->
      <div class="divider my-2 text-xs">Watermark</div>

      <!-- Watermark Path -->
      <div class="form-control mb-3">
        <label class="label py-1">
          <span class="label-text text-xs">Watermark Image Path</span>
        </label>
        <input
          v-model="config.watermark_path"
          type="text"
          placeholder="Absolute path to watermark image"
          class="input input-bordered input-sm w-full"
        />
      </div>

      <!-- Watermark Position -->
      <div v-if="config.watermark_path" class="form-control mb-3">
        <label class="label py-1">
          <span class="label-text text-xs">Position</span>
        </label>
        <select
          v-model="config.watermark_position"
          class="select select-bordered select-sm w-full"
        >
          <option
            v-for="pos in WATERMARK_POSITIONS"
            :key="pos.value"
            :value="pos.value"
          >
            {{ pos.label }}
          </option>
        </select>
      </div>

      <!-- Watermark Margin -->
      <div v-if="config.watermark_path" class="form-control mb-3">
        <label class="label py-1">
          <span class="label-text text-xs">Margin (px)</span>
        </label>
        <input
          v-model.number="config.watermark_margin"
          type="number"
          min="0"
          max="100"
          class="input input-bordered input-sm w-full"
        />
      </div>

      <!-- Divider -->
      <div class="divider my-2 text-xs">Audio/Speed</div>

      <!-- Volume -->
      <div class="form-control mb-3">
        <label class="label py-1">
          <span class="label-text text-xs">Volume</span>
        </label>
        <input
          v-model="config.volume"
          type="text"
          placeholder="e.g. 1.5 (boost), 0.5 (reduce)"
          class="input input-bordered input-sm w-full"
        />
        <label class="label py-0.5">
          <span class="label-text-alt text-xs text-base-content/50">
            Leave empty for original volume
          </span>
        </label>
      </div>

      <!-- Speed -->
      <div class="form-control">
        <label class="label py-1">
          <span class="label-text text-xs">Speed</span>
        </label>
        <input
          v-model="config.speed"
          type="text"
          placeholder="e.g. 2.0 (faster), 0.5 (slower)"
          class="input input-bordered input-sm w-full"
        />
        <label class="label py-0.5">
          <span class="label-text-alt text-xs text-base-content/50">
            Leave empty for original speed (range 0.25 - 100)
          </span>
        </label>
      </div>
    </div>
  </div>
</template>
