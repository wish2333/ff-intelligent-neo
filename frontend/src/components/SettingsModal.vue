<script setup lang="ts">
export interface AppInfo {
  app_name: string;
  app_version: string;
  python_version: string;
  ffmpeg_path: string;
  ffmpeg_version: string | null;
  ffprobe_path: string;
  ffprobe_version: string | null;
  is_packaged: boolean;
}

defineProps<{
  visible: boolean;
  appInfo: AppInfo | null;
}>();

const emit = defineEmits<{
  close: [];
}>();
</script>

<template>
  <dialog
    class="modal"
    :class="{ 'modal-open': visible }"
    @click.self="emit('close')"
  >
    <div class="modal-box max-w-lg">
      <h3 class="text-lg font-bold">About / Settings</h3>

      <div v-if="appInfo" class="mt-4 space-y-4">
        <!-- App info -->
        <div class="form-control">
          <label class="label"><span class="label-text font-semibold">Application</span></label>
          <div class="bg-base-200 rounded-lg p-3 text-sm space-y-1">
            <div class="flex justify-between">
              <span class="text-base-content/60">Name</span>
              <span>{{ appInfo.app_name }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-base-content/60">Version</span>
              <span>{{ appInfo.app_version }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-base-content/60">Python</span>
              <span>{{ appInfo.python_version }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-base-content/60">Mode</span>
              <span :class="appInfo.is_packaged ? 'badge badge-success badge-sm' : 'badge badge-warning badge-sm'">
                {{ appInfo.is_packaged ? 'Packaged' : 'Development' }}
              </span>
            </div>
          </div>
        </div>

        <!-- FFmpeg info -->
        <div class="form-control">
          <label class="label"><span class="label-text font-semibold">FFmpeg</span></label>
          <div class="bg-base-200 rounded-lg p-3 text-sm space-y-1">
            <div class="flex justify-between">
              <span class="text-base-content/60">Status</span>
              <span :class="appInfo.ffmpeg_version ? 'badge badge-success badge-sm' : 'badge badge-error badge-sm'">
                {{ appInfo.ffmpeg_version ? `${appInfo.ffmpeg_version}` : 'Not Found' }}
              </span>
            </div>
            <div v-if="appInfo.ffmpeg_path">
              <span class="text-base-content/60">Path</span>
              <div class="text-xs break-all mt-0.5 opacity-70">{{ appInfo.ffmpeg_path }}</div>
            </div>
          </div>
        </div>

        <!-- FFprobe info -->
        <div class="form-control">
          <label class="label"><span class="label-text font-semibold">FFprobe</span></label>
          <div class="bg-base-200 rounded-lg p-3 text-sm space-y-1">
            <div class="flex justify-between">
              <span class="text-base-content/60">Status</span>
              <span :class="appInfo.ffprobe_version ? 'badge badge-success badge-sm' : 'badge badge-error badge-sm'">
                {{ appInfo.ffprobe_version ? `${appInfo.ffprobe_version}` : 'Not Found' }}
              </span>
            </div>
            <div v-if="appInfo.ffprobe_path">
              <span class="text-base-content/60">Path</span>
              <div class="text-xs break-all mt-0.5 opacity-70">{{ appInfo.ffprobe_path }}</div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="mt-4 text-base-content/50">Loading...</div>

      <div class="modal-action">
        <button class="btn btn-sm" @click="emit('close')">Close</button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="emit('close')">close</button>
    </form>
  </dialog>
</template>
