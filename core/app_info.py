"""FFmpeg version detection and application metadata."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from core.logging import get_logger

logger = get_logger()

# Module-level cache
_ffmpeg_version: str | None = None
_ffprobe_version: str | None = None

_VERSION_RE = re.compile(r"ffmpeg version\s+([^\s]+)", re.IGNORECASE)
_FFPROBE_VERSION_RE = re.compile(r"ffprobe version\s+([^\s]+)", re.IGNORECASE)


def _run_version_cmd(binary_path: str) -> str:
    """Run `{binary} -version` and return stdout."""
    try:
        result = subprocess.run(
            [binary_path, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout
    except Exception as exc:
        logger.warning("Failed to run {} -version: {}", binary_path, exc)
        return ""


def get_ffmpeg_version(ffmpeg_path: str | None) -> str | None:
    """Get FFmpeg version string (e.g. '6.0'). Cached after first call."""
    global _ffmpeg_version
    if _ffmpeg_version is not None:
        return _ffmpeg_version
    if not ffmpeg_path:
        return None
    output = _run_version_cmd(ffmpeg_path)
    match = _VERSION_RE.search(output)
    if match:
        _ffmpeg_version = match.group(1)
        return _ffmpeg_version
    return None


def get_ffprobe_version(ffprobe_path: str | None) -> str | None:
    """Get FFprobe version string. Cached after first call."""
    global _ffprobe_version
    if _ffprobe_version is not None:
        return _ffprobe_version
    if not ffprobe_path:
        return None
    output = _run_version_cmd(ffprobe_path)
    match = _FFPROBE_VERSION_RE.search(output)
    if match:
        _ffprobe_version = match.group(1)
        return _ffprobe_version
    return None


def get_app_info() -> dict:
    """Return application metadata including FFmpeg/FFprobe versions."""
    from core.ffmpeg_setup import get_ffmpeg_path, get_ffprobe_path

    ffmpeg_path = get_ffmpeg_path()
    ffprobe_path = get_ffprobe_path()

    return {
        "app_name": "FF Intelligent",
        "app_version": _read_project_version(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "ffmpeg_path": ffmpeg_path or "",
        "ffmpeg_version": get_ffmpeg_version(ffmpeg_path),
        "ffprobe_path": ffprobe_path or "",
        "ffprobe_version": get_ffprobe_version(ffprobe_path),
        "is_packaged": bool(getattr(sys, "frozen", False)),
    }


def _read_project_version() -> str:
    """Read version from pyproject.toml."""
    try:
        toml_path = Path(__file__).parent.parent / "pyproject.toml"
        if not toml_path.exists():
            # PyInstaller: check _MEIPASS
            if hasattr(sys, "_MEIPASS"):
                toml_path = Path(sys._MEIPASS) / "pyproject.toml"
        if toml_path.exists():
            content = toml_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.strip().startswith("version"):
                    match = re.match(r'version\s*=\s*"([^"]+)"', line.strip())
                    if match:
                        return match.group(1)
    except Exception as exc:
        logger.debug("Could not read project version: {}", exc)
    return "unknown"
