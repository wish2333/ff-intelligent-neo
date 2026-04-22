"""Build FFmpeg command-line arguments from TaskConfig.

Phase 2a scope: basic transcode parameters only (codec, bitrate,
resolution, framerate, output extension).  Filter chain support is
added in Phase 3.
"""

from __future__ import annotations

from pathlib import Path

from core.models import TaskConfig


def build_command(
    config: TaskConfig,
    input_path: str,
    output_path: str,
) -> list[str]:
    """Build the full FFmpeg argument list (without the binary name).

    Args:
        config: Task configuration containing transcode params.
        input_path: Source media file path.
        output_path: Destination file path.

    Returns:
        List of arguments to pass to subprocess.Popen, e.g.
        ``["-i", "input.mp4", "-c:v", "libx264", ...]``
    """
    tc = config.transcode
    args: list[str] = []

    # --- input ---
    args.extend(["-i", input_path])

    # --- video codec ---
    vcodec = tc.video_codec.lower()
    if vcodec == "none":
        args.append("-vn")
    elif vcodec == "copy":
        args.extend(["-c:v", "copy"])
    else:
        args.extend(["-c:v", vcodec])
        # video bitrate (only when re-encoding)
        if tc.video_bitrate:
            args.extend(["-b:v", tc.video_bitrate])

        # resolution / scale filter
        if tc.resolution:
            args.extend(["-vf", f"scale={tc.resolution}"])

    # --- audio codec ---
    acodec = tc.audio_codec.lower()
    if acodec == "none":
        args.append("-an")
    elif acodec == "copy":
        args.extend(["-c:a", "copy"])
    else:
        args.extend(["-c:a", acodec])
        if tc.audio_bitrate:
            args.extend(["-b:a", tc.audio_bitrate])

    # --- framerate ---
    if tc.framerate and vcodec != "copy":
        args.extend(["-r", tc.framerate])

    # --- overwrite + output ---
    args.extend(["-y", output_path])

    return args


def build_output_path(
    input_path: str,
    config: TaskConfig,
    output_dir: str = "",
    timestamp: str = "",
) -> str:
    """Compute the output file path for a given input.

    If *output_dir* is empty the output goes next to the source file.
    When outputting to the source directory, a *timestamp* suffix is
    appended to the stem to avoid overwriting the original file
    (e.g. ``video-20260422_210000.mp4``).

    Args:
        input_path: Source file path.
        config: Task configuration (reads output_extension).
        output_dir: Override directory (empty = same as source).
        timestamp: Timestamp string in ``YYYYMMDD_HHMMSS`` format.

    Returns:
        Full output path string.
    """
    from datetime import datetime

    src = Path(input_path)
    ext = config.transcode.output_extension or src.suffix

    same_dir = not output_dir
    if same_dir and not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    stem = src.stem
    if same_dir:
        filename = f"{stem}-{timestamp}{ext}"
    else:
        filename = f"{stem}{ext}"

    if output_dir:
        return str(Path(output_dir) / filename)
    return str(src.parent / filename)
