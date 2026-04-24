<script setup lang="ts">
import { call } from "../../bridge"
import { useI18n } from "vue-i18n"

defineProps<{
  value: string
}>()

const emit = defineEmits<{
  change: [value: string]
}>()

const { t } = useI18n()

function handleRadioChange(event: Event): void {
  const target = event.target as HTMLInputElement
  if (target.value === "same") {
    emit("change", "")
  }
}

async function handleBrowse(): Promise<void> {
  const res = await call<string>("select_output_dir")
  if (res.success && res.data) {
    emit("change", res.data)
  }
}

function handleInputChange(event: Event): void {
  const target = event.target as HTMLInputElement
  emit("change", target.value)
}
</script>

<template>
  <div class="space-y-3">
    <h3 class="text-lg font-semibold">{{ t("settings.output.title") }}</h3>

    <div class="space-y-2">
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="radio"
          name="output-mode"
          value="same"
          :checked="!value"
          class="radio radio-sm radio-primary"
          @change="handleRadioChange"
        />
        <span class="text-sm">{{ t("settings.output.sameAsSource") }}</span>
      </label>

      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="radio"
          name="output-mode"
          value="custom"
          :checked="!!value"
          class="radio radio-sm radio-primary"
          @change="() => {}"
        />
        <span class="text-sm">{{ t("settings.output.customFolder") }}</span>
      </label>

      <div v-if="!!value" class="flex items-center gap-2 ml-6">
        <input
          type="text"
          :value="value"
          class="input input-bordered input-sm flex-1"
          :placeholder="t('settings.output.placeholder')"
          @change="handleInputChange"
        />
        <button class="btn btn-xs btn-outline" @click="handleBrowse">
          {{ t("settings.output.browse") }}
        </button>
      </div>

      <div v-else class="ml-6">
        <button class="btn btn-xs btn-outline" @click="handleBrowse">
          {{ t("settings.output.selectFolder") }}
        </button>
      </div>
    </div>
  </div>
</template>
