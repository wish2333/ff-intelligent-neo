# /// script
# requires-python = ">=3.10"
# dependencies = ["static-ffmpeg"]
# ///
"""Pre-build script: download FFmpeg binaries for packaging.

Run before PyInstaller to ensure ffmpeg_binaries/ contains
platform-specific ffmpeg and ffprobe binaries.

Usage:
    uv run scripts/pre_build.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FFMPEG_BIN_DIR = PROJECT_ROOT / "ffmpeg_binaries"


def _ffprobe_name() -> str:
    """Return the ffprobe binary name for the current platform."""
    return "ffprobe.exe" if sys.platform == "win32" else "ffprobe"


def _ffmpeg_name() -> str:
    """Return the ffmpeg binary name for the current platform."""
    return "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"


def _is_bin_valid(bin_path: Path) -> bool:
    """Check if a binary exists and is executable."""
    if not bin_path.exists():
        return False
    try:
        subprocess.run(
            [str(bin_path), "-version"],
            capture_output=True,
            timeout=10,
        )
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


def _existing_binaries_valid() -> bool:
    """Check if ffmpeg_binaries/ already has valid binaries."""
    return _is_bin_valid(FFMPEG_BIN_DIR / _ffmpeg_name())


def _download_ffmpeg() -> None:
    """Download FFmpeg via static-ffmpeg and copy to ffmpeg_binaries/."""
    import static_ffmpeg

    static_ffmpeg.add_paths()

    pkg_dir = Path(static_ffmpeg.__file__).parent

    FFMPEG_BIN_DIR.mkdir(parents=True, exist_ok=True)

    copied = 0
    for name in (_ffmpeg_name(), _ffprobe_name()):
        # Try to find via static_ffmpeg package directory
        found = False
        for pattern in [f"bin/*/{name}", f"bin/*/{name}.EXE"]:
            matches = list(pkg_dir.glob(pattern))
            if matches:
                dst = FFMPEG_BIN_DIR / name
                shutil.copy2(matches[0], dst)
                # Ensure executable permission on non-Windows
                if sys.platform != "win32":
                    dst.chmod(0o755)
                print(f"[pre_build] Copied {matches[0]} -> {dst}")
                found = True
                copied += 1
                break

        if not found:
            print(f"[pre_build] WARNING: {name} not found in static_ffmpeg package")

    if copied == 0:
        print(
            "[pre_build] ERROR: No FFmpeg binaries found after download.\n"
            "  Check your network connection and try again.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    if _existing_binaries_valid():
        print("[pre_build] ffmpeg_binaries/ already valid, skipping download.")
        return

    print("[pre_build] FFmpeg binaries not found or invalid. Downloading...")
    try:
        _download_ffmpeg()
    except Exception as e:
        print(
            f"[pre_build] ERROR: Failed to download FFmpeg: {e}\n"
            "  Please check your network connection and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Verify after download
    if not _existing_binaries_valid():
        print(
            "[pre_build] ERROR: FFmpeg binaries invalid after download.\n"
            "  Please check your network connection and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("[pre_build] FFmpeg binaries ready.")


if __name__ == "__main__":
    main()
