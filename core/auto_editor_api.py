"""Auto-editor API class.

Provides the backend API for auto-editor integration: path management,
version checking, encoder querying, task management, and command preview.

Note: This is a plain class (not a Bridge subclass) because pywebvue's
App only supports a single js_api object. Exposed methods are delegated
through FFmpegApi in main.py.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

from core.auto_editor_runner import (
    build_command,
    generate_output_path,
    validate_local_input,
)
from core.config import load_settings, save_settings
from core.logging import get_logger
from core.models import AppSettings, Task, TaskConfig

logger = get_logger()

_VERSION_RE = re.compile(r"auto-editor\s+(\d+)\.(\d+)\.(\d+)")


def _run_subprocess(
    args: list[str],
    timeout: int = 10,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Run a subprocess with platform-appropriate flags."""
    kw: dict = {
        "capture_output": capture_output,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "timeout": timeout,
    }
    if sys.platform == "win32":
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.run(args, **kw)


def _parse_version(version_str: str) -> list[int] | None:
    """Parse version string into [major, minor, patch].

    Args:
        version_str: Version output from auto-editor --version.

    Returns:
        List of 3 ints, or None if parsing fails.
    """
    match = _VERSION_RE.search(version_str)
    if match:
        return [int(match.group(1)), int(match.group(2)), int(match.group(3))]
    return None


