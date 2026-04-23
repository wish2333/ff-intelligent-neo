"""Frozen dataclasses for type-safe data transfer between layers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

TaskState = Literal[
    "pending", "running", "paused", "completed", "failed", "cancelled"
]

VALID_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    "pending": {"running", "cancelled"},
    "running": {"paused", "completed", "failed", "cancelled"},
    "paused": {"running", "cancelled"},
    "failed": {"pending"},
    "completed": set(),
    "cancelled": set(),
}


# ---------------------------------------------------------------------------
# Transcode parameters
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TranscodeConfig:
    """FFmpeg encoding parameters."""

    video_codec: str = "libx264"
    audio_codec: str = "aac"
    video_bitrate: str = ""
    audio_bitrate: str = ""
    resolution: str = ""
    framerate: str = ""
    output_extension: str = ".mp4"

    def to_dict(self) -> dict:
        return {
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "video_bitrate": self.video_bitrate,
            "audio_bitrate": self.audio_bitrate,
            "resolution": self.resolution,
            "framerate": self.framerate,
            "output_extension": self.output_extension,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TranscodeConfig:
        return cls(
            video_codec=data.get("video_codec", "libx264"),
            audio_codec=data.get("audio_codec", "aac"),
            video_bitrate=data.get("video_bitrate", ""),
            audio_bitrate=data.get("audio_bitrate", ""),
            resolution=data.get("resolution", ""),
            framerate=data.get("framerate", ""),
            output_extension=data.get("output_extension", ".mp4"),
        )


# ---------------------------------------------------------------------------
# Filter parameters
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FilterConfig:
    """FFmpeg filter parameters."""

    rotate: str = ""
    crop: str = ""
    watermark_path: str = ""
    watermark_position: str = "bottom-right"
    watermark_margin: int = 10
    volume: str = ""
    speed: str = ""

    def to_dict(self) -> dict:
        return {
            "rotate": self.rotate,
            "crop": self.crop,
            "watermark_path": self.watermark_path,
            "watermark_position": self.watermark_position,
            "watermark_margin": self.watermark_margin,
            "volume": self.volume,
            "speed": self.speed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> FilterConfig:
        return cls(
            rotate=data.get("rotate", ""),
            crop=data.get("crop", ""),
            watermark_path=data.get("watermark_path", ""),
            watermark_position=data.get("watermark_position", "bottom-right"),
            watermark_margin=data.get("watermark_margin", 10),
            volume=data.get("volume", ""),
            speed=data.get("speed", ""),
        )


# ---------------------------------------------------------------------------
# Task-level configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaskConfig:
    """Complete configuration for a single conversion task."""

    transcode: TranscodeConfig = field(default_factory=TranscodeConfig)
    filters: FilterConfig = field(default_factory=FilterConfig)
    output_dir: str = ""

    def to_dict(self) -> dict:
        return {
            "transcode": self.transcode.to_dict(),
            "filters": self.filters.to_dict(),
            "output_dir": self.output_dir,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TaskConfig:
        tc = data.get("transcode", {})
        fc = data.get("filters", {})
        return cls(
            transcode=TranscodeConfig.from_dict(tc),
            filters=FilterConfig.from_dict(fc),
            output_dir=data.get("output_dir", ""),
        )


# ---------------------------------------------------------------------------
# Task progress (immutable snapshot, created on each update)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaskProgress:
    """Progress info for a single conversion task (immutable snapshot)."""

    percent: float = 0.0
    current_seconds: float = 0.0
    total_seconds: float = 0.0
    speed: str = ""
    fps: str = ""
    frame: int = 0
    estimated_remaining: str = ""

    def to_dict(self) -> dict:
        return {
            "percent": self.percent,
            "current_seconds": self.current_seconds,
            "total_seconds": self.total_seconds,
            "speed": self.speed,
            "fps": self.fps,
            "frame": self.frame,
            "estimated_remaining": self.estimated_remaining,
        }


# ---------------------------------------------------------------------------
# Task entity (mutable -- state/progress/log_lines updated at runtime)
# ---------------------------------------------------------------------------


@dataclass
class Task:
    """A single conversion task with file info, config, and runtime state."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    file_path: str = ""
    file_name: str = ""
    file_size_bytes: int = 0
    duration_seconds: float = 0.0
    config: TaskConfig = field(default_factory=TaskConfig)
    state: TaskState = "pending"
    progress: TaskProgress = field(default_factory=TaskProgress)
    output_path: str = ""
    error: str = ""
    log_lines: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    started_at: str = ""
    completed_at: str = ""

    def can_transition(self, new_state: TaskState) -> bool:
        return new_state in VALID_TRANSITIONS.get(self.state, set())

    def transition(self, new_state: TaskState) -> str:
        """Transition to *new_state* and return the previous state.

        Raises ``ValueError`` if the transition is invalid per
        ``VALID_TRANSITIONS``.
        """
        if not self.can_transition(new_state):
            raise ValueError(
                f"Invalid transition: {self.state} -> {new_state}"
            )
        old_state = self.state
        self.state = new_state

        if new_state == "running" and not self.started_at:
            self.started_at = datetime.now().isoformat()

        if new_state in ("completed", "failed", "cancelled"):
            self.completed_at = datetime.now().isoformat()

        return old_state

    def update_progress(self, progress: TaskProgress) -> None:
        self.progress = progress

    def to_dict(self) -> dict:
        """Serialize to dict for JSON persistence and bridge transfer."""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size_bytes": self.file_size_bytes,
            "duration_seconds": self.duration_seconds,
            "config": self.config.to_dict(),
            "state": self.state,
            "progress": self.progress.to_dict(),
            "output_path": self.output_path,
            "error": self.error,
            "log_lines": self.log_lines[-100:],
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Deserialize from dict (JSON persistence / bridge transfer)."""
        pr = data.get("progress", {})

        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            file_path=data.get("file_path", ""),
            file_name=data.get("file_name", ""),
            file_size_bytes=data.get("file_size_bytes", 0),
            duration_seconds=data.get("duration_seconds", 0.0),
            config=TaskConfig.from_dict(data.get("config", {})),
            state=data.get("state", "pending"),
            progress=TaskProgress(
                percent=pr.get("percent", 0.0),
                current_seconds=pr.get("current_seconds", 0.0),
                total_seconds=pr.get("total_seconds", 0.0),
                speed=pr.get("speed", ""),
                fps=pr.get("fps", ""),
                frame=pr.get("frame", 0),
                estimated_remaining=pr.get("estimated_remaining", ""),
            ),
            output_path=data.get("output_path", ""),
            error=data.get("error", ""),
            log_lines=data.get("log_lines", []),
            created_at=data.get("created_at", ""),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at", ""),
        )


# ---------------------------------------------------------------------------
# Preset (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Preset:
    """An FFmpeg conversion preset with embedded TaskConfig."""

    id: str
    name: str
    description: str = ""
    config: TaskConfig = field(default_factory=TaskConfig)
    is_default: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict for bridge transfer and persistence."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "config": self.config.to_dict(),
            "is_default": self.is_default,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Preset:
        """Deserialize from dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            config=TaskConfig.from_dict(data.get("config", {})),
            is_default=data.get("is_default", False),
        )


# ---------------------------------------------------------------------------
# App settings (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AppSettings:
    """Application-level settings persisted to settings.json."""

    max_workers: int = 2
    default_output_dir: str = ""
    ffmpeg_path: str = ""
    ffprobe_path: str = ""

    def to_dict(self) -> dict:
        return {
            "max_workers": self.max_workers,
            "default_output_dir": self.default_output_dir,
            "ffmpeg_path": self.ffmpeg_path,
            "ffprobe_path": self.ffprobe_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AppSettings:
        return cls(
            max_workers=data.get("max_workers", 2),
            default_output_dir=data.get("default_output_dir", ""),
            ffmpeg_path=data.get("ffmpeg_path", ""),
            ffprobe_path=data.get("ffprobe_path", ""),
        )
