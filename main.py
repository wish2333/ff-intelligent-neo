# /// script
# requires-python = ">=3.10"
# dependencies = ["pywebview>=6.0", "static-ffmpeg", "loguru>=0.7"]
# ///
"""FF Intelligent MVP - FFmpeg batch processing desktop tool."""

from __future__ import annotations

import dataclasses
import threading
import warnings

import webview

# Suppress pywebview deprecation warnings (FOLDER_DIALOG / OPEN_DIALOG)
warnings.filterwarnings("ignore", message=".*deprecated.*", module="webview")

from pywebvue import App, Bridge, expose
from core.logging import get_logger, setup_frontend_sink
from core.ffmpeg_setup import ensure_ffmpeg, get_ffmpeg_path
from core.file_info import probe_file
from core.models import FileItem, Preset

logger = get_logger()


def _as_dicts(items) -> list[dict]:
    return [dataclasses.asdict(item) for item in items]


_MEDIA_FILE_TYPES = (
    ("Video Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm"),
    ("Audio Files", "*.mp3 *.wav *.aac *.flac *.ogg *.m4a"),
    ("All Files", "*.*"),
)


class FFmpegApi(Bridge):

    def __init__(self) -> None:
        super().__init__()
        self._files: list[FileItem] = []
        self._files_lock = threading.Lock()
        self._preset_manager = None
        self._batch_runner = None
        self._loguru_initialized = False

    def _ensure_loguru(self) -> None:
        """Setup loguru frontend sink once the bridge emit is available."""
        if self._loguru_initialized:
            return
        self._loguru_initialized = True
        setup_frontend_sink(self._emit)
        logger.info("FF Intelligent started, loguru frontend sink connected")

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
    # File management
    # ------------------------------------------------------------------

    @expose
    def add_files(self, paths: list[str]) -> dict:
        self._ensure_loguru()
        logger.info("Adding {} files", len(paths))
        new_items = [probe_file(p) for p in paths]
        with self._files_lock:
            self._files.extend(new_items)
            serialized = _as_dicts(self._files)
        return {"success": True, "data": {"files": serialized, "added": len(new_items)}}

    @expose
    def remove_files(self, indices: list[int]) -> dict:
        with self._files_lock:
            for idx in sorted(set(indices), reverse=True):
                if 0 <= idx < len(self._files):
                    self._files.pop(idx)
            serialized = _as_dicts(self._files)
        return {"success": True, "data": serialized}

    @expose
    def clear_files(self) -> dict:
        with self._files_lock:
            self._files.clear()
        return {"success": True, "data": []}

    @expose
    def get_files(self) -> dict:
        with self._files_lock:
            serialized = _as_dicts(self._files)
        return {"success": True, "data": serialized}

    # ------------------------------------------------------------------
    # Preset management
    # ------------------------------------------------------------------

    def _get_preset_manager(self):
        if self._preset_manager is None:
            from core.preset_manager import PresetManager
            self._preset_manager = PresetManager()
        return self._preset_manager

    @expose
    def get_presets(self) -> dict:
        self._ensure_loguru()
        pm = self._get_preset_manager()
        presets = pm.list_presets()
        return {"success": True, "data": _as_dicts(presets)}

    @expose
    def get_preset(self, preset_id: str) -> dict:
        pm = self._get_preset_manager()
        preset = pm.get_preset(preset_id)
        if preset is None:
            return {"success": False, "error": f"Preset '{preset_id}' not found"}
        return {"success": True, "data": _as_dicts(preset)[0]}

    @expose
    def save_preset(self, preset_data: dict) -> dict:
        pm = self._get_preset_manager()
        preset = Preset(
            id=preset_data["id"],
            name=preset_data["name"],
            description=preset_data.get("description", ""),
            output_extension=preset_data.get("output_extension", ".mp4"),
            command_template=preset_data.get("command_template", ""),
            is_default=preset_data.get("is_default", False),
        )
        saved = pm.save_preset(preset)
        return {"success": True, "data": _as_dicts(saved)[0]}

    @expose
    def delete_preset(self, preset_id: str) -> dict:
        pm = self._get_preset_manager()
        try:
            pm.delete_preset(preset_id)
            return {"success": True, "data": None}
        except ValueError as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------------------

    def _get_batch_runner(self):
        if self._batch_runner is None:
            from core.batch_runner import BatchRunner
            self._batch_runner = BatchRunner(emit=self._emit)
        return self._batch_runner

    @expose
    def start_batch(
        self,
        preset_id: str,
        output_dir: str = "",
        max_workers: int = 2,
    ) -> dict:
        self._ensure_loguru()

        pm = self._get_preset_manager()
        preset = pm.get_preset(preset_id)
        if preset is None:
            logger.error("Preset '{}' not found", preset_id)
            return {"success": False, "error": f"Preset '{preset_id}' not found"}

        with self._files_lock:
            if not self._files:
                logger.error("No files to process")
                return {"success": False, "error": "No files to process"}
            files_snapshot = list(self._files)

        effective_output_dir = output_dir if output_dir else None
        runner = self._get_batch_runner()
        runner.start(files_snapshot, preset, effective_output_dir, max_workers)
        return {"success": True, "data": None}

    @expose
    def cancel_batch(self) -> dict:
        runner = self._get_batch_runner()
        runner.cancel()
        return {"success": True, "data": None}

    # ------------------------------------------------------------------
    # File dialogs (must use self._window, not webview.windows[])
    # ------------------------------------------------------------------

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


if __name__ == "__main__":
    print("[DEBUG] Creating FFmpegApi instance...")
    api = FFmpegApi()
    print(f"[DEBUG] API instance methods: {[m for m in dir(api) if not m.startswith('_')]}")
    print(f"[DEBUG] API has get_app_info: {hasattr(api, 'get_app_info')}")
    print(f"[DEBUG] API has setup_ffmpeg: {hasattr(api, 'setup_ffmpeg')}")
    print(f"[DEBUG] API has add_files: {hasattr(api, 'add_files')}")
    print(f"[DEBUG] API has start_batch: {hasattr(api, 'start_batch')}")
    print("[DEBUG] Starting app...")
    app = App(
        api,
        title="FF Intelligent",
        width=960,
        height=720,
        min_size=(800, 600),
        frontend_dir="frontend_dist",
    )
    app.run()
