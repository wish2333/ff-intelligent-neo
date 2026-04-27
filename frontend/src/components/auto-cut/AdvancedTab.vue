<script setup lang="ts">
/**
 * AdvancedTab - Auto-editor advanced parameters.
 *
 * Sections: Actions, Timeline, Container switches, Video params, Audio params, Output.
 * Range lists support add/remove.
 *
 * v2.2.0 Phase 4.
 */

import { useI18n } from "vue-i18n"
import type { AdvancedOptions } from "../../types/autoEditor"

const { t } = useI18n()

const props = defineProps<{
  advancedOptions: AdvancedOptions
}>()

const emit = defineEmits<{
  "update:advancedOptions": [value: AdvancedOptions]
}>()

function updateField<K extends keyof AdvancedOptions>(field: K, value: AdvancedOptions[K]) {
  emit("update:advancedOptions", { ...props.advancedOptions, [field]: value })
}

function addRange(field: "cutOutRanges" | "addInRange" | "setActionRanges") {
  emit("update:advancedOptions", {
    ...props.advancedOptions,
    [field]: [...props.advancedOptions[field], ""],
  })
}

function removeRange(field: "cutOutRanges" | "addInRange" | "setActionRanges", index: number) {
  emit("update:advancedOptions", {
    ...props.advancedOptions,
    [field]: props.advancedOptions[field].filter((_: string, i: number) => i !== index),
  })
}