class AutoEditorApi:

    def __init__(self, emit, queue, runner) -> None:
        """Initialize with references to shared infrastructure.

        Args:
            emit: Callable(event_name, data) - typically Bridge._emit.
            queue: Shared TaskQueue instance (same as FFmpegApi uses).
            runner: Shared TaskRunner instance (same as FFmpegApi uses).
        """
        self._emit = emit
        self._queue = queue
        self._runner = runner

    # ------------------------------------------------------------------
    # Path management
    # ------------------------------------------------------------------

    def set_auto_editor_path(self, path: str) -> dict:
        """Validate an auto-editor binary and save to settings.

        Args:
            path: File system path to the auto-editor binary.

        Returns:
            {success, data: {version, path}} on success.
        """
        try:
            resolved = Path(path).resolve()
            if not resolved.exists():
                return {"success": False, "error": "File not found"}

            result = _run_subprocess(
                [str(resolved), "--version"],
                timeout=10,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to run auto-editor: {result.stderr.strip()}",
                }

            version_parts = _parse_version(result.stdout)
            if version_parts is None:
                return {
                    "success": False,
                    "error": f"Cannot parse version from output: {result.stdout.strip()}",
                }

            # Compatibility check: >= 30.1.0, < 31.0.0
            if version_parts < [30, 1, 0] or version_parts >= [31, 0, 0]:
                version_str = ".".join(str(v) for v in version_parts)
                return {
                    "success": False,
                    "error": (
                        f"Version {version_str} not supported. "
                        "Need >= 30.1.0, < 31.0.0"
                    ),
                }

            # Save to settings
            settings = load_settings()
            new_settings = AppSettings(
                max_workers=settings.max_workers,
                default_output_dir=settings.default_output_dir,
                ffmpeg_path=settings.ffmpeg_path,
                ffprobe_path=settings.ffprobe_path,
                auto_editor_path=str(resolved),
                theme=settings.theme,
                language=settings.language,
            )
            save_settings(new_settings)

            version_str = ".".join(str(v) for v in version_parts)
            self._emit("auto_editor_version_changed", {
                "version": version_str,
                "path": str(resolved),
                "status": "ready",
            })

            return {
                "success": True,
                "data": {
                    "version": version_str,
                    "path": str(resolved),
                },
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout verifying auto-editor binary"}
        except Exception as exc:
            logger.exception("set_auto_editor_path failed: {}", exc)
            return {"success": False, "error": str(exc)}

    def get_auto_editor_status(self) -> dict:
        """Check auto-editor availability and version compatibility.

        Returns:
            {success, data: {available, compatible, version, path}}.
        """
        try:
            settings = load_settings()
            path = settings.auto_editor_path

            if not path:
                return {
                    "success": True,
                    "data": {
                        "available": False,
                        "compatible": False,
                        "version": "",
                        "path": "",
                    },
                }

            resolved = Path(path).resolve()
            if not resolved.exists():
                return {
                    "success": True,
                    "data": {
                        "available": False,
                        "compatible": False,
                        "version": "",
                        "path": path,
                    },
                }

            result = _run_subprocess(
                [str(resolved), "--version"],
                timeout=10,
            )

            if result.returncode != 0:
                return {
                    "success": True,
                    "data": {
                        "available": False,
                        "compatible": False,
                        "version": "",
                        "path": path,
                    },
                }

            version_parts = _parse_version(result.stdout)
            if version_parts is None:
                return {
                    "success": True,
                    "data": {
                        "available": True,
                        "compatible": False,
                        "version": "",
                        "path": path,
                    },
                }

            version_str = ".".join(str(v) for v in version_parts)
            compatible = version_parts >= [30, 1, 0] and version_parts < [31, 0, 0]

            return {
                "success": True,
                "data": {
                    "available": True,
                    "compatible": compatible,
                    "version": version_str,
                    "path": path,
                },
            }
        except Exception as exc:
            logger.exception("get_auto_editor_status failed: {}", exc)
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Encoder query
    # ------------------------------------------------------------------

    def get_auto_editor_encoders(self, output_format: str = "mp4") -> dict:
        """Query auto-editor for supported encoders of a given format.

        Args:
            output_format: Container format (e.g. "mp4", "mkv", "mov").

        Returns:
            {success, data: {video: [...], audio: [...], subtitle: [...], other: [...]}}.
        """
        try:
            fmt = output_format.lower().lstrip(".")
            allowed_formats = {"mp4", "mkv", "mov"}
            if fmt not in allowed_formats:
                return {
                    "success": False,
                    "error": f"Unsupported format '{output_format}'. Allowed: {', '.join(sorted(allowed_formats))}",
                }

            settings = load_settings()
            path = settings.auto_editor_path
            if not path:
                return {"success": False, "error": "Auto-editor path not configured"}

            result = _run_subprocess(
                [path, "info", "-encoders", fmt],
                timeout=15,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to query encoders: {result.stderr.strip()}",
                }

            encoders = self._parse_encoder_output(result.stdout)
            return {"success": True, "data": encoders}
        except Exception as exc:
            logger.exception("get_auto_editor_encoders failed: {}", exc)
            return {"success": False, "error": str(exc)}

    def _parse_encoder_output(self, stdout: str) -> dict:
        """Parse auto-editor info -encoders output.

        Expected format:
            v: libx264
            v: libx265
            a: aac
            s: ass
        """
        result: dict[str, list[str]] = {
            "video": [],
            "audio": [],
            "subtitle": [],
            "other": [],
        }

        prefix_map = {
            "v:": "video",
            "a:": "audio",
            "s:": "subtitle",
        }

        for line in stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            matched = False
            for prefix, category in prefix_map.items():
                if line.startswith(prefix):
                    encoder_name = line[len(prefix):].strip()
                    if encoder_name:
                        result[category].append(encoder_name)
                    matched = True
                    break

            if not matched and ":" in line:
                encoder_name = line.split(":", 1)[1].strip()
                if encoder_name:
                    result["other"].append(encoder_name)

        return result

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_auto_editor_task(self, input_file: str, params: dict) -> dict:
        """Validate input and parameters, then enqueue an auto-editor task.

        Args:
            input_file: Path to the input media file.
            params: auto-editor parameters dict.

        Returns:
            {success, data: {task_id}}.
        """
        try:
            # Validate input
            validated_path = validate_local_input(input_file)

            # Cross-parameter validation
            edit_method = params.get("edit", "audio")
            if edit_method == "motion" and params.get("an", False):
                logger.warning(
                    "Motion edit with audio disabled (-an) may produce unexpected results"
                )

            # Determine output settings
            settings = load_settings()
            output_dir = params.get("output_dir", "") or settings.default_output_dir
            if not output_dir:
                output_dir = str(validated_path.parent)

            output_ext = params.get("output_extension", ".mp4")

            # Build command (NOT at enqueue time, but we need output_path now)
            task_id = uuid.uuid4().hex[:12]
            output_path = generate_output_path(
                str(validated_path), output_dir, task_id, output_ext
            )

            auto_editor_path = settings.auto_editor_path
            if not auto_editor_path:
                return {"success": False, "error": "Auto-editor path not configured"}

            # Create Task entity
            task = Task(
                id=task_id,
                file_path=str(validated_path),
                file_name=validated_path.name,
                file_size_bytes=validated_path.stat().st_size,
                task_type="auto_editor",
            )
            task.output_path = str(output_path)
            task.config = TaskConfig(output_dir=output_dir)

            # Enqueue task
            self._queue.add_task(task)

            self._emit("queue_changed", self._queue.get_summary())

            # Store auto-editor params for execution time
            if not hasattr(self, "_pending_auto_editor_tasks"):
                self._pending_auto_editor_tasks = {}
            self._pending_auto_editor_tasks[task_id] = {
                "input_file": str(validated_path),
                "params": params,
                "auto_editor_path": auto_editor_path,
                "output_path": str(output_path),
                "output_dir": output_dir,
            }

            return {
                "success": True,
                "data": {"task_id": task_id},
            }
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.exception("add_auto_editor_task failed: {}", exc)
            return {"success": False, "error": str(exc)}

    def preview_auto_editor_command(self, params: dict) -> dict:
        """Build and return a preview of the auto-editor command.

        Args:
            params: auto-editor parameters dict (must include 'input_file').

        Returns:
            {success, data: {argv: [...], display: str}}.
        """
        try:
            input_file = params.get("input_file")
            if not input_file:
                return {"success": False, "error": "input_file is required"}

            validate_local_input(input_file)

            settings = load_settings()
            auto_editor_path = settings.auto_editor_path
            if not auto_editor_path:
                return {"success": False, "error": "Auto-editor path not configured"}

            # Set preview mode
            preview_params = {**params, "_preview_mode": True}

            argv = build_command(
                input_file=input_file,
                params=preview_params,
                auto_editor_path=auto_editor_path,
            )

            display = " ".join(argv)

            return {
                "success": True,
                "data": {
                    "argv": argv,
                    "display": display,
                },
            }
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.exception("preview_auto_editor_command failed: {}", exc)
            return {"success": False, "error": str(exc)}

    def cancel_auto_editor_task(self, task_id: str) -> dict:
        """Cancel a running auto-editor task and cleanup partial output.

        Args:
            task_id: Task identifier to cancel.

        Returns:
            {success: bool, error?: str}.
        """
        try:
            task = self._queue.get_task(task_id)
            if task is None:
                return {"success": False, "error": "Task not found"}

            if task.state not in ("pending", "running"):
                return {"success": False, "error": f"Cannot cancel task in state: {task.state}"}

            # Kill process via task runner
            self._runner.stop_task(task_id)

            # Cleanup pending params
            if hasattr(self, "_pending_auto_editor_tasks"):
                self._pending_auto_editor_tasks.pop(task_id, None)

            return {"success": True, "data": None}
        except Exception as exc:
            logger.exception("cancel_auto_editor_task failed: {}", exc)
            return {"success": False, "error": str(exc)}

    def start_auto_editor_task(self, task_id: str) -> dict:
        """Start a pending auto-editor task.

        Builds the command at execution time and submits to the runner.

        Args:
            task_id: Task identifier to start.

        Returns:
            {success: bool, error?: str}.
        """
        try:
            if not hasattr(self, "_pending_auto_editor_tasks"):
                self._pending_auto_editor_tasks = {}

            pending = self._pending_auto_editor_tasks.get(task_id)
            if not pending:
                return {"success": False, "error": "No pending auto-editor task data"}

            args = build_command(
                input_file=pending["input_file"],
                params=pending["params"],
                auto_editor_path=pending["auto_editor_path"],
                output_path=pending["output_path"],
            )

            runner = self._runner
            runner.start_auto_editor_task(
                task_id=task_id,
                args=args,
                input_file=pending["input_file"],
                output_path=pending["output_path"],
            )

            # Clean up stored params after submission
            self._pending_auto_editor_tasks.pop(task_id, None)

            return {"success": True, "data": None}
        except Exception as exc:
            logger.exception("start_auto_editor_task failed: {}", exc)
            return {"success": False, "error": str(exc)}
