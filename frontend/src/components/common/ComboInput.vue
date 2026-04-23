<script setup lang="ts">
/**
 * Combobox input with dropdown suggestions.
 *
 * Combines a text input with a clickable dropdown arrow.
 * Typing filters the suggestion list; clicking the arrow shows all.
 * Selecting a suggestion fills the input; custom text is always allowed.
 */
import { ref, computed, onMounted, onBeforeUnmount } from "vue"

const props = withDefaults(defineProps<{
  modelValue: string
  suggestions: string[]
  placeholder?: string
}>(), {
  placeholder: "",
})

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void
}>()

const isOpen = ref(false)
const showAll = ref(false)
const wrapperRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)

const items = computed(() => {
  if (showAll.value || !props.modelValue) return props.suggestions
  const q = props.modelValue.toLowerCase()
  return props.suggestions.filter((s) => s.toLowerCase().includes(q))
})

function select(value: string) {
  emit("update:modelValue", value)
  isOpen.value = false
}

function toggleDropdown() {
  if (isOpen.value) {
    isOpen.value = false
  } else {
    showAll.value = true
    isOpen.value = true
  }
}

function onInputFocus() {
  showAll.value = false
  isOpen.value = true
}

function onInput(e: Event) {
  showAll.value = false
  emit("update:modelValue", (e.target as HTMLInputElement).value)
}

function onClickOutside(e: MouseEvent) {
  if (wrapperRef.value && !wrapperRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener("mousedown", onClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onClickOutside)
})
</script>

<template>
  <div ref="wrapperRef" class="combo-input relative">
    <input
      ref="inputRef"
      :value="modelValue"
      :placeholder="placeholder"
      type="text"
      class="input input-bordered input-sm w-full pr-7"
      @focus="onInputFocus"
      @input="onInput"
    />
    <!-- Dropdown toggle button -->
    <button
      type="button"
      class="absolute right-1 top-1/2 -translate-y-1/2 p-0.5 text-base-content/50 hover:text-base-content/80"
      tabindex="-1"
      @click.prevent="toggleDropdown"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
      </svg>
    </button>

    <!-- Dropdown list -->
    <ul
      v-if="isOpen && items.length > 0"
      class="absolute z-50 mt-1 max-h-48 w-full overflow-y-auto rounded-md border border-base-300 bg-base-100 shadow-lg"
    >
      <li
        v-for="item in items"
        :key="item"
        class="cursor-pointer px-3 py-1.5 text-sm hover:bg-primary/10"
        :class="{ 'bg-primary/10 font-medium': item === modelValue }"
        @mousedown.prevent="select(item)"
      >
        {{ item }}
      </li>
    </ul>
  </div>
</template>
