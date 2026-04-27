"""FF Intelligent Neo 2.0 - FFmpeg batch processing desktop tool."""

from __future__ import annotations

from pathlib import Path

import warnings
import sys
import threading

import webview
import json

# Suppress pywebview deprecation warnings (FOLDER_DIALOG / OPEN_DIALOG)
warnings.filterwarnings("ignore", message=".*deprecated.*", module="webview")

# Data directory migration must run before any core module imports
# (logging.py creates file sink at import time)
from core.paths import migrate_if_needed
migrate_if_needed()

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
    def select_files(self, file_types: list | None = None) -> dict:
        try:
            kwargs: dict = {
                "dialog_type": webview.FileDialog.OPEN,
                "allow_multiple": True,
            }
            if file_types:
                kwargs["file_types"] = tuple(file_types)
            result = self._window.create_file_dialog(**kwargs)
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
                # Phase 3.5: quality fields
                quality_mode=tc_data.get("quality_mode", ""),
                quality_value=tc_data.get("quality_value", 0),
                preset=tc_data.get("preset", ""),
                pixel_format=tc_data.get("pixel_format", ""),
                max_bitrate=tc_data.get("max_bitrate", ""),
                bufsize=tc_data.get("bufsize", ""),
            )
            fc = FilterConfig(
                rotate=fc_data.get("rotate", ""),
                crop=fc_data.get("crop", ""),
                watermark_path=fc_data.get("watermark_path", ""),
                watermark_position=fc_data.get("watermark_position", "bottom-right"),
                watermark_margin=fc_data.get("watermark_margin", 10),
                volume=fc_data.get("volume", ""),
                speed=fc_data.get("speed", ""),
                # Phase 3: audio normalization + aspect convert
                audio_normalize=fc_data.get("audio_normalize", False),
                target_loudness=fc_data.get("target_loudness", -16),
                true_peak=fc_data.get("true_peak", -1),
                lra=fc_data.get("lra", 11),
                aspect_convert=fc_data.get("aspect_convert", ""),
                target_resolution=fc_data.get("target_resolution", ""),
                bg_image_path=fc_data.get("bg_image_path", ""),
            )
            task_config = TaskConfig(transcode=tc, filters=fc, output_dir=output_dir)

            # Phase 3: attach sub-configs if present
            clip_data = (config or {}).get("clip")
            if clip_data and (clip_data.get("start_time") or clip_data.get("end_time_or_duration")):
                from core.models import ClipConfig
                task_config = TaskConfig(
                    transcode=tc, filters=fc,
                    clip=ClipConfig.from_dict(clip_data),
                    output_dir=output_dir,
                )

            merge_data = (config or {}).get("merge")
            if merge_data and len(merge_data.get("file_list", [])) >= 2:
                from core.models import MergeConfig
                task_config = TaskConfig(
                    transcode=tc, filters=fc,
                    merge=MergeConfig.from_dict(merge_data),
                    output_dir=output_dir,
                )

            avsmix_data = (config or {}).get("avsmix")
            if avsmix_data and (avsmix_data.get("external_audio_path") or avsmix_data.get("subtitle_path")):
                from core.models import AudioSubtitleConfig
                task_config = TaskConfig(
                    transcode=tc, filters=fc,
                    avsmix=AudioSubtitleConfig.from_dict(avsmix_data),
                    output_dir=output_dir,
                )

            custom_data = (config or {}).get("custom_command")
            if custom_data and custom_data.get("raw_args"):
                from core.models import CustomCommandConfig
                task_config = TaskConfig(
                    transcode=tc, filters=fc,
                    custom_command=CustomCommandConfig.from_dict(custom_data),
                    output_dir=output_dir,
                )

            # Determine tasks to add (without probing - use placeholder data)
            tasks: list[Task] = []
            if task_config.merge and len(task_config.merge.file_list) >= 2:
                # Merge mode: create ONE task for the entire merge operation
                merge_cfg = task_config.merge
                first_path = merge_cfg.file_list[0]
                task = Task(
                    file_path=first_path,
                    file_name=Path(first_path).name,
                    file_size_bytes=0,
                    duration_seconds=0.0,
                    config=task_config,
                )
                tasks = [task]
            else:
                # Normal mode: create one task per file
                for path in paths:
                    tasks.append(Task(
                        file_path=path,
                        file_name=Path(path).name,
                        file_size_bytes=0,
                        duration_seconds=0.0,
                        config=task_config,
                    ))

            # Batch add to queue (single notification)
            self._queue.add_tasks(tasks)

            # Emit individual events after atomic add
            for task in tasks:
                self._emit("task_added", {"task": task.to_dict()})

            # Background thread: probe files and emit updates
            def _probe_bg() -> None:
                for task in tasks:
                    try:
                        info = probe_file(task.file_path) or {}
                        task.file_name = info.get("file_name", task.file_name)
                        task.file_path = info.get("file_path", task.file_path)
                        task.file_size_bytes = info.get("file_size_bytes", 0)
                        task.duration_seconds = info.get("duration_seconds", 0.0)
                        self._emit("task_info_updated", {
                            "task_id": task.id,
                            "file_name": task.file_name,
                            "duration_seconds": task.duration_seconds,
                            "file_size_bytes": task.file_size_bytes,
                        })
                    except Exception as probe_err:
                        logger.warning("probe_file failed for {}: {}", task.file_path, probe_err)

            threading.Thread(target=_probe_bg, daemon=True).start()

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
    def start_task(self, task_id: str, config: dict | None = None) -> dict:
        """Start executing a single pending task with the current config."""
        try:
            task = self._queue.get_task(task_id)
            if task is not None and getattr(task, 'task_type', '') == 'auto_editor':
                return self._auto_editor.start_auto_editor_task(task_id)
            ok = self._runner.start_task(task_id, config=config)
            return {"success": ok, "data": None}
        except Exception as exc:
            logger.exception("start_task failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def stop_task(self, task_id: str) -> dict:
        """Stop a single task (pending / running / paused)."""
        try:
            task = self._queue.get_task(task_id)
            if task is not None and getattr(task, 'task_type', '') == 'auto_editor':
                return self._auto_editor.cancel_auto_editor_task(task_id)
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
    def retry_task(self, task_id: str, config: dict | None = None) -> dict:
        """Retry a failed task with the current config."""
        try:
            task = self._queue.get_task(task_id)
            if task is not None and getattr(task, 'task_type', '') == 'auto_editor':
                # Reset state then re-execute with stored params
                ok = self._runner.reset_task(task_id)
                if not ok:
                    return {"success": False, "error": "Failed to reset task"}
                return self._auto_editor.start_auto_editor_task(task_id)
            ok = self._runner.retry_task(task_id, config=config)
            return {"success": ok, "data": None}
        except Exception as exc:
            logger.exception("retry_task failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def reset_task(self, task_id: str) -> dict:
        """Reset a completed or cancelled task to pending."""
        try:
            ok = self._runner.reset_task(task_id)
            return {"success": ok, "data": None}
        except Exception as exc:
            logger.exception("reset_task failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def fail_task(self, task_id: str) -> dict:
        """Debug: force a running task to fail."""
        try:
            task = self._runner._queue.get_task(task_id)
            if task is None or task.state != "running":
                return {"success": False, "error": "Task not found or not running"}
            task.error = "Simulated failure for testing"
            self._runner._queue.transition_task(task_id, "failed")
            self._runner._emit("task_state_changed", {
                "task_id": task_id,
                "old_state": "running",
                "new_state": "failed",
            })
            self._runner._emit("queue_changed", self._runner._queue.get_summary())
            return {"success": True, "data": None}
        except Exception as exc:
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

    @expose
    def open_folder(self, path: str) -> dict:
        """Open the given folder in the system file explorer."""
        import subprocess, os
        try:
            folder = os.path.dirname(path) if os.path.isfile(path) else path
            if not os.path.isdir(folder):
                return {"success": False, "error": f"Path not found: {folder}"}
            if sys.platform == "win32":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            return {"success": True, "data": None}
        except Exception as exc:
            logger.exception("open_folder failed: {}", exc)
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
        """Validate a config dict. Returns structured {errors, warnings} with param info."""
        try:
            from core.models import TaskConfig
            from core.command_builder import validate_config, ValidationContext
            tc = TaskConfig.from_dict(config)
            ctx = ValidationContext()
            result = validate_config(tc, ctx)
            structured = {
                "errors": [{"param": i["param"], "message": i["message"]} for i in result.get("errors", []) if "param" in i],
                "warnings": [{"param": i["param"], "message": i["message"]} for i in result.get("warnings", []) if "param" in i],
            }
            return {"success": True, "data": structured}
        except Exception as exc:
            logger.exception("validate_config failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def preview_command(self, config: dict) -> dict:
        """Merged command preview and validation in a single IPC call."""
        try:
            from core.models import TaskConfig
            from core.command_builder import validate_config, ValidationContext, build_command_preview
            tc = TaskConfig.from_dict(config)
            ctx = ValidationContext(preview_mode=True)
            result = validate_config(tc, ctx)
            command = build_command_preview(tc)
            errors = [{"param": i["param"], "message": i["message"]} for i in result.get("errors", []) if "param" in i]
            warnings = [{"param": i["param"], "message": i["message"]} for i in result.get("warnings", []) if "param" in i]
            return {"success": True, "data": {"command": command, "errors": errors, "warnings": warnings}}
        except Exception as exc:
            logger.exception("preview_command failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def check_hw_encoders(self) -> dict:
        """Detect available hardware encoders from the current FFmpeg binary."""
        try:
            import subprocess
            ffmpeg_path = get_ffmpeg_path()
            if not ffmpeg_path:
                return {"success": True, "data": []}
            result = subprocess.run(
                [ffmpeg_path, "-encoders"],
                capture_output=True, text=True, timeout=30,
                creationflags=0x08000000 if sys.platform == "win32" else 0,
            )
            encoders = []
            for line in result.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] not in ("=",):
                    encoders.append(parts[1])
            return {"success": True, "data": encoders}
        except Exception as exc:
            logger.exception("check_hw_encoders failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @expose
    def get_file_duration(self, file_path: str) -> dict:
        """Get the duration of a media file in seconds using ffprobe."""
        try:
            import subprocess
            ffprobe_path = get_ffmpeg_path().replace("ffmpeg", "ffprobe")
            if not ffprobe_path or not file_path:
                return {"success": False, "error": "Invalid file path"}
            result = subprocess.run(
                [ffprobe_path, "-v", "error", "-show_entries",
                 "format=duration", "-of", "csv=p=0", file_path],
                capture_output=True, text=True, timeout=30,
                creationflags=0x08000000 if sys.platform == "win32" else 0,
            )
            duration = float(result.stdout.strip())
            return {"success": True, "data": duration}
        except Exception as exc:
            logger.exception("get_file_duration failed: {}", exc)
            return {"success": False, "error": str(exc)}
    @expose
    def get_file_formats(self) -> dict:
        """Return supported file formats from presets/file_formats.json."""
        try:
            from core.preset_manager import _get_default_presets_dir
            presets_dir = _get_default_presets_dir()
            fmt_path = presets_dir / "file_formats.json"
            if fmt_path.exists():
                with open(fmt_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {"success": True, "data": data}
            return {"success": False, "error": "file_formats.json not found"}
        except Exception as exc:
            logger.exception("get_file_formats failed: {}", exc)
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
            from core.config import load_settings, save_settings as _save
            from core.models import AppSettings
            current = load_settings()
            merged = {
                **current.to_dict(),
                **settings,
            }
            s = AppSettings.from_dict(merged)
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
            self._emit("ffmpeg_version_changed", {
                "version": info.get("version", ""),
                "path": info.get("path", ""),
                "status": "ready",
            })
            return {"success": True, "data": info}
        except (ValueError, OSError) as exc:
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

    @expose
    def select_file_filtered(self, file_types: list | None = None) -> dict:
        """Open single-file dialog with optional file type filtering."""
        try:
            kwargs: dict = {"dialog_type": webview.FileDialog.OPEN}
            if file_types:
                kwargs["file_types"] = tuple(file_types)
            result = self._window.create_file_dialog(**kwargs)
            if result and len(result) > 0:
                return {"success": True, "data": result[0]}
            return {"success": True, "data": None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @expose
    def download_ffmpeg(self) -> dict:
        """Download FFmpeg using static_ffmpeg package (Windows only).

        On non-Windows platforms, returns install instructions instead.
        """
        self._ensure_loguru()

        # Non-Windows: return platform-specific install instructions
        if sys.platform != "win32":
            return {
                "success": False,
                "error": "download_not_supported",
                "data": {
                    "platform": sys.platform,
                    "instructions": self._get_ffmpeg_install_instructions(),
                },
            }

        try:
            from core.ffmpeg_setup import is_frozen

            if is_frozen():
                return {"success": False, "error": "Download not available in packaged app"}

            import static_ffmpeg
            static_ffmpeg.add_paths()

            import shutil as _shutil
            ffmpeg_path = _shutil.which("ffmpeg")
            if ffmpeg_path:
                return {"success": True, "data": {"ffmpeg_path": ffmpeg_path}}
            return {"success": False, "error": "FFmpeg not found after download attempt"}
        except Exception as exc:
            logger.exception("download_ffmpeg failed: {}", exc)
            return {"success": False, "error": str(exc)}

    @staticmethod
    def _get_ffmpeg_install_instructions() -> dict:
        """Return platform-specific FFmpeg installation instructions."""
        if sys.platform == "darwin":
            return {
                "method": "homebrew",
                "command": "brew install ffmpeg",
                "url": "https://brew.sh",
            }
        if sys.platform.startswith("linux"):
            try:
                import platform as _platform
                os_release = _platform.freedesktop_os_release()
                distro_id = os_release.get("ID", "")
            except (AttributeError, OSError):
                distro_id = ""
            if distro_id in ("ubuntu", "debian", "linuxmint", "pop"):
                return {"method": "apt", "command": "sudo apt install ffmpeg"}
            if distro_id in ("fedora", "rhel", "centos"):
                return {"method": "dnf", "command": "sudo dnf install ffmpeg"}
            if distro_id in ("arch", "manjaro", "endeavouros"):
                return {"method": "pacman", "command": "sudo pacman -S ffmpeg"}
            return {"method": "package_manager", "command": "sudo <package_manager> install ffmpeg"}
        return {"method": "unknown", "command": ""}

    # ------------------------------------------------------------------
    # Auto-Editor delegates (v2.2.0)
    # ------------------------------------------------------------------

    @property
    def _auto_editor(self):
        if not hasattr(self, "_auto_editor_inst"):
            from core.auto_editor_api import AutoEditorApi
            self._auto_editor_inst = AutoEditorApi(
                emit=self._emit,
                queue=self._queue,
                runner=self._runner,
            )
        return self._auto_editor_inst

    @expose
    def set_auto_editor_path(self, path: str) -> dict:
        return self._auto_editor.set_auto_editor_path(path)

    @expose
    def get_auto_editor_status(self) -> dict:
        return self._auto_editor.get_auto_editor_status()

    @expose
    def get_auto_editor_encoders(self, output_format: str = "mp4") -> dict:
        return self._auto_editor.get_auto_editor_encoders(output_format)

    @expose
    def download_auto_editor(self) -> dict:
        return self._auto_editor.download_auto_editor()

    @expose
    def add_auto_editor_task(self, input_file: str, params: dict) -> dict:
        return self._auto_editor.add_auto_editor_task(input_file, params)

    @expose
    def preview_auto_editor_command(self, params: dict) -> dict:
        return self._auto_editor.preview_auto_editor_command(params)

    @expose
    def cancel_auto_editor_task(self, task_id: str) -> dict:
        return self._auto_editor.cancel_auto_editor_task(task_id)

    @expose
    def start_auto_editor_task(self, task_id: str) -> dict:
        return self._auto_editor.start_auto_editor_task(task_id)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup(self) -> None:
        """Force-kill all FFmpeg processes and exit immediately."""
        if getattr(self, "_cleanup_done", False):
            return
        self._cleanup_done = True
        try:
            if hasattr(self, "_runner_inst"):
                self._ensure_loguru()
                runner = self._runner_inst
                logger.info("Force-killing all tasks for shutdown...")
                runner.force_kill_all()
        except Exception as exc:
            logger.error("Cleanup error: {}", exc)


if __name__ == "__main__":
    import atexit

    api = FFmpegApi()
    atexit.register(api._cleanup)
    app = App(
        api,
        title="FF Intelligent Neo",
        width=1260,
        height=1000,
        min_size=(1100, 600),
        frontend_dir="frontend_dist",
        on_closing=api._cleanup,
    )
    app.run()
