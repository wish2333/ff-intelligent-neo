"""Thread pool coordinator for batch FFmpeg processing."""

from __future__ import annotations

import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime
from pathlib import Path

from core.logging import get_logger
from core.models import FileItem, Preset, TaskProgress
from core.ffmpeg_runner import run_single
from core.ffmpeg_setup import get_ffmpeg_path, get_ffprobe_path
from core.preset_manager import PresetManager

logger = get_logger()


def _build_output_path(
    input_path: str,
    preset: Preset,
    output_dir: str | None,
    batch_timestamp: str,
) -> str:
    """Build the output path for a single file.

    Args:
        input_path: Source file path.
        preset: Preset with output extension.
        output_dir: If set, all files go here. If None, output to source directory.
        batch_timestamp: Shared timestamp string (yyyy-mm-dd-HH-MM) for this batch.

    Returns:
        Full output path string.
    """
    src = Path(input_path)
    stem = src.stem
    ext = preset.output_extension
    filename = f"{stem}_{batch_timestamp}{ext}"

    if output_dir:
        return str(Path(output_dir) / filename)
    else:
        return str(src.parent / filename)


class BatchRunner:
    """Manages multi-threaded batch FFmpeg conversions."""

    def __init__(self, emit) -> None:
        self._emit = emit
        self._cancel_event = threading.Event()
        self._running = False
        self._total = 0
        self._completed = 0
        self._errors = 0
        self._progress_map: dict[int, TaskProgress] = {}

    @property
    def is_running(self) -> bool:
        return self._running

    def start(
        self,
        files: list[FileItem],
        preset: Preset,
        output_dir: str | None,
        max_workers: int = 2,
    ) -> None:
        logger.info("=== 🚀 BatchRunner.start() invoked with {} files ===", len(files))
        if self._running:
            logger.warning("Batch already running, ignoring start request")
            return

        self._cancel_event.clear()
        self._running = True
        self._total = len(files)
        self._completed = 0
        self._errors = 0
        self._progress_map.clear()

        batch_timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        logger.info(
            "Batch started: {} files, preset='{}', output_dir={}, workers={}",
            len(files),
            preset.id,
            output_dir or "(source dir)",
            max_workers,
        )

        # Emit initial batch_progress so frontend knows total count
        logger.info("[BatchRunner] Emitting initial batch_progress: total={} completed=0", self._total)
        self._emit("batch_progress", {
            "total": self._total,
            "completed": 0,
            "overall_percent": 0,
        })

        ffmpeg_path = get_ffmpeg_path()
        ffprobe_path = get_ffprobe_path()

        if not ffmpeg_path:
            self._running = False
            logger.error(
                "FFmpeg binary not found. PATH={} | sys.prefix={}",
                os.environ.get("PATH", "(empty)")[:200],
                sys.prefix,
            )
            error_msg = "FFmpeg binary not found"
            logger.info("[BatchRunner] Emitting task_error: {}", error_msg)
            self._emit("task_error", {
                "file_index": -1,
                "file_name": "",
                "error": error_msg,
            })
            logger.info("[BatchRunner] Emitting batch_complete (due to FFmpeg not found)")
            self._emit("batch_complete", {
                "total": 0,
                "completed": 0,
                "errors": 1,
            })
            return

        pm = PresetManager()

        def _run_task(index: int, file_item: FileItem) -> None:
            if self._cancel_event.is_set():
                logger.debug("[_run_task] Cancel event set, skipping task {}", index)
                return

            logger.info("[_run_task] Starting task {}: {}", index, file_item.name)
            self._emit("task_start", {
                "file_index": index,
                "file_name": file_item.name,
            })
            logger.info(
                "[{}/{}] Processing: {}",
                index + 1,
                self._total,
                file_item.name,
            )

            output_path = _build_output_path(
                file_item.path, preset, output_dir, batch_timestamp
            )
            logger.debug("Output path: {}", output_path)

            args = pm.resolve_command(preset, file_item.path, output_path)

            def on_progress(percent: float, time_str: str, speed: str = "", fps: str = "") -> None:
                logger.debug("[on_progress] Task {}: {:.1f}% time={} speed={} fps={}", index, percent, time_str, speed, fps)
                self._progress_map[index] = TaskProgress(
                    file_index=index,
                    file_name=file_item.name,
                    percent=percent,
                    time_str=time_str,
                    status="running",
                    speed=speed,
                    fps=fps,
                )
                self._emit("task_progress", {
                    "file_index": index,
                    "file_name": file_item.name,
                    "percent": percent,
                    "time_str": time_str,
                    "speed": speed,
                    "fps": fps,
                })

            def on_log(line: str) -> None:
                logger.debug("[on_log] Task {}: {}", index, line.rstrip())
                self._emit("log_line", {"line": line})

            success, error = run_single(
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
                args=args,
                cancel_event=self._cancel_event,
                on_progress=on_progress,
                on_log=on_log,
            )

            if success:
                logger.info("[_run_task] Task {} succeeded, emitting task_complete", index)
                self._progress_map[index] = TaskProgress(
                    file_index=index,
                    file_name=file_item.name,
                    percent=100,
                    status="done",
                    output_path=output_path,
                )
                self._emit("task_complete", {
                    "file_index": index,
                    "file_name": file_item.name,
                    "output_path": output_path,
                })
                logger.info("[{}/{}] Done: {}", index + 1, self._total, file_item.name)
            else:
                logger.error("[_run_task] Task {} failed, emitting task_error: {}", index, error)
                self._progress_map[index] = TaskProgress(
                    file_index=index,
                    file_name=file_item.name,
                    status="error",
                    error=error,
                )
                self._emit("task_error", {
                    "file_index": index,
                    "file_name": file_item.name,
                    "error": error,
                })
                logger.error("[{}/{}] Failed: {} - {}", index + 1, self._total, file_item.name, error)

            with threading.Lock():
                self._completed += 1
                if not success:
                    self._errors += 1

                overall = self._completed / self._total * 100 if self._total > 0 else 100
                logger.debug("[batch_progress] total={} completed={} overall={:.1f}%", self._total, self._completed, overall)
                self._emit("batch_progress", {
                    "total": self._total,
                    "completed": self._completed,
                    "overall_percent": overall,
                })

        def _run_all():
            try:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures: list[Future] = []
                    for i, f in enumerate(files):
                        if self._cancel_event.is_set():
                            break
                        future = executor.submit(_run_task, i, f)
                        futures.append(future)

                    for f in futures:
                        try:
                            f.result()
                        except Exception as exc:
                            logger.exception("Unexpected error in task: {}", exc)
            finally:
                self._running = False
                logger.info(
                    "Batch complete: {}/{} done, {} errors",
                    self._completed - self._errors,
                    self._total,
                    self._errors,
                )
                logger.info("[BatchRunner] Emitting batch_complete: total={} completed={} errors={}", self._total, self._completed, self._errors)
                self._emit("batch_complete", {
                    "total": self._total,
                    "completed": self._completed,
                    "errors": self._errors,
                })

        thread = threading.Thread(target=_run_all, daemon=True)
        thread.start()

    def cancel(self) -> None:
        logger.info("Batch cancel requested")
        self._cancel_event.set()