function updateRange(field: "cutOutRanges" | "addInRange" | "setActionRanges", index: number, value: string) {
  emit("update:advancedOptions", {
    ...props.advancedOptions,
    [field]: props.advancedOptions[field].map((v: string, i: number) => i === index ? value : v),
  })
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- Section: Actions -->
    <div class="form-control md:col-span-2">
      <label class="label">
        <span class="label-text font-semibold">{{ t("autoCut.advancedSections.actions") }}</span>
      </label>

      <!-- Cut-out ranges -->
      <div class="mb-3">
        <span class="text-sm text-base-content/70 mb-1 block">{{ t("autoCut.cutOutRanges") }}</span>
        <div class="flex flex-col gap-1">
          <div
            v-for="(range, idx) in advancedOptions.cutOutRanges"
            :key="'cutout-' + idx"
            class="flex items-center gap-2"
          >
            <input
              :value="range"
              type="text"
              class="input input-bordered input-sm flex-1"
              :placeholder="t('autoCut.rangePlaceholder')"
              @input="updateRange('cutOutRanges', idx, ($event.target as HTMLInputElement).value)"
            />
            <button
              class="btn btn-ghost btn-sm btn-square"
              @click="removeRange('cutOutRanges', idx)"
            >
              <span class="text-xs">{{ t("autoCut.removeRange") }}</span>
            </button>
          </div>
          <button class="btn btn-outline btn-sm btn-block" @click="addRange('cutOutRanges')">
            {{ t("autoCut.addRange") }}
          </button>
        </div>
      </div>

      <!-- Add-in ranges -->
      <div class="mb-3">
        <span class="text-sm text-base-content/70 mb-1 block">{{ t("autoCut.addInRange") }}</span>
        <div class="flex flex-col gap-1">
          <div
            v-for="(range, idx) in advancedOptions.addInRange"
            :key="'addin-' + idx"
            class="flex items-center gap-2"
          >
            <input
              :value="range"
              type="text"
              class="input input-bordered input-sm flex-1"
              :placeholder="t('autoCut.rangePlaceholder')"
              @input="updateRange('addInRange', idx, ($event.target as HTMLInputElement).value)"
            />
            <button
              class="btn btn-ghost btn-sm btn-square"
              @click="removeRange('addInRange', idx)"
            >
              <span class="text-xs">{{ t("autoCut.removeRange") }}</span>
            </button>
          </div>
          <button class="btn btn-outline btn-sm btn-block" @click="addRange('addInRange')">
            {{ t("autoCut.addRange") }}
          </button>
        </div>
      </div>

      <!-- Set-action ranges -->
      <div>
        <span class="text-sm text-base-content/70 mb-1 block">{{ t("autoCut.setActionRanges") }}</span>
        <div class="flex flex-col gap-1">
          <div
            v-for="(range, idx) in advancedOptions.setActionRanges"
            :key="'setaction-' + idx"
            class="flex items-center gap-2"
          >
            <input
              :value="range"
              type="text"
              class="input input-bordered input-sm flex-1"
              :placeholder="t('autoCut.setActionPlaceholder')"
              @input="updateRange('setActionRanges', idx, ($event.target as HTMLInputElement).value)"
            />
            <button
              class="btn btn-ghost btn-sm btn-square"
              @click="removeRange('setActionRanges', idx)"
            >
              <span class="text-xs">{{ t("autoCut.removeRange") }}</span>
            </button>
          </div>
          <button class="btn btn-outline btn-sm btn-block" @click="addRange('setActionRanges')">
            {{ t("autoCut.addRange") }}
          </button>
        </div>
      </div>
    </div>

    <!-- Section: Timeline -->
    <div class="form-control">
      <label class="label">
        <span class="label-text font-semibold">{{ t("autoCut.advancedSections.timeline") }}</span>
      </label>
      <input
        :value="advancedOptions.frameRate"
        type="text"
        class="input input-bordered input-sm w-full"
        :placeholder="t('autoCut.frameRateHint')"
        @input="updateField('frameRate', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.sampleRate") }}</span>
      </label>
      <input
        :value="advancedOptions.sampleRate"
        type="text"
        class="input input-bordered input-sm w-full"
        :placeholder="t('autoCut.sampleRateHint')"
        @input="updateField('sampleRate', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <div class="form-control md:col-span-2">
      <label class="label">
        <span class="label-text">{{ t("autoCut.resolution") }}</span>
      </label>
      <input
        :value="advancedOptions.resolution"
        type="text"
        class="input input-bordered input-sm w-full"
        :placeholder="t('autoCut.resolutionHint')"
        @input="updateField('resolution', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <!-- Section: Switches -->
    <div class="form-control md:col-span-2">
      <label class="label">
        <span class="label-text font-semibold">{{ t("autoCut.advancedSections.switches") }}</span>
      </label>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
        <label class="label cursor-pointer gap-2 justify-start"><input type="checkbox" class="toggle toggle-sm toggle-primary" :checked="advancedOptions.vn" @change="updateField('vn', ($event.target as HTMLInputElement).checked)" /><span class="label-text text-sm">{{ t("autoCut.disableVideo") }}</span></label>
        <label class="label cursor-pointer gap-2 justify-start"><input type="checkbox" class="toggle toggle-sm toggle-primary" :checked="advancedOptions.an" @change="updateField('an', ($event.target as HTMLInputElement).checked)" /><span class="label-text text-sm">{{ t("autoCut.disableAudio") }}</span></label>
        <label class="label cursor-pointer gap-2 justify-start"><input type="checkbox" class="toggle toggle-sm toggle-primary" :checked="advancedOptions.sn" @change="updateField('sn', ($event.target as HTMLInputElement).checked)" /><span class="label-text text-sm">{{ t("autoCut.disableSubtitle") }}</span></label>
        <label class="label cursor-pointer gap-2 justify-start"><input type="checkbox" class="toggle toggle-sm toggle-primary" :checked="advancedOptions.dn" @change="updateField('dn', ($event.target as HTMLInputElement).checked)" /><span class="label-text text-sm">{{ t("autoCut.disableData") }}</span></label>
        <label class="label cursor-pointer gap-2 justify-start"><input type="checkbox" class="toggle toggle-sm toggle-primary" :checked="advancedOptions.faststart" @change="updateField('faststart', ($event.target as HTMLInputElement).checked)" /><span class="label-text text-sm">{{ t("autoCut.faststart") }}</span></label>
        <label class="label cursor-pointer gap-2 justify-start"><input type="checkbox" class="toggle toggle-sm toggle-primary" :checked="advancedOptions.fragmented" @change="updateField('fragmented', ($event.target as HTMLInputElement).checked)" /><span class="label-text text-sm">{{ t("autoCut.fragmented") }}</span></label>
        <label class="label cursor-pointer gap-2 justify-start"><input type="checkbox" class="toggle toggle-sm toggle-primary" :checked="advancedOptions.noCache" @change="updateField('noCache', ($event.target as HTMLInputElement).checked)" /><span class="label-text text-sm">{{ t("autoCut.noCache") }}</span></label>
        <label class="label cursor-pointer gap-2 justify-start"><input type="checkbox" class="toggle toggle-sm toggle-primary" :checked="advancedOptions.open" @change="updateField('open', ($event.target as HTMLInputElement).checked)" /><span class="label-text text-sm">{{ t("autoCut.openAfter") }}</span></label>
      </div>
      <span v-if="advancedOptions.open" class="label-text-alt text-warning text-xs mt-1">{{ t("autoCut.openWarning") }}</span>
    </div>

    <!-- Section: Video params -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.videoBitrate") }}</span>
      </label>
      <input
        :value="advancedOptions.videoBitrate"
        type="text"
        class="input input-bordered input-sm w-full"
        :placeholder="t('autoCut.videoBitrateHint')"
        @input="updateField('videoBitrate', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.crf") }}</span>
      </label>
      <input
        :value="advancedOptions.crf"
        type="text"
        class="input input-bordered input-sm w-full"
        :placeholder="t('autoCut.crfHint')"
        @input="updateField('crf', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <!-- Section: Audio params -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.audioBitrate") }}</span>
      </label>
      <input
        :value="advancedOptions.audioBitrate"
        type="text"
        class="input input-bordered input-sm w-full"
        :placeholder="t('autoCut.audioBitrateHint')"
        @input="updateField('audioBitrate', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.audioLayout") }}</span>
      </label>
      <input
        :value="advancedOptions.audioLayout"
        type="text"
        class="input input-bordered input-sm w-full"
        :placeholder="t('autoCut.audioLayoutHint')"
        @input="updateField('audioLayout', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.audioNormalize") }}</span>
      </label>
      <select
        :value="advancedOptions.audioNormalize"
        class="select select-bordered select-sm w-full"
        @change="updateField('audioNormalize', ($event.target as HTMLSelectElement).value)"
      >
        <option value=""></option>
        <option value="none">{{ t("autoCut.normalizeNone") }}</option>
        <option value="peak">{{ t("autoCut.normalizePeak") }}</option>
        <option value="ebu">{{ t("autoCut.normalizeEbu") }}</option>
      </select>
    </div>

    <!-- Output -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">{{ t("autoCut.outputExtension") }}</span>
      </label>
      <select
        :value="advancedOptions.outputExtension"
        class="select select-bordered select-sm w-full"
        @change="updateField('outputExtension', ($event.target as HTMLSelectElement).value)"
      >
        <option value=".mp4">.mp4</option>
        <option value=".mkv">.mkv</option>
        <option value=".mov">.mov</option>
      </select>
    </div>
  </div>
</template>
