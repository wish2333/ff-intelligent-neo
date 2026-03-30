"""File metadata extraction via ffprobe."""

from __future__ import annotations

import json
import subprocess

from core.models import FileItem


def probe_file(file_path: str) -> FileItem:
    """Probe a media file with ffprobe and return a FileItem.

    Falls back gracefully if ffprobe is unavailable -- returns a
    FileItem with empty metadata fields.
    """
    from pathlib import Path

    p = Path(file_path)
    name = p.name
    size_bytes = p.stat().st_size if p.exists() else 0

    ffprobe = __import__("core.ffmpeg_setup", fromlist=["get_ffprobe_path"]).get_ffprobe_path()
    if ffprobe is None:
        return FileItem(
            path=file_path, name=name, size_bytes=size_bytes,
        )

    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            return FileItem(
                path=file_path, name=name, size_bytes=size_bytes,
            )

        info = json.loads(result.stdout)
        return _parse_probe(file_path, name, size_bytes, info)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return FileItem(
            path=file_path, name=name, size_bytes=size_bytes,
        )


def _parse_probe(
    file_path: str,
    name: str,
    size_bytes: int,
    info: dict,
) -> FileItem:
    """Extract relevant fields from ffprobe JSON output."""
    fmt = info.get("format", {})
    duration = float(fmt.get("duration", 0))
    format_name = fmt.get("format_name", "")

    video_codec = ""
    audio_codec = ""
    width = 0
    height = 0

    for stream in info.get("streams", []):
        codec_type = stream.get("codec_type", "")
        codec_name = stream.get("codec_name", "")

        if codec_type == "video" and not video_codec:
            video_codec = codec_name
            width = int(stream.get("width", 0))
            height = int(stream.get("height", 0))
        elif codec_type == "audio" and not audio_codec:
            audio_codec = codec_name

    return FileItem(
        path=file_path,
        name=name,
        size_bytes=size_bytes,
        duration_seconds=duration,
        video_codec=video_codec,
        audio_codec=audio_codec,
        width=width,
        height=height,
        format_name=format_name,
    )
