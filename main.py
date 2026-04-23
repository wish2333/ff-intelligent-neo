# /// script
# requires-python = ">=3.10"
# dependencies = ["pywebview>=6.0", "static-ffmpeg", "loguru>=0.7"]
# ///
"""FF Intelligent Neo 2.0 - FFmpeg batch processing desktop tool."""

from __future__ import annotations

import warnings

import webview

# Suppress pywebview deprecation warnings (FOLDER_DIALOG / OPEN_DIALOG)
warnings.filterwarnings("ignore", message=".*deprecated.*", module="webview")

from pywebvue import App, Bridge, expose
from core.logging import get_logger, setup_frontend_sink
from core.ffmpeg_setup import ensure_ffmpeg, get_ffmpeg_path
from core.config import load_settings

logger = get_logger()


class FFmpegApi(Bridge):

    def __init__(self) -> None:
        super().__init__()
        self._loguru_initialized = False

    # ------------------------------------------------------------------
    # Lazy initialisation helpers
    # ------------------------------------------------------------------

    def _ensure_loguru(self) -> None:
        """Setup loguru frontend sink once the bridge emit is available."""
        if self._loguru_initialized:
            return
        self._loguru_initialized = True
        setup_frontend_sink(self._emit)
        logger.info("FF Intelligent Neo 2.0 started, loguru frontend sink connected")

    @property
    def _queue(self):
        from core.task_queue import TaskQueue
        if not hasattr(self, "_queue_inst"):
            self._queue_inst = TaskQueue()
            self._queue_inst.load_state()
            self._queue_inst.set_on_change(self._on_queue_change)
        return self._queue_inst

    @property
    def _runner(self):
        from core.task_runner import TaskRunner
        if not hasattr(self, "_runner_inst"):
            settings = load_settings()
            self._runner_inst = TaskRunner(self._queue, self._emit)
            self._runner_inst.start(max_workers=settings.max_workers)
        return self._runner_inst

    def _on_queue_change(self, summary: dict) -> None:
        self._emit("queue_changed", summary)

    # ------------------------------------------------------------------
    # FFmpeg setup
    # ------------------------------------------------------------------

    @expose
    def setup_ffmpeg(self) -> dict:
        self._ensure_loguru()
        try:
            ready = ensure_ffmpeg()
            ffmpeg_path = get_ffmpeg_path()
            logger.info("FFmpeg setup: ready={}, path={}", ready, ffmpeg_path)
            return {"success": True, "data": {"ready": ready, "ffmpeg_path": ffmpeg_path or ""}}
        except Exception as exc:
            logger.exception("FFmpeg setup failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def get_app_info(self) -> dict:
        """Return application metadata and FFmpeg/FFprobe versions."""
        try:
            from core.app_info import get_app_info as _get_info
            info = _get_info()
            return {"success": True, "data": info}
        except Exception as exc:
            logger.exception("get_app_info failed: {}", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # File dialogs
    # ------------------------------------------------------------------

    @expose
    def select_files(self) -> dict:
        try:
            result = self._window.create_file_dialog(
                dialog_type=webview.FileDialog.OPEN,
                allow_multiple=True,
            )
            if result:
                return {"success": True, "data": list(result)}
            return {"success": True, "data": []}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @expose
    def select_output_dir(self) -> dict:
        try:
            result = self._window.create_file_dialog(
                dialog_type=webview.FileDialog.FOLDER,
            )
            if result and len(result) > 0:
                return {"success": True, "data": result[0]}
            return {"success": True, "data": None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Task queue operations
    # ------------------------------------------------------------------

    @expose
    def add_tasks(self, paths: list, config: dict | None = None) -> dict:
        """Probe files and add them to the task queue."""
        self._ensure_loguru()
        try:
            from core.file_info import probe_file
            from core.models import Task, TaskConfig, TranscodeConfig, FilterConfig

            tc_data = (config or {}).get("transcode", {})
            fc_data = (config or {}).get("filters", {})
            output_dir = (config or {}).get("output_dir", "")

            tc = TranscodeConfig(
                video_codec=tc_data.get("video_codec", "libx264"),
                audio_codec=tc_data.get("audio_codec", "aac"),
                video_bitrate=tc_data.get("video_bitrate", ""),
                audio_bitrate=tc_data.get("audio_bitrate", ""),
                resolution=tc_data.get("resolution", ""),
                framerate=tc_data.get("framerate", ""),
                output_extension=tc_data.get("output_extension", ".mp4"),
            )
            fc = FilterConfig(
                rotate=fc_data.get("rotate", ""),
                crop=fc_data.get("crop", ""),
                watermark_path=fc_data.get("watermark_path", ""),
                watermark_position=fc_data.get("watermark_position", "bottom-right"),
                watermark_margin=fc_data.get("watermark_margin", 10),
                volume=fc_data.get("volume", ""),
                speed=fc_data.get("speed", ""),
            )
            task_config = TaskConfig(transcode=tc, filters=fc, output_dir=output_dir)

            # Probe all files first, then add atomically
            tasks: list[Task] = []
            for path in paths:
                info = probe_file(path)
                task = Task(
                    file_path=info.get("file_path", path),
                    file_name=info.get("file_name", ""),
                    file_size_bytes=info.get("file_size_bytes", 0),
                    duration_seconds=info.get("duration_seconds", 0.0),
                    config=task_config,
                )
                tasks.append(task)

            # Batch add to queue (single notification)
            self._queue.add_tasks(tasks)

            # Emit individual events after atomic add
            for task in tasks:
                self._emit("task_added", {"task": task.to_dict()})

            return {"success": True, "data": [t.to_dict() for t in tasks]}
        except Exception as exc:
            logger.exception("add_tasks failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def remove_tasks(self, task_ids: list) -> dict:
        """Remove tasks from the queue."""
        try:
            # Determine which IDs actually exist before removing
            existing_ids = {t.id for t in self._queue.get_all_tasks_objects()}
            to_emit = [tid for tid in task_ids if tid in existing_ids]

            removed = self._queue.remove_tasks(task_ids)
            for tid in to_emit:
                self._emit("task_removed", {"task_id": tid})
            return {"success": True, "data": {"removed": removed}}
        except Exception as exc:
            logger.exception("remove_tasks failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def reorder_tasks(self, task_ids: list) -> dict:
        """Reorder tasks in the queue."""
        try:
            self._queue.reorder_tasks(task_ids)
            return {"success": True, "data": None}
        except Exception as exc:
            logger.exception("reorder_tasks failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def get_tasks(self) -> dict:
        """Return all tasks in queue order."""
        try:
            tasks = self._queue.get_all_tasks()
            return {"success": True, "data": tasks}
        except Exception as exc:
            logger.exception("get_tasks failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def get_queue_summary(self) -> dict:
        """Return counts by state."""
        try:
            summary = self._queue.get_summary()
            return {"success": True, "data": summary}
        except Exception as exc:
            logger.exception("get_queue_summary failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def clear_completed(self) -> dict:
        """Remove all completed tasks from the queue."""
        try:
            removed = self._queue.clear_completed()
            return {"success": True, "data": {"removed": removed}}
        except Exception as exc:
            logger.exception("clear_completed failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def clear_all(self) -> dict:
        """Remove all tasks from the queue."""
        try:
            removed = self._queue.clear_all()
            return {"success": True, "data": {"removed": removed}}
        except Exception as exc:
            logger.exception("clear_all failed: {}", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Task control
    # ------------------------------------------------------------------

    @expose
    def start_task(self, task_id: str) -> dict:
        """Start executing a single pending task."""
        try:
            ok = self._runner.start_task(task_id)
            return {"success": ok, "data": None}
        except Exception as exc:
            logger.exception("start_task failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def stop_task(self, task_id: str) -> dict:
        """Stop a single task (pending / running / paused)."""
        try:
            ok = self._runner.stop_task(task_id)
            return {"success": ok, "data": None}
        except Exception as exc:
            logger.exception("stop_task failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def pause_task(self, task_id: str) -> dict:
        """Pause a single running task."""
        try:
            ok = self._runner.pause_task(task_id)
            return {"success": ok, "data": None}
        except Exception as exc:
            logger.exception("pause_task failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def resume_task(self, task_id: str) -> dict:
        """Resume a single paused task."""
        try:
            ok = self._runner.resume_task(task_id)
            return {"success": ok, "data": None}
        except Exception as exc:
            logger.exception("resume_task failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def retry_task(self, task_id: str) -> dict:
        """Retry a failed task."""
        try:
            ok = self._runner.retry_task(task_id)
            return {"success": ok, "data": None}
        except Exception as exc:
            logger.exception("retry_task failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def stop_all(self) -> dict:
        """Stop all non-terminal tasks."""
        try:
            stopped = self._runner.stop_all()
            return {"success": True, "data": {"stopped": stopped}}
        except Exception as exc:
            logger.exception("stop_all failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def pause_all(self) -> dict:
        """Phase 4: pause all running tasks."""
        try:
            paused = self._runner.pause_all()
            return {"success": True, "data": {"paused": paused}}
        except Exception as exc:
            logger.exception("pause_all failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def resume_all(self) -> dict:
        """Phase 4: resume all paused tasks."""
        try:
            resumed = self._runner.resume_all()
            return {"success": True, "data": {"resumed": resumed}}
        except Exception as exc:
            logger.exception("resume_all failed: {}", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Config & Presets
    # ------------------------------------------------------------------

    @property
    def _preset_mgr(self):
        from core.preset_manager import PresetManager
        if not hasattr(self, "_preset_mgr_inst"):
            self._preset_mgr_inst = PresetManager()
        return self._preset_mgr_inst

    @expose
    def build_command(self, config: dict) -> dict:
        """Build an FFmpeg command string from a config dict (for preview)."""
        try:
            from core.models import TaskConfig
            from core.command_builder import build_command_preview
            tc = TaskConfig.from_dict(config)
            cmd = build_command_preview(tc)
            return {"success": True, "data": cmd}
        except Exception as exc:
            logger.exception("build_command failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def validate_config(self, config: dict) -> dict:
        """Validate a config dict. Returns {errors, warnings} lists."""
        try:
            from core.models import TaskConfig
            from core.command_builder import validate_config, ValidationContext
            tc = TaskConfig.from_dict(config)
            ctx = ValidationContext()
            result = validate_config(tc, ctx)
            return {"success": True, "data": result}
        except Exception as exc:
            logger.exception("validate_config failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def get_presets(self) -> dict:
        """Return all presets (defaults + user)."""
        try:
            presets = self._preset_mgr.list_presets()
            return {"success": True, "data": presets}
        except Exception as exc:
            logger.exception("get_presets failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def save_preset(self, preset: dict) -> dict:
        """Create or update a user preset."""
        try:
            saved = self._preset_mgr.save_preset(preset)
            return {"success": True, "data": saved}
        except Exception as exc:
            logger.exception("save_preset failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def delete_preset(self, preset_id: str) -> dict:
        """Delete a user preset."""
        try:
            self._preset_mgr.delete_preset(preset_id)
            return {"success": True, "data": None}
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.exception("delete_preset failed: {}", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Settings (Phase 1 stubs)
    # ------------------------------------------------------------------

    @expose
    def get_settings(self) -> dict:
        try:
            settings = load_settings()
            return {"success": True, "data": settings.to_dict()}
        except Exception as exc:
            logger.exception("get_settings failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def save_settings(self, settings: dict) -> dict:
        try:
            from core.config import save_settings as _save
            from core.models import AppSettings
            s = AppSettings.from_dict(settings)
            _save(s)
            return {"success": True, "data": None}
        except Exception as exc:
            logger.exception("save_settings failed: {}", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # FFmpeg version management
    # ------------------------------------------------------------------

    @expose
    def get_ffmpeg_versions(self) -> dict:
        """Discover and return all available FFmpeg versions."""
        try:
            from core.ffmpeg_setup import discover_ffmpeg_versions
            versions = discover_ffmpeg_versions()
            return {"success": True, "data": versions}
        except Exception as exc:
            logger.exception("get_ffmpeg_versions failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def switch_ffmpeg(self, path: str) -> dict:
        """Switch to a specific FFmpeg binary."""
        try:
            from core.ffmpeg_setup import switch_ffmpeg
            info = switch_ffmpeg(path)
            return {"success": True, "data": info}
        except (ValueError, Exception) as exc:
            logger.exception("switch_ffmpeg failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def select_ffmpeg_binary(self) -> dict:
        """Open file dialog to select an FFmpeg binary."""
        try:
            result = self._window.create_file_dialog(
                dialog_type=webview.FileDialog.OPEN,
            )
            if result and len(result) > 0:
                return {"success": True, "data": result[0]}
            return {"success": True, "data": None}
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    api = FFmpegApi()
    app = App(
        api,
        title="FF Intelligent Neo",
        width=1200,
        height=900,
        min_size=(800, 600),
        frontend_dir="frontend_dist",
    )
    app.run()
