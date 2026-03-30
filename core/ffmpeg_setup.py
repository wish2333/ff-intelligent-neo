"""FFmpeg binary setup using static-ffmpeg package."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Check if running as a PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def _find_bundled_ffmpeg_bin(name: str) -> str | None:
    """Locate a binary from the PyInstaller bundle directory.

    In onedir mode, binaries are next to the executable.
    In onefile mode, binaries are in sys._MEIPASS.
    """
    if not is_frozen():
        return None

    import logging
    logger = logging.getLogger(__name__)

    suffix = ".exe" if sys.platform == "win32" else ""
    bin_name = f"{name}{suffix}"

    # Check sys._MEIPASS (onefile) and executable directory (onedir)
    search_dirs = []
    if hasattr(sys, '_MEIPASS'):
        search_dirs.append(Path(sys._MEIPASS))
    if hasattr(sys, 'executable'):
        search_dirs.append(Path(sys.executable).parent)

    for search_dir in search_dirs:
        candidate = search_dir / bin_name
        if candidate.exists():
            logger.info("[ffmpeg_setup] Found bundled {}: {}", name, candidate)
            return str(candidate)

    logger.warning("[ffmpeg_setup] Bundled {} not found", name)
    return None


def _find_static_ffmpeg_bin(name: str) -> str | None:
    """Locate a binary (ffmpeg/ffprobe) from various sources.

    Priority:
    1. Bundled binary (PyInstaller packaged)
    2. PATH (system-installed ffmpeg)
    3. static_ffmpeg package directory
    """
    import logging
    logger = logging.getLogger(__name__)

    # 1. Bundled binary (packaged environment)
    bundled = _find_bundled_ffmpeg_bin(name)
    if bundled:
        return bundled

    # 2. Try PATH (handles system-installed ffmpeg)
    path_result = shutil.which(name)
    if path_result:
        logger.info("[ffmpeg_setup] Found {} in PATH: {}", name, path_result)
        return path_result

    # 3. Try to find via static_ffmpeg package location
    try:
        import static_ffmpeg
        pkg_dir = Path(static_ffmpeg.__file__).parent
        logger.info("[ffmpeg_setup] static_ffmpeg package dir: {}", pkg_dir)
        for pattern in [f"bin/*/{name}", f"bin/*/{name}.exe", f"bin/*/{name}.EXE"]:
            matches = list(pkg_dir.glob(pattern))
            if matches:
                logger.info("[ffmpeg_setup] Found {} via pattern {}: {}", name, pattern, matches[0])
                return str(matches[0])
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

    In packaged environment: uses bundled binaries, no download.
    In dev environment: uses static_ffmpeg.add_paths() to download if needed.

    Returns True if ffmpeg is available after this call.
    """
    if is_frozen():
        return _find_static_ffmpeg_bin("ffmpeg") is not None

    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except ImportError:
        pass

    return _find_static_ffmpeg_bin("ffmpeg") is not None


def is_ffmpeg_ready() -> bool:
    """Check if ffmpeg is already available without downloading."""
    return _find_static_ffmpeg_bin("ffmpeg") is not None


def get_ffmpeg_path() -> str | None:
    """Return the ffmpeg binary path, or None."""
    return _find_static_ffmpeg_bin("ffmpeg")


def get_ffprobe_path() -> str | None:
    """Return the ffprobe binary path, or None."""
    return _find_static_ffmpeg_bin("ffprobe")
