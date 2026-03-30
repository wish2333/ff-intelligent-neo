"""FFmpeg binary setup using static-ffmpeg package."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _find_static_ffmpeg_bin(name: str) -> str | None:
    """Locate a binary (ffmpeg/ffprobe) from static_ffmpeg package directory.

    Falls back to PATH lookup if package-based lookup fails.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Try PATH first (handles system-installed ffmpeg)
    path_result = shutil.which(name)
    if path_result:
        logger.info("[ffmpeg_setup] Found {} in PATH: {}", name, path_result)
        return path_result

    # Try to find via static_ffmpeg package location
    try:
        import static_ffmpeg
        pkg_dir = Path(static_ffmpeg.__file__).parent
        logger.info("[ffmpeg_setup] static_ffmpeg package dir: {}", pkg_dir)
        # Look for bin/<platform>/<name> or bin/<platform>/<name>.exe
        for pattern in [f"bin/*/{name}", f"bin/*/{name}.exe", f"bin/*/{name}.EXE"]:
            matches = list(pkg_dir.glob(pattern))
            if matches:
                logger.info("[ffmpeg_setup] Found {} via pattern {}: {}", name, pattern, matches[0])
                return str(matches[0])
        # Also check bin subdirectories directly
        for bin_dir in pkg_dir.glob("bin/*"):
            if bin_dir.is_dir():
                candidate = bin_dir / f"{name}.exe" if sys.platform == "win32" else bin_dir / name
                if candidate.exists():
                    logger.info("[ffmpeg_setup] Found {} in bin dir: {}", name, candidate)
                    return str(candidate)
                else:
                    logger.debug("[ffmpeg_setup] Candidate does not exist: {}", candidate)
    except (ImportError, Exception) as e:
        logger.warning("[ffmpeg_setup] Error accessing static_ffmpeg: {}", e)

    logger.warning("[ffmpeg_setup] {} not found", name)
    return None


def ensure_ffmpeg() -> bool:
    """Download ffmpeg binaries if needed and verify availability.

    Returns True if ffmpeg is available after this call.
    """
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except ImportError:
        pass

    return _find_static_ffmpeg_bin("ffmpeg") is not None


def is_ffmpeg_ready() -> bool:
    """Check if ffmpeg is already on PATH without downloading."""
    return _find_static_ffmpeg_bin("ffmpeg") is not None


def get_ffmpeg_path() -> str | None:
    """Return the ffmpeg binary path, or None."""
    return _find_static_ffmpeg_bin("ffmpeg")


def get_ffprobe_path() -> str | None:
    """Return the ffprobe binary path, or None."""
    return _find_static_ffmpeg_bin("ffprobe")
