"""FFmpeg binary discovery, setup, and version management.

Priority chain for FFmpeg resolution:
1. User-specified path (from settings, highest priority)
2. Bundled binary (PyInstaller environment)
3. Local ./ffmpeg/ folder (alongside the application)
4. Platform-specific known paths (Homebrew, Linux package managers)
5. System PATH (shutil.which)
6. static_ffmpeg package (may download on first call)
"""

from __future__ import annotations

import os
import platform as _platform
import shutil
import sys
from pathlib import Path

from core.logging import get_logger

logger = get_logger()

# Module-level caches
_ffmpeg_override_path: str | None = None
_ffmpeg_override_ffprobe: str | None = None


def is_frozen() -> bool:
    """Check if running as a PyInstaller bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


# ---------------------------------------------------------------------------
# Bundled binary lookup (PyInstaller)
# ---------------------------------------------------------------------------


def _find_bundled_bin(name: str) -> str | None:
    """Locate a binary from the PyInstaller bundle directory."""
    if not is_frozen():
        return None

    suffix = ".exe" if sys.platform == "win32" else ""
    bin_name = f"{name}{suffix}"

    search_dirs = []
    if hasattr(sys, "_MEIPASS"):
        search_dirs.append(Path(sys._MEIPASS))
    if hasattr(sys, "executable"):
        search_dirs.append(Path(sys.executable).parent)

    for search_dir in search_dirs:
        candidate = search_dir / bin_name
        if candidate.exists():
            logger.info("[ffmpeg_setup] Found bundled {}: {}", name, candidate)
            return str(candidate)

    logger.warning("[ffmpeg_setup] Bundled {} not found", name)
    return None


# ---------------------------------------------------------------------------
# Platform-known paths
# ---------------------------------------------------------------------------


def _find_platform_bin(name: str) -> str | None:
    """Check platform-specific known installation paths."""
    suffix = ".exe" if sys.platform == "win32" else ""
    known: list[str] = []

    machine = _platform.machine().lower()
    if sys.platform == "darwin":
        if machine in ("arm64", "aarch64"):
            known = ["/opt/homebrew/bin/{name}"]
        else:
            known = ["/usr/local/bin/{name}"]
    elif sys.platform.startswith("linux"):
        known = [
            "/usr/bin/{name}",
            "/usr/local/bin/{name}",
            "/snap/bin/{name}",
            "/usr/lib/flatpak/bin/{name}",
        ]

    for template in known:
        candidate = Path(template.format(name=f"{name}{suffix}"))
        if candidate.is_file():
            return str(candidate)
    return None


# ---------------------------------------------------------------------------
# Local ./ffmpeg/ folder detection
# ---------------------------------------------------------------------------


def _find_local_ffmpeg_bin(name: str) -> str | None:
    """Check for FFmpeg binaries in the application's sibling ./ffmpeg/ folder.

    Skipped in PyInstaller frozen environments (bundled binaries are
    resolved by ``_find_bundled_bin`` instead).
    """
    if is_frozen():
        return None

    suffix = ".exe" if sys.platform == "win32" else ""
    bin_name = f"{name}{suffix}"

    # Application root: work backwards from this file's location
    app_root = Path(__file__).resolve().parent.parent
    local_dir = app_root / "ffmpeg"

    if local_dir.is_dir():
        candidate = local_dir / bin_name
        if candidate.is_file():
            logger.info("[ffmpeg_setup] Found local {}: {}", name, candidate)
            return str(candidate)
    return None


# ---------------------------------------------------------------------------
# static_ffmpeg lookup
# ---------------------------------------------------------------------------


def _remove_static_ffmpeg_from_path() -> None:
    """Temporarily remove static_ffmpeg directories from PATH.

    This prevents static_ffmpeg binaries from shadowing system-installed
    FFmpeg when discovering versions.
    """
    try:
        import static_ffmpeg

        pkg_dir = os.path.normpath(Path(static_ffmpeg.__file__).parent)
        current = os.environ.get("PATH", "")
        entries = current.split(os.pathsep)
        filtered = [e for e in entries if os.path.normpath(e) != pkg_dir
                    and not os.path.normpath(e).startswith(pkg_dir + os.sep)]
        os.environ["PATH"] = os.pathsep.join(filtered)
    except ImportError:
        pass


def _find_static_ffmpeg_bin(name: str) -> str | None:
    """Locate a binary from the static_ffmpeg package directory."""
    try:
        import static_ffmpeg

        pkg_dir = Path(static_ffmpeg.__file__).parent
        for pattern in [
            f"bin/*/{name}",
            f"bin/*/{name}.exe",
            f"bin/*/{name}.EXE",
        ]:
            matches = list(pkg_dir.glob(pattern))
            if matches:
                return str(matches[0])

        for bin_dir in pkg_dir.glob("bin/*"):
            if bin_dir.is_dir():
                suffix = ".exe" if sys.platform == "win32" else ""
                candidate = bin_dir / f"{name}{suffix}"
                if candidate.exists():
                    return str(candidate)
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("[ffmpeg_setup] static_ffmpeg error: {}", exc)

    return None


# ---------------------------------------------------------------------------
# Main resolution (priority chain)
# ---------------------------------------------------------------------------


def _resolve_user_path(path_str: str, name: str) -> str | None:
    """Resolve a user-specified path for *name* (ffmpeg / ffprobe)."""
    if not path_str:
        return None
    candidate = path_str.strip()
    # If pointing to a directory, look for the binary inside it
    if os.path.isdir(candidate):
        exe = f"{name}.exe" if sys.platform == "win32" else name
        candidate = os.path.join(candidate, exe)
    if os.path.isfile(candidate):
        return candidate
    return None


def _find_ffprobe_for_ffmpeg(ffmpeg_path: str) -> str | None:
    """Try to find ffprobe in the same directory as ffmpeg."""
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    exe = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
    candidate = os.path.join(ffmpeg_dir, exe)
    if os.path.isfile(candidate):
        return candidate
    return None


def ensure_ffmpeg(ffmpeg_path_override: str = "") -> str | None:
    """Ensure ffmpeg is available, returning its path or None.

    Priority:
    1. User-specified path (from config)
    2. Bundled binary (PyInstaller)
    3. Local ./ffmpeg/ folder (alongside the application)
    4. Platform-specific known paths
    5. System PATH
    6. static_ffmpeg (may download on first call)
    """
    # 1. User-specified path (highest priority)
    if ffmpeg_path_override:
        result = _resolve_user_path(ffmpeg_path_override, "ffmpeg")
        if result:
            return result

    # 2. Bundled binary (packaged environment)
    bundled = _find_bundled_bin("ffmpeg")
    if bundled:
        return bundled

    # 3. Local ./ffmpeg/ folder
    local_path = _find_local_ffmpeg_bin("ffmpeg")
    if local_path:
        return local_path

    # 4. Platform-specific known paths
    platform_path = _find_platform_bin("ffmpeg")
    if platform_path:
        return platform_path

    # 5. System PATH
    path_result = shutil.which("ffmpeg")
    if path_result:
        return path_result

    # 6. static_ffmpeg (may download)
    try:
        import static_ffmpeg

        static_ffmpeg.add_paths()
        path_result = shutil.which("ffmpeg")
        if path_result:
            return path_result
    except Exception as exc:
        logger.warning("static_ffmpeg unavailable: {}", exc)

    return None


def is_ffmpeg_ready() -> bool:
    """Check if ffmpeg is already available without downloading."""
    return get_ffmpeg_path() is not None


def get_ffmpeg_path() -> str | None:
    """Return the active ffmpeg binary path, or None."""
    global _ffmpeg_override_path

    if _ffmpeg_override_path is not None:
        if os.path.isfile(_ffmpeg_override_path):
            return _ffmpeg_override_path
        # Override path no longer valid, clear it
        _ffmpeg_override_path = None

    from core.config import load_settings

    settings = load_settings()
    return ensure_ffmpeg(settings.ffmpeg_path)


def get_ffprobe_path() -> str | None:
    """Return the active ffprobe binary path, or None."""
    global _ffmpeg_override_ffprobe

    if _ffmpeg_override_ffprobe is not None:
        if os.path.isfile(_ffmpeg_override_ffprobe):
            return _ffmpeg_override_ffprobe
        _ffmpeg_override_ffprobe = None

    # Try to derive from ffmpeg path first
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path:
        ffprobe = _find_ffprobe_for_ffmpeg(ffmpeg_path)
        if ffprobe:
            return ffprobe

    # Fallback: same resolution chain for ffprobe
    from core.config import load_settings

    settings = load_settings()
    ffmpeg_override = settings.ffmpeg_path
    if ffmpeg_override:
        # Try same directory as user's ffmpeg
        result = _resolve_user_path(ffmpeg_override, "ffprobe")
        if result:
            return result

    # Try other sources
    for finder in [
        _find_bundled_bin,
        _find_local_ffmpeg_bin,
        _find_platform_bin,
        lambda n: shutil.which(n),
        _find_static_ffmpeg_bin,
    ]:
        result = finder("ffprobe")
        if result:
            return result

    return None


# ---------------------------------------------------------------------------
# Version discovery & switching
# ---------------------------------------------------------------------------


def discover_ffmpeg_versions() -> list[dict]:
    """Discover available FFmpeg installations.

    Search scope (in order):
      1. User-specified path (from settings)
      2. Local ``./ffmpeg/`` directory
      3. Platform-known paths (macOS/Linux only, ``is_file`` check)
      4. System PATH (``shutil.which``)
      5. ``static_ffmpeg`` package directory (Windows only)
      6. Bundled binary (PyInstaller frozen only)

    Returns a list of dicts:
    ``{"path": str, "version": str, "source": str, "active": bool}``
    """
    from core.config import load_settings

    settings = load_settings()
    current_path = get_ffmpeg_path()

    versions: list[dict] = []
    seen_paths: set[str] = set()

    def _add(path: str, source: str) -> None:
        if not path or path in seen_paths:
            return
        seen_paths.add(path)
        is_active = (
            os.path.normpath(path) == os.path.normpath(current_path)
            if current_path else False
        )
        version = _get_version_string(path) if is_active else ""
        versions.append({
            "path": path,
            "version": version,
            "source": source,
            "active": is_active,
        })

    # 1. User-specified
    if settings.ffmpeg_path:
        user_ff = _resolve_user_path(settings.ffmpeg_path, "ffmpeg")
        if user_ff:
            _add(user_ff, "User")

    # 2. Local ./ffmpeg/ folder
    local_path = _find_local_ffmpeg_bin("ffmpeg")
    if local_path:
        _add(local_path, "Local")

    # 3. Platform-known paths (only checks paths for the current OS)
    platform_path = _find_platform_bin("ffmpeg")
    if platform_path:
        _add(platform_path, "System")

    # 4. System PATH
    path_ff = shutil.which("ffmpeg")
    if path_ff:
        _add(path_ff, "PATH")

    # 5. static_ffmpeg (Windows only)
    if sys.platform == "win32":
        static_ff = _find_static_ffmpeg_bin("ffmpeg")
        if static_ff:
            _add(static_ff, "Static FFmpeg")

    # 6. Bundled (PyInstaller only)
    bundled = _find_bundled_bin("ffmpeg")
    if bundled:
        _add(bundled, "Bundled")

    return versions


def _get_version_string(ffmpeg_path: str) -> str | None:
    """Run ffmpeg -version and extract the version number."""
    try:
        import subprocess

        run_kw: dict = {
            "capture_output": True,
            "text": True,
            "timeout": 10,
            "encoding": "utf-8",
            "errors": "replace",
        }
        if sys.platform == "win32":
            run_kw["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            [ffmpeg_path, "-version"],
            **run_kw,
        )
        import re

        match = re.search(
            r"ffmpeg version\s+([^\s]+)", result.stdout, re.IGNORECASE
        )
        if match:
            return match.group(1)
    except Exception as exc:
        logger.debug("Failed to get version for {}: {}", ffmpeg_path, exc)
    return None


def switch_ffmpeg(path: str) -> dict:
    """Switch to a specific FFmpeg binary.

    Validates the path, saves to settings, and returns version info.
    Raises ValueError if the path is invalid.
    """
    if not os.path.isfile(path):
        raise ValueError(f"FFmpeg not found at: {path}")

    version = _get_version_string(path)
    if version is None:
        raise ValueError(
            f"Cannot determine FFmpeg version for: {path}"
        )

    # Save to settings
    from core.config import save_settings
    from core.models import AppSettings

    settings = AppSettings(ffmpeg_path=path)
    save_settings(settings)

    # Clear caches so new path takes effect
    global _ffmpeg_override_path, _ffmpeg_override_ffprobe
    _ffmpeg_override_path = path
    _ffmpeg_override_ffprobe = _find_ffprobe_for_ffmpeg(path)

    # Clear app_info version caches
    try:
        import core.app_info as _ai

        _ai._ffmpeg_version = None
        _ai._ffprobe_version = None
    except Exception:
        pass

    logger.info("Switched FFmpeg to: {} (v{})", path, version)

    return {
        "path": path,
        "version": version,
        "ffprobe_path": _ffmpeg_override_ffprobe or "",
    }
