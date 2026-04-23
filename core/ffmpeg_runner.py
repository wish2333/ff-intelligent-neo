"""Single-file FFmpeg execution with progress parsing.

Refactored for 2.0: works with the new :class:`Task` model and reports
progress as frozen :class:`TaskProgress` snapshots.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import time

from core.logging import get_logger
from core.models import Task, TaskProgress
from core.process_control import kill_process_tree

logger = get_logger()

_TIME_RE = re.compile(r"time=(\d+):(\d+):(\d+)\.(\d+)")
_SPEED_RE = re.compile(r"speed=\s*(\S+)")
_FPS_RE = re.compile(r"fps=\s*(\S+)")


def _parse_time_to_seconds(match: re.Match) -> float:
    h = int(match.group(1))
    m = int(match.group(2))
    s = int(match.group(3))
    frac = int(match.group(4).ljust(3, "0")[:3])
    return h * 3600 + m * 60 + s + frac / 1000.0


def _get_duration_seconds(ffprobe: str, file_path: str) -> float:
    """Get the duration of a media file using ffprobe."""
    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            return 0.0
        info = json.loads(result.stdout)
        return float(info.get("format", {}).get("duration", 0))
    except Exception as exc:
        logger.warning("Failed to get duration for {}: {}", file_path, exc)
        return 0.0


def run_single(
    task: Task,
    ffmpeg_path: str,
    ffprobe_path: str,
    args: list[str],
    cancel_event: threading.Event,
    on_progress: "Callable[[TaskProgress], None] | None" = None,
    on_log: "Callable[[str], None] | None" = None,
    on_proc_start: "Callable[[subprocess.Popen], None] | None" = None,
) -> tuple[bool, str]:
    """Execute a single FFmpeg command for *task*.

    Args:
        task: The Task entity (mutable -- progress/log updated in-place).
        ffmpeg_path: Path to ffmpeg binary.
        ffprobe_path: Path to ffprobe binary.
        args: FFmpeg arguments (without the binary name).
        cancel_event: Threading event to signal cancellation.
        on_progress: Callback receiving a frozen TaskProgress snapshot.
        on_log: Callback receiving each stderr line (stripped).
        on_proc_start: Callback receiving the Popen object after launch.

    Returns:
        Tuple of (success: bool, error_message: str).
    """
    duration = 0.0
    if task.file_path and ffprobe_path:
        duration = _get_duration_seconds(ffprobe_path, task.file_path)

    cmd = [ffmpeg_path, "-hide_banner", "-y", *args]
    logger.debug("Running: {}", " ".join(cmd))

    popen_kw: dict = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }
    if sys.platform == "win32":
        popen_kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        proc = subprocess.Popen(cmd, **popen_kw)
    except OSError as e:
        logger.error("Failed to start ffmpeg: {}", e)
        return False, str(e)

    if on_proc_start:
        on_proc_start(proc)

    last_progress_time = 0.0
    current_speed = ""
    current_fps = ""
    task_start_time = time.monotonic()

    def _read_stderr() -> None:
        nonlocal last_progress_time, current_speed, current_fps
        try:
            for line in proc.stderr:  # type: ignore[union-attr]
                if cancel_event.is_set():
                    break

                stripped = line.rstrip()
                if on_log:
                    on_log(stripped)

                # Append to task log (keep last 500 lines)
                task.log_lines.append(stripped)
                if len(task.log_lines) > 500:
                    task.log_lines = task.log_lines[-500:]

                # Parse speed and fps from every line
                speed_match = _SPEED_RE.search(line)
                if speed_match:
                    current_speed = speed_match.group(1)
                fps_match = _FPS_RE.search(line)
                if fps_match:
                    current_fps = fps_match.group(1)

                if on_progress and duration > 0:
                    match = _TIME_RE.search(line)
                    if match:
                        current = _parse_time_to_seconds(match)
                        percent = min(current / duration * 100, 100)

                        now = time.monotonic()
                        if now - last_progress_time >= 0.5:
                            last_progress_time = now
                            # Calculate estimated remaining time
                            estimated_remaining = ""
                            elapsed = now - task_start_time
                            if percent > 1 and elapsed > 0:
                                remaining = (elapsed / percent) * (100 - percent)
                                mins = int(remaining // 60)
                                secs = int(remaining % 60)
                                if mins > 0:
                                    estimated_remaining = f"{mins}m {secs}s"
                                else:
                                    estimated_remaining = f"{secs}s"

                            progress = TaskProgress(
                                percent=percent,
                                current_seconds=current,
                                total_seconds=duration,
                                speed=current_speed,
                                fps=current_fps,
                                estimated_remaining=estimated_remaining,
                            )
                            task.update_progress(progress)
                            on_progress(progress)
        except Exception:
            logger.exception("Error reading stderr (task {})", task.id)

    reader_thread = threading.Thread(target=_read_stderr, daemon=True)
    reader_thread.start()

    # Wait for process to finish OR cancellation
    returncode = 0
    try:
        while True:
            if cancel_event.is_set():
                kill_process_tree(proc.pid)
                logger.info("FFmpeg process killed (task {})", task.id)
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass
                reader_thread.join(timeout=2)
                return False, "Cancelled"

            returncode = proc.poll()
            if returncode is not None:
                break

            time.sleep(0.1)
    except Exception as e:
        logger.error("Exception during proc wait (task {}): {}", task.id, e)
        kill_process_tree(proc.pid)
        returncode = -1

    reader_thread.join(timeout=2)

    if returncode == 0:
        if on_progress:
            progress = TaskProgress(
                percent=100.0,
                current_seconds=duration,
                total_seconds=duration,
                speed=current_speed,
                fps=current_fps,
                estimated_remaining="",
            )
            task.update_progress(progress)
            on_progress(progress)
        logger.info("FFmpeg completed (task {})", task.id)
        return True, ""

    logger.error("FFmpeg exited with code {} (task {})", returncode, task.id)
    return False, f"FFmpeg exited with code {returncode}"
