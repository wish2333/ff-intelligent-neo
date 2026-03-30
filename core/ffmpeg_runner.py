"""Single-file FFmpeg execution with progress parsing."""

from __future__ import annotations

import re
import subprocess
import threading
import time

from core.logging import get_logger

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
        info = __import__("json").loads(result.stdout)
        return float(info.get("format", {}).get("duration", 0))
    except Exception as exc:
        logger.warning("Failed to get duration for {}: {}", file_path, exc)
        return 0.0


def run_single(
    ffmpeg_path: str,
    ffprobe_path: str,
    args: list[str],
    cancel_event: threading.Event,
    on_progress=None,
    on_log=None,
) -> tuple[bool, str]:
    """Execute a single FFmpeg command with progress tracking.

    Args:
        ffmpeg_path: Path to ffmpeg binary.
        ffprobe_path: Path to ffprobe binary.
        args: FFmpeg arguments (without the binary name).
        cancel_event: Threading event to signal cancellation.
        on_progress: Callback(percent: float, time_str: str, speed: str, fps: str).
        on_log: Callback(line: str).

    Returns:
        Tuple of (success: bool, error_message: str).
    """
    # Find input file in args to get duration
    input_path = ""
    for i, arg in enumerate(args):
        if arg == "-i" and i + 1 < len(args):
            input_path = args[i + 1]
            break

    duration = 0.0
    if input_path and ffprobe_path:
        duration = _get_duration_seconds(ffprobe_path, input_path)

    cmd = [ffmpeg_path, "-hide_banner", "-y", *args]
    logger.debug("Running: {}", " ".join(cmd))

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as e:
        logger.error("Failed to start ffmpeg: {}", e)
        return False, str(e)

    last_progress_time = 0.0
    current_speed = ""
    current_fps = ""

    def _read_stderr():
        nonlocal last_progress_time, current_speed, current_fps
        try:
            for line in proc.stderr:  # type: ignore[union-attr]
                if cancel_event.is_set():
                    break

                if on_log:
                    on_log(line.rstrip())

                # Parse speed and fps from every line (they appear periodically)
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
                            on_progress(percent, match.group(0), current_speed, current_fps)
        except Exception:
            pass

    reader_thread = threading.Thread(target=_read_stderr, daemon=True)
    reader_thread.start()

    # Wait for process to finish OR cancellation
    try:
        while True:
            # 检查取消请求
            if cancel_event.is_set():
                proc.kill()
                logger.info("FFmpeg process killed due to cancel request")
                # 等待进程真正结束
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass
                reader_thread.join(timeout=2)
                return False, "Cancelled"

            # 检查进程是否自然结束
            returncode = proc.poll()
            if returncode is not None:
                # 进程结束
                break

            # 短暂休眠避免忙等待
            time.sleep(0.1)

    except Exception as e:
        logger.error("Exception during proc wait: {}", e)
        proc.kill()
        returncode = -1

    # 等待读取线程结束
    reader_thread.join(timeout=2)

    if returncode == 0:
        if on_progress:
            on_progress(100, "", current_speed, current_fps)
        logger.info("FFmpeg completed successfully")
        return True, ""
    else:
        logger.error("FFmpeg exited with code {}", returncode)
        return False, f"FFmpeg exited with code {returncode}"
