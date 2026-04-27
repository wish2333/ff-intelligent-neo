"""auto-editor command builder, input validation, and progress parser.

Provides utilities for integrating auto-editor v30.1.4+ into the task
pipeline: input validation, CLI command construction, output path
generation, and machine-format progress parsing.
"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from core.logging import get_logger

logger = get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: set[str] = {
    ".mp4", ".mov", ".mkv", ".m4v",
    ".mp3", ".wav", ".m4a", ".aac",
}

URL_SCHEMES: set[str] = {"http", "https", "ftp", "ftps", "rtsp", "rtmp"}

# dash-only CLI flags for auto-editor
_EDIT_ACTIONS = {"audio", "motion", "subtitle"}

_CONTAINER_TOGGLES = {
    "vn", "an", "sn", "dn",
}


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def validate_local_input(input_file: str) -> Path:
    """Validate a local input file for auto-editor processing.

    Rejects URL inputs, validates file existence and extension.

    Args:
        input_file: Path or URL to validate.

    Returns:
        Resolved absolute Path.

    Raises:
        ValueError: If input is a URL, file doesn't exist, or extension
            is not supported.
    """
    # Reject URL inputs
    if "://" in input_file:
        scheme = input_file.split("://")[0].lower()
        if scheme in URL_SCHEMES:
            raise ValueError("URL input is not supported for auto-editor")

    path = Path(input_file).resolve()

    if not path.exists():
        raise ValueError(f"File not found: {input_file}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    return path


# ---------------------------------------------------------------------------
# Command builder
# ---------------------------------------------------------------------------


def build_command(
    input_file: str,
    params: dict,
    auto_editor_path: str,
    output_path: str | None = None,
) -> list[str]:
    """Build auto-editor CLI command from UI parameters.

    Args:
        input_file: Path to input media file.
        params: UI parameters dict (dash-form keys).
        auto_editor_path: Path to auto-editor binary.
        output_path: Output file path. None in preview mode.

    Returns:
        List of command-line arguments (including binary).
    """
    cmd: list[str] = [auto_editor_path]

    # Input file
    cmd.append(str(input_file))

    # --progress machine (always added)
    cmd.extend(["--progress", "machine"])

    # Edit method with embedded threshold: --edit audio:0.04 or --edit motion:0.02
    # https://auto-editor.com/ref/edit
    edit_method = params.get("edit", "audio")
    if edit_method in _EDIT_ACTIONS:
        threshold = params.get("audio_threshold" if edit_method == "audio" else "motion_threshold",
                               params.get("threshold", ""))
        if threshold:
            cmd.extend(["--edit", f"{edit_method}:{threshold}"])
        else:
            cmd.extend(["--edit", edit_method])

    # Margin
    margin = params.get("margin", "")
    if margin:
        cmd.extend(["--margin", str(margin)])

    # Smooth
    smooth = params.get("smooth", "")
    if smooth:
        cmd.extend(["--smooth", str(smooth)])

    # When-silent action
    when_silent = params.get("when_silent", params.get("when-silent", "cut"))
    if when_silent and when_silent != "nil":
        cmd.extend(["--when-silent", str(when_silent)])

    # When-normal action
    when_normal = params.get("when_normal", params.get("when-normal", "nil"))
    if when_normal and when_normal != "nil":
        cmd.extend(["--when-normal", str(when_normal)])

    # --- Advanced params ---

    # Multi-range flags
    for flag_key in ("cut_out", "cut-out"):
        ranges = params.get(flag_key, params.get("cut_out_ranges", []))
        if ranges and isinstance(ranges, list):
            for r in ranges:
                cmd.extend(["--cut-out", str(r)])
            break

    for flag_key in ("add_in", "add-in"):
        ranges = params.get(flag_key, params.get("add_in_ranges", []))
        if ranges and isinstance(ranges, list):
            for r in ranges:
                cmd.extend(["--add-in", str(r)])
            break

    for flag_key in ("set_action", "set-action"):
        ranges = params.get(flag_key, params.get("set_action_ranges", []))
        if ranges and isinstance(ranges, list):
            for r in ranges:
                cmd.extend(["--set-action", str(r)])
            break

    # Frame rate
    frame_rate = params.get("frame_rate", params.get("frame-rate", ""))
    if frame_rate:
        cmd.extend(["--frame-rate", str(frame_rate)])

    # Sample rate
    sample_rate = params.get("sample_rate", params.get("sample-rate", ""))
    if sample_rate:
        cmd.extend(["--sample-rate", str(sample_rate)])

    # Resolution
    resolution = params.get("resolution", "")
    if resolution:
        cmd.extend(["--resolution", str(resolution)])

    # Container toggles
    for toggle in ("vn", "an", "sn", "dn"):
        if params.get(toggle, False):
            cmd.append(f"-{toggle}")

    # Video codec
    video_codec = params.get("video_codec", params.get("video-codec", ""))
    if video_codec:
        cmd.extend(["--video-codec", str(video_codec)])

    # Audio codec
    audio_codec = params.get("audio_codec", params.get("audio-codec", ""))
    if audio_codec:
        cmd.extend(["--audio-codec", str(audio_codec)])

    # Bitrate
    video_bitrate = params.get("video_bitrate", params.get("b:v", ""))
    if video_bitrate:
        cmd.extend(["-b:v", str(video_bitrate)])

    audio_bitrate = params.get("audio_bitrate", params.get("b:a", ""))
    if audio_bitrate:
        cmd.extend(["-b:a", str(audio_bitrate)])

    # CRF
    crf = params.get("crf", "")
    if crf:
        cmd.extend(["-crf", str(crf)])

    # Audio layout
    audio_layout = params.get("audio_layout", params.get("audio-layout", ""))
    if audio_layout:
        cmd.extend(["--audio-layout", str(audio_layout)])

    # Audio normalize
    audio_normalize = params.get("audio_normalize", params.get("audio-normalize", ""))
    if audio_normalize:
        cmd.extend(["--audio-normalize", str(audio_normalize)])

    # No cache
    if params.get("no_cache", params.get("no-cache", False)):
        cmd.append("--no-cache")

    # Open (with warning handled at API layer)
    if params.get("open", False):
        cmd.append("--open")

    # Faststart (default ON = no flag; OFF = --no-faststart)
    if params.get("faststart", True) is False:
        cmd.append("--no-faststart")

    # Fragmented (default OFF = no flag; ON = --fragmented)
    if params.get("fragmented", False) is True:
        cmd.append("--fragmented")

    # Output path (only if not in preview mode)
    is_preview = params.get("_preview_mode", False)
    if output_path and not is_preview:
        cmd.extend(["--output", str(output_path)])
    elif is_preview:
        # Placeholder for preview - won't create real file
        cmd.extend(["--output", str(Path(input_file).with_name("_preview_output.mp4"))])

    return cmd


# ---------------------------------------------------------------------------
# Output path generation
# ---------------------------------------------------------------------------


def generate_output_path(
    input_file: str,
    output_dir: str,
    task_id: str,
    extension: str = ".mp4",
) -> Path:
    """Generate a unique output path within output_dir.

    Args:
        input_file: Original input file path.
        output_dir: Target output directory.
        task_id: Task identifier (used for uniqueness).
        extension: Output file extension (with dot).

    Returns:
        Resolved Path for the output file.

    Raises:
        ValueError: If output_dir doesn't exist, isn't a directory, or
            isn't writable, or if path traversal is detected.
    """
    dir_path = Path(output_dir).resolve()

    if not dir_path.exists():
        raise ValueError(f"Output directory does not exist: {output_dir}")
    if not dir_path.is_dir():
        raise ValueError(f"Output path is not a directory: {output_dir}")
    if not os.access(dir_path, os.W_OK):
        raise ValueError(f"Output directory is not writable: {output_dir}")

    # Path traversal prevention: check the raw input_file for traversal patterns
    # Normalize to forward slashes for consistent checking
    normalized_input = input_file.replace("\\", "/")
    if ".." in normalized_input or normalized_input.startswith("/") or "//" in normalized_input:
        raise ValueError(f"Invalid input file name for path generation: {input_file}")

    stem = Path(input_file).stem
    # Normalize extension: ensure it starts with '.'
    if extension and not extension.startswith("."):
        extension = f".{extension}"

    short_id = task_id[:8] if len(task_id) >= 8 else task_id
    filename = f"{stem}_{short_id}{extension}"

    output = dir_path / filename

    # Verify output stays within output_dir (defense in depth)
    if not str(output.resolve()).startswith(str(dir_path)):
        raise ValueError("Output path traversal detected")

    return output


# ---------------------------------------------------------------------------
# Progress parser (--progress machine format)
# ---------------------------------------------------------------------------

# Format: title~current~total~eta_seconds
# Example: "Video~123~1000~45.2"
_SEGMENT_RE = re.compile(
    r"^(.+?)~(\d+(?:\.\d+)?)~(\d+(?:\.\d+)?)~(\d+(?:\.\d+)?)\s*$"
)


def parse_auto_editor_segment(segment: str) -> dict | None:
    """Parse a single auto-editor machine-progress segment.

    Expected format: ``title~current~total~eta_seconds``
    The title may contain literal ``~`` characters, so we match from
    the right (last 3 fields are numeric).

    Args:
        segment: Raw segment string (may include trailing \\r or \\n).

    Returns:
        Dict with progress info, or a log entry dict for non-machine lines.
        Returns None for empty/whitespace-only segments.
    """
    stripped = segment.strip()
    if not stripped:
        return None

    match = _SEGMENT_RE.match(stripped)
    if match:
        title = match.group(1)
        current = float(match.group(2))
        total = float(match.group(3))
        eta_seconds = float(match.group(4))

        progress = (current / total * 100) if total > 0 else 0.0

        return {
            "type": "progress",
            "title": title,
            "current": current,
            "total": total,
            "progress": round(progress, 1),
            "eta_seconds": eta_seconds,
        }

    return {"type": "log", "message": stripped}


def read_auto_editor_output(proc):
    """Generator that reads auto-editor stdout and yields parsed segments.

    auto-editor with ``--progress machine`` outputs progress on stdout
    separated by ``\\r``. This generator reads in 4096-byte chunks,
    splits on ``\\r``, and yields parsed result dicts from
    :func:`parse_auto_editor_segment`.

    Args:
        proc: subprocess.Popen instance with stdout=PIPE.

    Yields:
        dicts from parse_auto_editor_segment (progress or log entries).
    """
    buf = b""
    while True:
        chunk = proc.stdout.read(4096)
        if not chunk:
            # Process ended - flush remaining buffer
            if buf:
                result = parse_auto_editor_segment(buf.decode("utf-8", errors="replace"))
                if result:
                    yield result
            break

        buf += chunk
        while b"\r" in buf:
            segment, buf = buf.split(b"\r", 1)
            result = parse_auto_editor_segment(segment.decode("utf-8", errors="replace"))
            if result:
                yield result
