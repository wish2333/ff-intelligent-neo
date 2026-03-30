"""Frozen dataclasses for type-safe data transfer between layers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileItem:
    """A single media file with probed metadata."""

    path: str
    name: str
    size_bytes: int
    duration_seconds: float = 0.0
    video_codec: str = ""
    audio_codec: str = ""
    width: int = 0
    height: int = 0
    format_name: str = ""


@dataclass(frozen=True)
class Preset:
    """An FFmpeg conversion preset."""

    id: str
    name: str
    description: str = ""
    output_extension: str = ".mp4"
    command_template: str = ""
    is_default: bool = False


@dataclass(frozen=True)
class TaskProgress:
    """Progress info for a single conversion task."""

    file_index: int
    file_name: str
    percent: float = 0.0
    time_str: str = ""
    status: str = "pending"  # pending | running | done | error
    error: str = ""
    output_path: str = ""
    speed: str = ""
    fps: str = ""
