"""File metadata extraction via ffprobe."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from fractions import Fraction


def probe_file(file_path: str) -> dict:
    """Probe a media file with ffprobe and return a metadata dict.

    Falls back gracefully if ffprobe is unavailable -- returns a
    dict with only basic file system fields.
    """
    p = Path(file_path)
    name = p.name
    size_bytes = p.stat().st_size if p.exists() else 0

    ffprobe = __import__(
        "core.ffmpeg_setup", fromlist=["get_ffprobe_path"]
    ).get_ffprobe_path()
    if ffprobe is None:
        return {
            "file_path": file_path,
            "file_name": name,
            "file_size_bytes": size_bytes,
        }

    try:
        run_kw: dict = {
            "capture_output": True,
            "text": True,
            "timeout": 30,
            "encoding": "utf-8",
            "errors": "replace",
        }
        if sys.platform == "win32":
            run_kw["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            [
                ffprobe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path,
            ],
            **run_kw,
        )
        if result.returncode != 0:
            return {
                "file_path": file_path,
                "file_name": name,
                "file_size_bytes": size_bytes,
            }

        info = json.loads(result.stdout)
        return _parse_probe(file_path, name, size_bytes, info)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return {
            "file_path": file_path,
            "file_name": name,
            "file_size_bytes": size_bytes,
        }


def _parse_probe(
    file_path: str,
    name: str,
    size_bytes: int,
    info: dict,
) -> dict:
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

    return {
        "file_path": file_path,
        "file_name": name,
        "file_size_bytes": size_bytes,
        "duration_seconds": duration,
        "video_codec": video_codec,
        "audio_codec": audio_codec,
        "width": width,
        "height": height,
        "format_name": format_name,
    }


def _parse_fps(r_frame_rate: str) -> str:
    """Convert ffprobe r_frame_rate (e.g. '30/1', '24000/1001') to human-readable."""
    if not r_frame_rate or "/" not in r_frame_rate:
        return r_frame_rate or ""
    try:
        num, den = r_frame_rate.split("/")
        num, den = int(num), int(den)
        if den <= 0:
            return r_frame_rate
        fps = Fraction(num, den)
        return str(float(fps)) if fps.denominator != 1 else str(fps.numerator)
    except (ValueError, ZeroDivisionError):
        return r_frame_rate


def _extract_streams(info: dict) -> dict:
    """Extract video, audio, and subtitle streams from ffprobe JSON."""
    video: list[dict] = []
    audio: list[dict] = []
    subtitle: list[dict] = []

    for stream in info.get("streams", []):
        codec_type = stream.get("codec_type", "")

        if codec_type == "video":
            w = int(stream.get("width", 0))
            h = int(stream.get("height", 0))
            video.append({
                "codec_name": stream.get("codec_name", ""),
                "codec_long_name": stream.get("codec_long_name", ""),
                "width": w,
                "height": h,
                "resolution": f"{w}x{h}" if w and h else "",
                "bit_rate": stream.get("bit_rate", ""),
                "fps": _parse_fps(stream.get("r_frame_rate", "")),
                "pix_fmt": stream.get("pix_fmt", ""),
                "color_space": stream.get("color_space", ""),
                "color_range": stream.get("color_range", ""),
                "profile": stream.get("profile", ""),
                "level": int(stream.get("level", -1)),
                "sample_aspect_ratio": stream.get("sample_aspect_ratio", ""),
                "display_aspect_ratio": stream.get("display_aspect_ratio", ""),
                "field_order": stream.get("field_order", ""),
                "language": stream.get("tags", {}).get("language", ""),
                "index": int(stream.get("index", 0)),
            })
        elif codec_type == "audio":
            audio.append({
                "codec_name": stream.get("codec_name", ""),
                "codec_long_name": stream.get("codec_long_name", ""),
                "sample_rate": stream.get("sample_rate", ""),
                "channels": int(stream.get("channels", 0)),
                "channel_layout": stream.get("channel_layout", ""),
                "bit_rate": stream.get("bit_rate", ""),
                "language": stream.get("tags", {}).get("language", ""),
                "index": int(stream.get("index", 0)),
            })
        elif codec_type == "subtitle":
            subtitle.append({
                "codec_name": stream.get("codec_name", ""),
                "language": stream.get("tags", {}).get("language", ""),
                "index": int(stream.get("index", 0)),
            })

    return {"video": video, "audio": audio, "subtitle": subtitle}


def probe_media_full(file_path: str) -> dict:
    """Full ffprobe analysis returning both parsed and raw JSON data.

    Returns a dict with success/data/error structure suitable for
    direct use as an @expose API response.
    """
    p = Path(file_path)
    if not p.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    name = p.name
    size_bytes = p.stat().st_size

    ffprobe = __import__(
        "core.ffmpeg_setup", fromlist=["get_ffprobe_path"]
    ).get_ffprobe_path()
    if ffprobe is None:
        return {"success": False, "error": "ffprobe not available"}

    try:
        run_kw: dict = {
            "capture_output": True,
            "text": True,
            "timeout": 30,
            "encoding": "utf-8",
            "errors": "replace",
        }
        if sys.platform == "win32":
            run_kw["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            [
                ffprobe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path,
            ],
            **run_kw,
        )
        if result.returncode != 0:
            return {"success": False, "error": "ffprobe returned non-zero exit code"}

        info = json.loads(result.stdout)
        fmt = info.get("format", {})

        streams = _extract_streams(info)
        general = {
            "file_name": name,
            "file_path": file_path,
            "file_size_bytes": size_bytes,
            "duration_seconds": float(fmt.get("duration", 0)),
            "format_name": fmt.get("format_name", ""),
            "format_long_name": fmt.get("format_long_name", ""),
            "bit_rate": fmt.get("bit_rate", ""),
            "nb_streams": int(fmt.get("nb_streams", 0)),
            "probe_score": int(fmt.get("probe_score", 0)),
        }

        parsed = {
            "general": general,
            **streams,
        }
        raw = json.dumps(info, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "data": {
                "parsed": parsed,
                "raw": raw,
            },
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "ffprobe timed out (30s)"}
    except json.JSONDecodeError as exc:
        return {"success": False, "error": f"Failed to parse ffprobe output: {exc}"}
    except OSError as exc:
        return {"success": False, "error": str(exc)}
