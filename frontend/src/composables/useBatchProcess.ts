import { ref, onMounted, onUnmounted } from "vue";
import { onEvent } from "../bridge";

export interface TaskProgressData {
  file_index: number;
  file_name: string;
  percent: number;
  time_str: string;
  status: string;
  error?: string;
  output_path?: string;
  speed?: string;
  fps?: string;
}

export function useBatchProcess() {
  const processing = ref(false);
  const overallProgress = ref(0);
  const overallTotal = ref(0);
  const overallCompleted = ref(0);
  const taskProgressMap = ref<Record<number, TaskProgressData>>({});
  const logLines = ref<string[]>([]);
  const cleanups: (() => void)[] = [];

  // Method to manually set processing state (fallback if event is missed)
  function setProcessing(value: boolean) {
    console.log("[useBatchProcess] setProcessing called:", value);
    processing.value = value;
  }

  onMounted(() => {
    console.log("[useBatchProcess] ✅ Component mounted, registering event listeners");
    console.log("[useBatchProcess] cleanups array length:", cleanups.length);
    cleanups.push(
      onEvent<{ file_index: number; file_name: string }>(
        "task_start",
        (data) => {
          console.log("[useBatchProcess] task_start received:", data);
          processing.value = true;
        },
      ),
      onEvent<{ total: number; completed: number; overall_percent: number }>(
        "batch_progress",
        (data) => {
          console.log("[useBatchProcess] batch_progress received:", data);
          overallTotal.value = data.total;
          overallCompleted.value = data.completed;
          overallProgress.value = data.overall_percent;
        },
      ),
      onEvent<{ file_index: number; file_name: string; percent: number; time_str: string; speed: string; fps: string }>(
        "task_progress",
        (data) => {
          console.log("[useBatchProcess] task_progress received:", data);
          taskProgressMap.value[data.file_index] = {
            file_index: data.file_index,
            file_name: data.file_name,
            percent: data.percent,
            time_str: data.time_str,
            status: "running",
            speed: data.speed,
            fps: data.fps,
          };
          taskProgressMap.value = { ...taskProgressMap.value };
        },
      ),
      onEvent<{ file_index: number; file_name: string; output_path: string }>(
        "task_complete",
        (data) => {
          console.log("[useBatchProcess] task_complete received:", data);
          const existing = taskProgressMap.value[data.file_index];
          taskProgressMap.value[data.file_index] = {
            file_index: data.file_index,
            file_name: data.file_name,
            percent: 100,
            time_str: "",
            status: "done",
            output_path: data.output_path,
            speed: existing?.speed ?? "",
            fps: existing?.fps ?? "",
          };
          taskProgressMap.value = { ...taskProgressMap.value };
        },
      ),
      onEvent<{ file_index: number; file_name: string; error: string }>(
        "task_error",
        (data) => {
          console.log("[useBatchProcess] task_error received:", data);
          const existing = taskProgressMap.value[data.file_index];
          taskProgressMap.value[data.file_index] = {
            file_index: data.file_index,
            file_name: data.file_name,
            percent: 0,
            time_str: "",
            status: "error",
            error: data.error,
            speed: existing?.speed ?? "",
            fps: existing?.fps ?? "",
          };
          taskProgressMap.value = { ...taskProgressMap.value };
        },
      ),
      onEvent<{ line: string }>(
        "log_line",
        (data) => {
          logLines.value.push(data.line);
          if (logLines.value.length > 200) {
            logLines.value = logLines.value.slice(-200);
          }
        },
      ),
      onEvent<{ total: number; completed: number; errors: number }>(
        "batch_complete",
        (data) => {
          console.log("[useBatchProcess] batch_complete received:", data);
          processing.value = false;
        },
      ),
    );
  });

  onUnmounted(() => {
    cleanups.forEach((fn) => fn());
    cleanups.length = 0;
  });

  function reset() {
    console.log("[useBatchProcess] reset called");
    processing.value = false;
    overallProgress.value = 0;
    overallTotal.value = 0;
    overallCompleted.value = 0;
    taskProgressMap.value = {};
    logLines.value = [];
  }

  return {
    processing,
    overallProgress,
    overallTotal,
    overallCompleted,
    taskProgressMap,
    logLines,
    reset,
    setProcessing,
  };
}
