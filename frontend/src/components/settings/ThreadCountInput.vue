<script setup lang="ts">
import { useI18n } from "vue-i18n"

defineProps<{
  value: number
}>()

const emit = defineEmits<{
  change: [value: number]
}>()

const { t } = useI18n()

function handleInput(event: Event): void {
  const target = event.target as HTMLInputElement
  let val = parseInt(target.value, 10)
  if (isNaN(val) || val < 1) val = 1
  if (val > 4) val = 4
  emit("change", val)
}
</script>

<template>
  <div class="space-y-3">
    <h3 class="text-lg font-semibold">{{ t("settings.concurrency.title") }}</h3>

    <div class="flex items-center gap-3">
      <label class="text-sm">{{ t("settings.concurrency.maxWorkers") }}</label>
      <input
        type="number"
        :value="value"
        min="1"
        max="4"
        class="input input-bordered input-sm w-20 text-center"
        @change="handleInput"
      />
    </div>

    <div class="flex gap-2">
      <button
        v-for="n in [1, 2, 3, 4]"
        :key="n"
        class="btn btn-xs"
        :class="value === n ? 'btn-primary' : 'btn-ghost'"
        @click="emit('change', n)"
      >
        {{ n }}
      </button>
    </div>

    <p class="text-xs opacity-50">
      {{ t("settings.concurrency.description") }}
    </p>
  </div>
</template>
