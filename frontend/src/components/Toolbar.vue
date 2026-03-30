<script setup lang="ts">
import { ref } from "vue";
import { call } from "../bridge";

const emit = defineEmits<{
  filesAdded: [paths: string[]];
  clearAll: [];
  removeSelected: [];
}>();

const errorMsg = ref("");

async function selectFiles() {
  errorMsg.value = "";
  try {
    const res = await call<string[]>("select_files");
    if (res.success && res.data && res.data.length > 0) {
      emit("filesAdded", res.data);
    } else if (!res.success && res.error) {
      errorMsg.value = res.error;
      console.error("[select_files] error:", res.error);
    }
  } catch (err) {
    errorMsg.value = String(err);
    console.error("[select_files] exception:", err);
  }
}

function clear() {
  emit("clearAll");
}
</script>

<template>
  <div class="flex items-center gap-2 px-4 py-2">
    <button class="btn btn-primary btn-sm" @click="selectFiles">
      Add Files
    </button>
    <button class="btn btn-ghost btn-sm" @click="emit('removeSelected')">
      Remove Selected
    </button>
    <button class="btn btn-ghost btn-sm" @click="clear">
      Clear
    </button>
    <span v-if="errorMsg" class="text-xs text-error" :title="errorMsg">
      {{ errorMsg.slice(0, 60) }}
    </span>
  </div>
</template>
