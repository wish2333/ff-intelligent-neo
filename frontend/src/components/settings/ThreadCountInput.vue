<script setup lang="ts">
/**
 * Max concurrent workers setting.
 */
defineProps<{
  value: number
}>()

const emit = defineEmits<{
  change: [value: number]
}>()

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
    <h3 class="text-lg font-semibold">Concurrency</h3>

    <div class="flex items-center gap-3">
      <label class="text-sm">Max workers:</label>
      <input
        type="number"
        :value="value"
        min="1"
        max="4"
        class="input input-bordered input-sm w-20 text-center"
        @change="handleInput"
      />
    </div>

    <!-- Quick select buttons -->
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
      Maximum number of tasks running simultaneously. Recommend not exceeding CPU core count.
    </p>
  </div>
</template>
