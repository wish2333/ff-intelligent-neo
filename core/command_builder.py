"""Build FFmpeg command-line arguments from TaskConfig.

Supports transcode parameters, filter chains (crop, scale, rotate,
speed, watermark overlay, volume), and parameter validation with
priority-based automatic filter ordering.
"""

from __future__ import annotations

import os
import re
import shlex as _shlex
from dataclasses import dataclass
from pathlib import Path

from core.models import TaskConfig


# ---------------------------------------------------------------------------
# Path quoting helpers
# ---------------------------------------------------------------------------

def _subprocess_quote(path: str) -> str:
    """Quote a path for use in a subprocess argument list.

    On Windows, Python's subprocess uses ``list2cmdline`` internally when
    passed a list, so paths with spaces/Unicode do NOT need shell quoting.
    On Unix, the exec syscall receives each list element as a separate arg
    so quoting is also not needed.  In both cases, simply return the path
    as-is — ``shlex.quote`` would add unwanted single quotes on Windows.
    """
    return path


def _preview_quote(path: str) -> str:
    """Quote a path for display in the command preview string.

    The preview is a human-readable string, so we use ``shlex.quote`` to
    produce a shell-like representation.
    """
    return _subprocess_quote(path)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_VIDEO_CODECS = {
    "libx264", "libx265", "libsvtav1", "libvpx-vp9",
    "av1_nvenc", "hevc_nvenc", "h264_nvenc",
    "h264_amf", "hevc_amf", "h264_qsv", "hevc_qsv", "av1_qsv",
    "h264_videotoolbox", "hevc_videotoolbox",
    "copy", "none",
}
VALID_AUDIO_CODECS = {"aac", "opus", "flac", "libmp3lame", "alac", "copy", "none"}
VALID_OUTPUT_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".mp3", ".aac", ".flac", ".wav"
}
VALID_ROTATE_OPTIONS = {"", "none", "transpose=1", "transpose=2", "transpose=3"}
VALID_WATERMARK_POSITIONS = {"", "top-left", "top-right", "bottom-left", "bottom-right"}
VALID_PRESETS = {"ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"}
VALID_QUALITY_MODES = {"crf", "cq", "qp", "q"}
VALID_PIXEL_FORMATS = {"yuv420p", "yuv420p10le", "yuv422p", "yuv444p"}

# ---------------------------------------------------------------------------
# Validation context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationContext:
    """Extra context for parameter validation."""
    file_info: dict | None = None
    ffmpeg_version: str | None = None
    preview_mode: bool = False


# ---------------------------------------------------------------------------
# Transcode parameter registry
# ---------------------------------------------------------------------------

_TRANSPILE_PARAMS: dict[str, dict] = {}


def _register_transcode_param(
    key: str,
    build: callable,
    validate: callable,
) -> None:
    _TRANSPILE_PARAMS[key] = {"build": build, "validate": validate}


def _build_transcode_args(tc, ctx: ValidationContext) -> list[str]:
    args: list[str] = []
    for key, param in _TRANSPILE_PARAMS.items():
        val = getattr(tc, key, "")
        if val:
            args.extend(param["build"](val, tc, ctx))
    return args


def _validate_transcode(tc, ctx: ValidationContext) -> list[dict]:
    errors: list[dict] = []
    for key, param in _TRANSPILE_PARAMS.items():
        val = getattr(tc, key, "")
        issues = param["validate"](val, tc, ctx)
        for item in issues:
            if isinstance(item, dict):
                errors.append({"level": item["level"], "param": key, "message": item["message"]})
            else:
                errors.append({"level": item[0], "param": key, "message": item[1]})
    return errors


# ---------------------------------------------------------------------------
# Filter registry (priority-based ordering)
# ---------------------------------------------------------------------------

_FILTERS: dict[str, dict] = {}


def _register_filter(
    key: str,
    priority: int,
    build_vf: callable,
    build_af: callable,
    validate: callable,
    needs_complex: bool = False,
) -> None:
    _FILTERS[key] = {
        "priority": priority,
        "build_vf": build_vf,
        "build_af": build_af,
        "validate": validate,
        "needs_complex": needs_complex,
    }


def _build_filter_args(tc, fc, ctx: ValidationContext) -> tuple[list[str], list[str], list[str]]:
    """Build video and audio filter argument lists from active filters.

    Collects active filters from both FilterConfig fields and
    TranscodeConfig.resolution, sorts by priority, then returns:
      - vf_segments: list[str] for -vf or filter_complex
      - af_segments: list[str] for -af
      - extra_inputs: list[str] for extra -i (e.g. watermark)
    """
    active: list[tuple] = []
    for key, filt in _FILTERS.items():
        val = getattr(fc, key, "")
        if val and key != "watermark_path":
            active.append((filt["priority"], key, filt, val, fc))
    if tc.resolution:
        active.append((_FILTERS["resolution"]["priority"], "resolution", _FILTERS["resolution"], tc.resolution, fc))

    active.sort(key=lambda x: x[0])

    vf_segments: list[str] = []
    af_segments: list[str] = []
    extra_inputs: list[str] = []

    for _pri, _key, filt, val, _fc in active:
        vf_result = filt["build_vf"](val, _fc, ctx)
        if vf_result:
            vf_segments.extend(vf_result)
        af_result = filt["build_af"](val, _fc, ctx)
        if af_result:
            af_segments.extend(af_result)

    if fc.watermark_path:
        extra_inputs.extend(["-i", _subprocess_quote(fc.watermark_path)])

    return vf_segments, af_segments, extra_inputs


def _validate_filters(fc, ctx: ValidationContext) -> list[dict]:
    errors: list[dict] = []
    for key, filt in _FILTERS.items():
        val = getattr(fc, key, "")
        if val:
            issues = filt["validate"](val, fc, ctx)
            for item in issues:
                if isinstance(item, dict):
                    errors.append({"level": item["level"], "param": key, "message": item["message"]})
                else:
                    # Tuple format: (level, message)
                    errors.append({"level": item[0], "param": key, "message": item[1]})
    return errors


# ---------------------------------------------------------------------------
# Register built-in transcode parameters
# ---------------------------------------------------------------------------

_register_transcode_param(
    "video_codec",
    build=lambda val, tc, ctx: (
        ["-vn"] if val == "none"
        else ["-c:v", val] if val == "copy"
        else ["-c:v", val]
    ),
    validate=lambda val, tc, ctx: (
        [{"level": "error", "message": f"Invalid video codec: {val}"}]
        if val and val.lower() not in VALID_VIDEO_CODECS
        else []
    ),
)

_register_transcode_param(
    "video_bitrate",
    build=lambda val, tc, ctx: (
        ["-b:v", val]
        if val and tc.video_codec not in ("copy", "none")
        else []
    ),
    validate=lambda val, tc, ctx: (
        [{"level": "error", "message": f"Invalid video bitrate format: {val}"}]
        if val and not re.match(r"^\d+[kKMGT]?$", val)
        else []
    ),
)

_register_transcode_param(
    "audio_codec",
    build=lambda val, tc, ctx: (
        ["-an"] if val == "none"
        else ["-c:a", val] if val == "copy"
        else ["-c:a", val]
    ),
    validate=lambda val, tc, ctx: (
        [{"level": "error", "message": f"Invalid audio codec: {val}"}]
        if val and val.lower() not in VALID_AUDIO_CODECS
        else []
    ),
)

_register_transcode_param(
    "audio_bitrate",
    build=lambda val, tc, ctx: (
        ["-b:a", val]
        if val and tc.audio_codec not in ("copy", "none")
        else []
    ),
    validate=lambda val, tc, ctx: (
        [{"level": "error", "message": f"Invalid audio bitrate format: {val}"}]
        if val and not re.match(r"^\d+[kKMGT]?$", val)
        else []
    ),
)

_register_transcode_param(
    "framerate",
    build=lambda val, tc, ctx: (
        ["-r", val]
        if val and tc.video_codec not in ("copy", "none")
        else []
    ),
    validate=lambda val, tc, ctx: (
        [{"level": "warning", "message": "Framerate is ignored when video codec is copy"}]
        if val and tc.video_codec == "copy"
        else []
    ),
)

# Phase 3.5: quality_mode -> -crf / -cq / -qp / -q:v
_QUALITY_FLAG_MAP = {"crf": "-crf", "cq": "-cq", "qp": "-qp", "q": "-q:v"}

_register_transcode_param(
    "quality_mode",
    build=lambda val, tc, ctx: (
        [
            _QUALITY_FLAG_MAP.get(val, f"-{val}"), str(tc.quality_value),
        ]
        if val and tc.quality_value > 0 and tc.video_codec not in ("copy", "none")
        else []
    ),
    validate=lambda val, tc, ctx: (
        [{"level": "error", "message": f"Invalid quality mode: {val} (expected crf, cq, or qp)"}]
        if val and val not in VALID_QUALITY_MODES
        else (
            [{"level": "warning", "message": f"Quality value out of range (0-{51 if val != 'q' else 100}): {tc.quality_value}"}]
            if val and (tc.quality_value < 0 or tc.quality_value > (51 if val != 'q' else 100))
            else []
        )
    ),
)

# Phase 3.5: preset -> -preset
_register_transcode_param(
    "preset",
    build=lambda val, tc, ctx: (
        ["-preset", val]
        if val and tc.video_codec not in ("copy", "none")
        else []
    ),
    validate=lambda val, tc, ctx: (
        [{"level": "error", "message": f"Invalid preset: {val}"}]
        if val and val not in VALID_PRESETS
        else []
    ),
)

# Phase 3.5: pixel_format -> -pix_fmt
_register_transcode_param(
    "pixel_format",
    build=lambda val, tc, ctx: (
        ["-pix_fmt", val]
        if val and tc.video_codec not in ("copy", "none")
        else []
    ),
    validate=lambda val, tc, ctx: (
        [{"level": "error", "message": f"Invalid pixel format: {val}"}]
        if val and val not in VALID_PIXEL_FORMATS
        else []
    ),
)

# Phase 3.5: max_bitrate -> -maxrate + -bufsize
_register_transcode_param(
    "max_bitrate",
    build=lambda val, tc, ctx: (
        ["-maxrate", val, "-bufsize", tc.bufsize]
        if val and tc.bufsize and tc.video_codec not in ("copy", "none")
        else ["-maxrate", val, "-bufsize", "2M"]
        if val and tc.video_codec not in ("copy", "none")
        else []
    ),
    validate=lambda val, tc, ctx: (
        [{"level": "error", "message": f"Invalid max bitrate format: {val}"}]
        if val and not re.match(r"^\d+[kKMGT]?$", val)
        else []
    ),
)


# ---------------------------------------------------------------------------
# Register built-in filters
# ---------------------------------------------------------------------------

# crop (priority 5)
_register_filter(
    "crop",
    priority=5,
    build_vf=lambda val, fc, ctx: [f"crop={val}"],
    build_af=lambda val, fc, ctx: [],
    validate=lambda val, fc, ctx: (
        [{"level": "error", "message": f"Invalid crop format (expected W:H:X:Y): {val}"}]
        if val and not re.match(r"^\d+:\d+:\d+:\d+$", val)
        else []
    ),
)

# scale (priority 20) -- uses resolution from transcode
_register_filter(
    "resolution",
    priority=20,
    build_vf=lambda val, fc, ctx: (
        [f"scale={val.replace('x', ':')}"]
        if val and re.match(r"^\d+x\d+$", val)
        else []
    ),
    build_af=lambda val, fc, ctx: [],
    needs_complex=False,
    validate=lambda val, fc, ctx: (
        [{"level": "error", "message": f"Invalid resolution format (expected WxH): {val}"}]
        if val and not re.match(r"^\d+x\d+$", val)
        else []
    ),
)

# rotate (priority 30)
_register_filter(
    "rotate",
    priority=30,
    build_vf=lambda val, fc, ctx: (
        [val]
        if val and val.startswith("transpose=")
        else []
    ),
    build_af=lambda val, fc, ctx: [],
    validate=lambda val, fc, ctx: (
        [{"level": "error", "message": f"Invalid rotate option: {val}"}]
        if val and val not in VALID_ROTATE_OPTIONS
        else []
    ),
)

# speed (priority 40)
_REGISTERED_FILTERS_SPEED = _register_filter(
    "speed",
    priority=40,
    build_vf=lambda val, fc, ctx: (
        [f"setpts={1.0 / float(val):.4f}*PTS"]
        if val
        else []
    ),
    build_af=lambda val, fc, ctx: (
        _build_atempo_chain(val)
        if val
        else []
    ),
    needs_complex=False,
    validate=lambda val, fc, ctx: (
        (
            [{"level": "error", "message": "Speed must be a positive number"}]
            if not _is_valid_number(val)
            else (
                [{"level": "error", "message": "Speed must be between 0.25 and 4"}]
                if float(val) < 0.25 or float(val) > 4
                else (
                    [{"level": "warning", "message": "Speed < 0.5 or > 2.0 may cause audio-video desync"}]
                    if float(val) < 0.5 or float(val) > 2.0
                    else []
                )
            )
        )
        if val
        else []
    ),
)

# overlay/watermark (priority 50)
_REGISTERED_FILTERS_OVERLAY = _register_filter(
    "watermark_path",
    priority=50,
    build_vf=lambda val, fc, ctx: (
        _build_overlay_expr(fc.watermark_position, fc.watermark_margin)
        if val
        else []
    ),
    build_af=lambda val, fc, ctx: [],
    needs_complex=True,
    validate=lambda val, fc, ctx: (
        []
        if ctx.preview_mode
        else (
            (
                [{"level": "error", "message": f"Watermark file not found: {val}"}]
                if not Path(val).exists()
                else (
                    [{"level": "error", "message": "Watermark must be an image file (png, jpg, bmp)"}]
                    if Path(val).suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}
                    else []
                )
            )
            if val
            else []
        )
    ),
)

# volume (priority 15) -- before speed in audio chain
_REGISTERED_FILTERS_VOLUME = _register_filter(
    "volume",
    priority=15,
    build_vf=lambda val, fc, ctx: [],
    build_af=lambda val, fc, ctx: (
        [f"volume={val}"]
        if val and _is_valid_number(val)
        else []
    ),
    needs_complex=False,
    validate=lambda val, fc, ctx: (
        (
            [{"level": "warning", "message": "Volume adjustment is ignored when audio codec is copy"}]
            if fc and getattr(fc, "audio_codec", "") == "copy"  # will check via context
            else (
                [{"level": "error", "message": "Volume must be a valid number"}]
                if not _is_valid_number(val)
                else []
            )
        )
        if val
        else []
    ),
)

# audio_normalize (priority 16) -- EBU R128 loudnorm
_REGISTERED_FILTERS_LOUDNORM = _register_filter(
    "audio_normalize",
    priority=16,
    build_vf=lambda val, fc, ctx: [],
    build_af=lambda val, fc, ctx: (
        [f"loudnorm=I={fc.target_loudness}:TP={fc.true_peak}:LRA={fc.lra}"]
        if val
        else []
    ),
    needs_complex=False,
    validate=lambda val, fc, ctx: (
        (
            [{"level": "warning", "message": "Audio normalization is ignored when audio codec is copy"}]
            if getattr(fc, "audio_codec", "") == "copy"
            else []
        )
        if val
        else []
    ),
)

# aspect_convert (priority 35) -- H2V/V2H conversion
_VALID_ASPECT_MODES = {"H2V-I", "H2V-T", "H2V-B", "V2H-I", "V2H-T", "V2H-B"}
_REGISTERED_FILTERS_ASPECT = _register_filter(
    "aspect_convert",
    priority=35,
    build_vf=lambda val, fc, ctx: [],
    build_af=lambda val, fc, ctx: [],
    needs_complex=True,
    validate=lambda val, fc, ctx: (
        [{"level": "error", "message": f"Invalid aspect convert mode: {val}"}]
        if val and val not in _VALID_ASPECT_MODES
        else (
            [{"level": "error", "message": "H2V-I and V2H-I modes require a background image"}]
            if val in ("H2V-I", "V2H-I") and not fc.bg_image_path
            else []
        )
    ),
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _is_valid_number(val: str) -> bool:
    """Check if string represents a valid positive number."""
    try:
        return float(val) > 0
    except (ValueError, TypeError):
        return False


def _build_atempo_chain(speed_str: str) -> list[str]:
    """Build atempo filter chain for speed adjustment.

    FFmpeg atempo supports 0.5-100.0 range per filter instance.
    For values outside this range, chain multiple atempo filters.
    """
    speed = float(speed_str)
    if speed == 1.0:
        return []

    filters: list[str] = []
    remaining = speed
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    while remaining > 100.0:
        filters.append("atempo=100.0")
        remaining /= 100.0
    filters.append(f"atempo={remaining:.4f}")
    return filters


def _build_overlay_expr(position: str, margin: int) -> list[str]:
    """Build overlay position expression for watermark.

    Returns the overlay filter string (without input labels).
    """
    exprs = {
        "top-left": f"overlay={margin}:{margin}",
        "top-right": f"overlay=main_w-overlay_w-{margin}:{margin}",
        "bottom-left": f"overlay={margin}:main_h-overlay_h-{margin}",
        "bottom-right": f"overlay=main_w-overlay_w-{margin}:main_h-overlay_h-{margin}",
    }
    return [exprs.get(position, exprs["bottom-right"])]


def _convert_time_to_ffmpeg(time_str: str) -> str:
    """Convert UI time format (H:mm:ss.fff) to FFmpeg format (HH:MM:SS.mmm).

    Replaces the 8th character (colon before ms) with a period.
    Input:  "0:01:30:500" -> Output: "0:01:30.500"
    """
    if not time_str or len(time_str) < 9:
        return time_str
    return time_str[:7] + "." + time_str[8:]


def _parse_time_to_seconds(time_str: str) -> float:
    """Parse UI time format (H:mm:ss.fff) to total seconds."""
    if not time_str:
        return 0.0
    parts = time_str.split(":")
    try:
        h = int(parts[0]) if len(parts) > 0 else 0
        m = int(parts[1]) if len(parts) > 1 else 0
        s = float(parts[2]) if len(parts) > 2 else 0.0
        ms = int(parts[3]) if len(parts) > 3 else 0
        return h * 3600 + m * 60 + s + ms / 1000.0
    except (ValueError, IndexError):
        return 0.0


def _build_aspect_convert_filter(
    mode: str,
    target_resolution: str,
    bg_image_path: str = "",
) -> tuple[list[str], list[str]]:
    """Build filter_complex expression for aspect ratio conversion.

    Returns (filter_complex_args, extra_inputs).
    """
    if not target_resolution:
        return [], []

    w, h = target_resolution.split("x")
    extra_inputs: list[str] = []

    if mode == "H2V-I":
        extra_inputs = ["-i", _subprocess_quote(bg_image_path)]
        expr = (
            f"[1:v]scale={w}:{h},setsar=1,loop=-1:size=2147483647[bg];"
            f"[0:v]scale={w}:-2,setsar=1[v];"
            f"[bg][v]overlay=(W-w)/2:(H-h)/2:shortest=1[vout]"
        )
    elif mode == "H2V-T":
        ratio = int(w) / int(h)
        expr = (
            f"[0:v]split=2[v_main][v_bg];"
            f"[v_main]scale={w}:-2,setsar=1,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black@0[v_scaled];"
            f"[v_bg]crop=ih*{ratio:.6f}:ih,boxblur=10:5,scale={w}:{h}[bg_blurred];"
            f"[bg_blurred][v_scaled]overlay=(W-w)/2:(H-h)/2:shortest=1[vout]"
        )
    elif mode == "H2V-B":
        expr = (
            f"[0:v]scale={w}:-2,setsar=1,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black[vout]"
        )
    elif mode == "V2H-I":
        extra_inputs = ["-i", _subprocess_quote(bg_image_path)]
        expr = (
            f"[1:v]scale={w}:{h},setsar=1,loop=-1:size=2147483647[bg];"
            f"[0:v]scale=-2:{h},setsar=1[v];"
            f"[bg][v]overlay=(W-w)/2:(H-h)/2:shortest=1[vout]"
        )
    elif mode == "V2H-T":
        ratio = int(h) / int(w)
        expr = (
            f"[0:v]split=2[v_main][v_bg];"
            f"[v_main]scale=-1:{h},setsar=1,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black@0[v_scaled];"
            f"[v_bg]crop=iw:iw*{ratio:.6f},boxblur=10:5,scale={w}:{h}[bg_blurred];"
            f"[bg_blurred][v_scaled]overlay=(W-w)/2:(H-h)/2:shortest=1[vout]"
        )
    elif mode == "V2H-B":
        expr = (
            f"[0:v]scale=-1:{h},setsar=1,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black[vout]"
        )
    else:
        return [], []

    return [f"-filter_complex", expr, "-map", "[vout]", "-map", "0:a"], extra_inputs


# ---------------------------------------------------------------------------
# Mode-specific command builders
# ---------------------------------------------------------------------------


def build_clip_command(
    config: TaskConfig,
    input_path: str,
    output_path: str,
    file_duration: float = 0.0,
) -> list[str]:
    """Build FFmpeg command for video clipping (extract/cut modes).

    Args:
        config: Task configuration (uses clip sub-config).
        input_path: Source media file.
        output_path: Destination file.
        file_duration: Total file duration in seconds (needed for extract mode).
    """
    clip = config.clip
    if not clip:
        return build_command(config, input_path, output_path)

    start = _convert_time_to_ffmpeg(clip.start_time)

    # Calculate end time
    if clip.clip_mode == "extract":
        end_seconds = file_duration - _parse_time_to_seconds(clip.end_time_or_duration)
        h = int(end_seconds // 3600)
        m = int((end_seconds % 3600) // 60)
        s = end_seconds % 60
        end = f"{h}:{m:02d}:{s:06.3f}"
    else:
        end = _convert_time_to_ffmpeg(clip.end_time_or_duration)

    # -hide_banner -y added by runner
    args = ["-ss", start, "-to", end, "-accurate_seek", "-i", _subprocess_quote(input_path)]

    if clip.use_copy_codec:
        args.extend(["-c", "copy"])
    else:
        # Use transcode config
        tc = config.transcode
        if tc.video_codec and tc.video_codec not in ("copy", "none"):
            args.extend(["-c:v", tc.video_codec])
        if tc.audio_codec and tc.audio_codec not in ("copy", "none"):
            args.extend(["-c:a", tc.audio_codec])

    args.extend([_subprocess_quote(output_path)])
    return args


def build_merge_command(
    config: TaskConfig,
    output_path: str,
) -> list[str]:
    """Build FFmpeg command for multi-video concatenation.

    Args:
        config: Task configuration (uses merge sub-config).
        output_path: Destination file.
    """
    merge = config.merge
    if not merge or len(merge.file_list) < 2:
        return []

    files = list(merge.file_list)

    if merge.merge_mode in ("concat_protocol", "ts_concat"):
        # Concat demuxer: reads a temp list file with same-codec segments.
        # The task_runner creates the list file at runtime (replacing "list.txt"
        # with the actual temp path).  Both concat_protocol and ts_concat use
        # this approach because the concat: URL protocol does NOT support MP4
        # (it only works for elementary streams like .ts).
        return [
            # flags added by runner
            "-f", "concat", "-safe", "0",
            "-i", "list.txt",
            "-c", "copy",
            _subprocess_quote(output_path),
        ]

    # filter_complex mode: normalize then concatenate
    n = len(files)
    tc = config.transcode
    res = merge.target_resolution.replace("x", ":") if merge.target_resolution else "1920:1080"
    fps = merge.target_fps if merge.target_fps > 0 else 30

    # Normalize video: fps, scale, setsar (always include)
    v_chain = f"fps={fps},scale={res},setsar=1"

    # Build filter_complex with interleaved video/audio inputs for concat
    # concat filter with n=3:v=1:a=1 expects: [v0][a0][v1][a1][v2][a2]concat=... [vout][aout]
    filter_parts = []
    concat_inputs: list[str] = []
    for i in range(n):
        filter_parts.append(f"[{i}:v]{v_chain}[v{i}]")
        filter_parts.append(f"[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}]")
        concat_inputs.append(f"[v{i}]")
        concat_inputs.append(f"[a{i}]")

    # Single concat filter with interleaved video+audio inputs
    filter_parts.append(
        f"{''.join(concat_inputs)}concat=n={n}:v=1:a=1[vout][aout]"
    )

    filter_str = ";".join(filter_parts)

    args = ["-hide_banner", "-y"]
    for f in files:
        args.extend(["-i", _subprocess_quote(f)])

    args.extend(["-filter_complex", filter_str])
    args.extend(["-map", "[vout]", "-map", "[aout]"])

    if tc.video_codec and tc.video_codec not in ("copy", "none"):
        args.extend(["-c:v", tc.video_codec])
    if tc.audio_codec and tc.audio_codec not in ("copy", "none"):
        args.extend(["-c:a", tc.audio_codec])

    args.extend([_subprocess_quote(output_path)])
    return args


def build_avsmix_command(
    config: TaskConfig,
    input_path: str,
    output_path: str,
) -> list[str]:
    """Build FFmpeg command with external audio and subtitle mixing.

    Args:
        config: Task configuration (uses avsmix sub-config + transcode/filters).
        input_path: Source video file.
        output_path: Destination file.
    """
    avsmix = config.avsmix
    if not avsmix:
        return build_command(config, input_path, output_path)

    # Build base transcode + filter command
    base = build_command(config, input_path, output_path)

    # Insert extra inputs before output, add map directives
    extra_inputs: list[str] = []
    map_directives: list[str] = []

    if avsmix.external_audio_path:
        extra_inputs.extend(["-i", avsmix.external_audio_path])
        if avsmix.replace_audio:
            map_directives.extend(["-map", "0:v", "-map", "1:a"])

    if avsmix.subtitle_path:
        extra_inputs.extend(["-i", avsmix.subtitle_path])
        map_directives.extend(["-map", "2:s", "-c:s", "mov_text"])
        if avsmix.subtitle_language:
            map_directives.extend(["-metadata:s:s:0", f"language={avsmix.subtitle_language}"])

    # Insert before "-y output_path" at the end
    if not extra_inputs:
        return base

    # Rebuild: args up to transcode, add extra inputs, add filters, add maps, add output
    # The base command structure is: [global_opts, -i input, extra_inputs, transcode, filters, -y output]
    result = list(base)
    # Find the "-y" before output and insert extra_inputs + maps there
    # Simple approach: remove last 2 items (-y, output), insert, then re-add
    result = result[:-2]

    result.extend(extra_inputs)
    result.extend(map_directives)
    result.extend(["-y", output_path])

    return result


def build_merge_intro_outro_command(
    config: TaskConfig,
    content_file: str,
    output_path: str,
) -> list[str]:
    """Build FFmpeg command for intro/outro concatenation with a single content file.

    Uses filter_complex to normalize all inputs and concat them.
    Input order: [intro], content, [outro].

    Args:
        config: Task configuration (uses merge sub-config for intro/outro paths and settings).
        content_file: The content video file to wrap with intro/outro.
        output_path: Destination file.
    """
    merge = config.merge
    if not merge:
        return build_command(config, content_file, output_path)

    intro = merge.intro_path
    outro = merge.outro_path
    tc = config.transcode
    res = merge.target_resolution.replace("x", ":") if merge.target_resolution else "1920:1080"
    fps = merge.target_fps if merge.target_fps > 0 else 30

    # Determine inputs
    inputs: list[str] = []
    if intro:
        inputs.append(intro)
    inputs.append(content_file)
    if outro:
        inputs.append(outro)

    n = len(inputs)

    # Build filter_complex with interleaved video/audio inputs for concat
    # concat filter expects: [v0][a0][v1][a1]...concat=n=N:v=1:a=1[vout][aout]
    filter_parts: list[str] = []
    concat_inputs: list[str] = []

    for i in range(n):
        filter_parts.append(f"[{i}:v]fps={fps},scale={res},setsar=1[v{i}]")
        filter_parts.append(f"[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}]")
        concat_inputs.append(f"[v{i}]")
        concat_inputs.append(f"[a{i}]")

    filter_parts.append(
        f"{''.join(concat_inputs)}concat=n={n}:v=1:a=1[vout][aout]"
    )

    filter_str = ";".join(filter_parts)

    args = ["-hide_banner", "-y"]
    for f in inputs:
        args.extend(["-i", _subprocess_quote(f)])

    args.extend(["-filter_complex", filter_str])
    args.extend(["-map", "[vout]", "-map", "[aout]"])

    if tc.video_codec and tc.video_codec not in ("copy", "none"):
        args.extend(["-c:v", tc.video_codec])
    if tc.audio_codec and tc.audio_codec not in ("copy", "none"):
        args.extend(["-c:a", tc.audio_codec])

    args.extend([_subprocess_quote(output_path)])
    return args


def build_custom_command(
    config: TaskConfig,
    input_path: str,
    output_path: str,
) -> list[str]:
    """Build FFmpeg command from raw user-provided arguments.

    Args:
        config: Task configuration (uses custom_command sub-config).
        input_path: Source media file path.
        output_path: Destination file path.
    """
    cc = config.custom_command
    if not cc:
        return build_command(config, input_path, output_path)

    # -hide_banner -y added by runner
    args = ["-i", _subprocess_quote(input_path)]
    if cc.raw_args.strip():
        args.extend(_shlex.split(cc.raw_args.strip()))
    args.extend(["-y", _subprocess_quote(output_path)])
    return args


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------


def build_command(
    config: TaskConfig,
    input_path: str,
    output_path: str,
) -> list[str]:
    """Build the full FFmpeg argument list (without the binary name).

    Both preview and execution call this same function, guaranteeing
    the displayed command is always exactly what gets executed.
    Dispatches to mode-specific builders when sub-configs are active.

    Args:
        config: Task configuration containing transcode and filter params.
        input_path: Source media file path.
        output_path: Destination file path.

    Returns:
        List of arguments to pass to subprocess.Popen.
    """
    # Dispatch to mode-specific builders
    # Phase 3.5: custom command checked first
    if config.custom_command:
        return build_custom_command(config, input_path, output_path)
    # Phase 3.5: only dispatch clip when inputs are filled
    if config.clip and (config.clip.start_time or config.clip.end_time_or_duration):
        return build_clip_command(config, input_path, output_path)
    # Phase 3.5.2: intro/outro takes a single content file and wraps it
    if config.merge and (config.merge.intro_path or config.merge.outro_path):
        return build_merge_intro_outro_command(config, input_path, output_path)
    if config.merge and len(config.merge.file_list) >= 2:
        return build_merge_command(config, output_path)

    tc = config.transcode
    fc = config.filters
    ctx = ValidationContext()

    # --- transcode args (built from registry for consistency) ---
    transcode_args = _build_transcode_args(tc, ctx)

    # --- aspect_convert: uses its own filter_complex ---
    if fc.aspect_convert:
        aspect_args, aspect_inputs = _build_aspect_convert_filter(
            fc.aspect_convert, fc.target_resolution, fc.bg_image_path,
        )
        args = ["-i", _subprocess_quote(input_path)]
        args.extend(aspect_inputs)
        args.extend(transcode_args)
        args.extend(aspect_args)
        args.extend(["-y", _subprocess_quote(output_path)])
        return args

    # --- filter chain ---
    has_filters = any([
        fc.rotate,
        fc.crop,
        fc.watermark_path,
        fc.volume,
        fc.speed,
        tc.resolution,
        fc.audio_normalize,
    ])

    filter_args: list[str] = []
    extra_inputs: list[str] = []

    vcodec = tc.video_codec.lower()
    if has_filters and vcodec not in ("copy", "none"):
        vf_segments, af_segments, extra_inputs = _build_filter_args(tc, fc, ctx)

        if fc.watermark_path:
            overlay_expr = _build_overlay_expr(fc.watermark_position, fc.watermark_margin)[0]
            video_chain = ",".join(vf_segments)
            if video_chain:
                filter_args.extend(["-filter_complex",
                    f"[0:v]{video_chain}[tmp];[tmp][1:v]{overlay_expr}"])
            else:
                filter_args.extend(["-filter_complex",
                    f"[0:v][1:v]{overlay_expr}"])
        else:
            if vf_segments:
                filter_args.extend(["-vf", ",".join(vf_segments)])

        if af_segments:
            filter_args.extend(["-af", ",".join(af_segments)])

    # --- avsmix: inject extra inputs and map directives ---
    if config.avsmix:
        avsmix = config.avsmix
        avsmix_inputs: list[str] = []
        map_directives: list[str] = []

        if avsmix.external_audio_path:
            avsmix_inputs.extend(["-i", _subprocess_quote(avsmix.external_audio_path)])
            if avsmix.replace_audio:
                map_directives.extend(["-map", "0:v", "-map", "1:a"])

        if avsmix.subtitle_path:
            avsmix_inputs.extend(["-i", _subprocess_quote(avsmix.subtitle_path)])
            map_directives.extend(["-map", "2:s", "-c:s", "mov_text"])
            if avsmix.subtitle_language:
                map_directives.extend(["-metadata:s:s:0", f"language={avsmix.subtitle_language}"])

        args = ["-i", _subprocess_quote(input_path)]
        args.extend(extra_inputs)
        args.extend(avsmix_inputs)
        args.extend(transcode_args)
        args.extend(filter_args)
        args.extend(map_directives)
        args.extend(["-y", _subprocess_quote(output_path)])
        return args

    # --- assemble: input, extra inputs, transcode, filters, output ---
    args = ["-i", _subprocess_quote(input_path)]
    args.extend(extra_inputs)
    args.extend(transcode_args)
    args.extend(filter_args)
    args.extend(["-y", _subprocess_quote(output_path)])

    return args


def build_command_preview(config: TaskConfig) -> str:
    """Build a human-readable FFmpeg command string for preview.

    Uses placeholder 'input.mp4' for the input and derives the
    output filename from the configured extension.
    For merge mode, uses placeholder file list.
    For custom command mode, uses the raw args directly.
    For intro/outro mode, uses the first content file as placeholder.
    """
    ext = config.transcode.output_extension or ".mp4"

    # Custom command mode
    if config.custom_command:
        args = build_custom_command(config, "input.mp4", f"output{ext}")
        return "ffmpeg " + " ".join(args)

    # Merge with intro/outro
    if config.merge and (config.merge.intro_path or config.merge.outro_path):
        # Preview intro/outro even without file_list (use placeholder)
        if len(config.merge.file_list) >= 2:
            first_file = config.merge.file_list[0]
        else:
            first_file = "content_video.mp4"
        args = build_merge_intro_outro_command(config, first_file, f"output{ext}")
        return "ffmpeg " + " ".join(args)
    if config.merge and len(config.merge.file_list) >= 2:
        args = build_merge_command(config, f"output{ext}")
        return "ffmpeg " + " ".join(args)
    # Merge config without files and without intro/outro - return empty
    # (frontend shows reference commands instead)
    if config.merge:
        return ""

    args = build_command(config, "input.mp4", f"output{ext}")
    return "ffmpeg " + " ".join(args)


def validate_config(
    config: TaskConfig,
    ctx: ValidationContext | None = None,
) -> dict:
    """Validate all config parameters.

    Returns:
        dict with 'errors' and 'warnings' lists.
    """
    if ctx is None:
        ctx = ValidationContext()

    issues: list[dict] = []

    # Validate transcode params
    issues.extend(_validate_transcode(config.transcode, ctx))

    # Validate filter params
    issues.extend(_validate_filters(config.filters, ctx))

    # Validate resolution (lives on transcode but uses filter-style validation)
    tc = config.transcode
    if tc.resolution and not re.match(r"^\d+x\d+$", tc.resolution):
        issues.append({
            "level": "error",
            "param": "resolution",
            "message": f"Invalid resolution format (expected WxH): {tc.resolution}",
        })

    # Cross-field warnings
    fc = config.filters

    has_filters = any([fc.rotate, fc.crop, fc.watermark_path, fc.volume, fc.speed, fc.audio_normalize])

    # audio_normalize and volume are mutually exclusive
    if fc.audio_normalize and fc.volume:
        issues.append({
            "level": "warning",
            "param": "audio_normalize",
            "message": "Audio normalization is enabled, volume adjustment will be ignored.",
        })

    # aspect_convert is mutually exclusive with crop/rotate/watermark
    if fc.aspect_convert:
        if fc.crop:
            issues.append({
                "level": "error",
                "param": "aspect_convert",
                "message": "Aspect conversion is mutually exclusive with crop.",
            })
        if fc.rotate:
            issues.append({
                "level": "error",
                "param": "aspect_convert",
                "message": "Aspect conversion is mutually exclusive with rotate.",
            })
        if fc.watermark_path:
            issues.append({
                "level": "error",
                "param": "aspect_convert",
                "message": "Aspect conversion is mutually exclusive with watermark.",
            })

    if tc.video_codec == "copy" and has_filters:
        issues.append({
            "level": "warning",
            "param": "video_codec",
            "message": "Video codec is 'copy' but filters are set. Filters require re-encoding.",
        })

    if tc.audio_codec == "copy" and fc.volume:
        issues.append({
            "level": "warning",
            "param": "audio_codec",
            "message": "Audio codec is 'copy' but volume is set. Volume adjustment requires re-encoding.",
        })

    if tc.audio_codec == "copy" and fc.audio_normalize:
        issues.append({
            "level": "warning",
            "param": "audio_codec",
            "message": "Audio codec is 'copy' but audio normalization is set. Normalization requires re-encoding.",
        })

    # Validate clip config (only when clip is provided with inputs filled)
    if config.clip and (config.clip.start_time or config.clip.end_time_or_duration):
        clip = config.clip
        if not clip.start_time:
            issues.append({
                "level": "error",
                "param": "start_time",
                "message": "Clip start time is required.",
            })
        if not clip.end_time_or_duration:
            issues.append({
                "level": "error",
                "param": "end_time_or_duration",
                "message": "Clip end time or duration is required.",
            })

    # Validate merge config
    if config.merge:
        merge = config.merge
        # Only require 2+ files when not in preview mode (config page doesn't upload files)
        # and no intro/outro is set (intro/outro can be used standalone)
        if (not ctx.preview_mode
                and not merge.intro_path and not merge.outro_path
                and len(merge.file_list) < 2):
            issues.append({
                "level": "error",
                "param": "file_list",
                "message": "At least 2 files are required for merge.",
            })
        if merge.merge_mode == "filter_complex" and not merge.target_resolution:
            issues.append({
                "level": "warning",
                "param": "target_resolution",
                "message": "filter_complex mode without target resolution may produce inconsistent output.",
            })

    # Validate avsmix config
    if config.avsmix:
        avsmix = config.avsmix
        if avsmix.subtitle_path and not avsmix.subtitle_language:
            issues.append({
                "level": "warning",
                "param": "subtitle_language",
                "message": "Subtitle language code is recommended for proper playback.",
            })

    errors = [{"param": i.get("param", ""), "message": i["message"]} for i in issues if i["level"] == "error"]
    warnings = [{"param": i.get("param", ""), "message": i["message"]} for i in issues if i["level"] == "warning"]

    return {"errors": errors, "warnings": warnings}


def build_output_path(
    input_path: str,
    config: TaskConfig,
    output_dir: str = "",
    timestamp: str = "",
) -> str:
    """Compute the output file path for a given input.

    If *output_dir* is empty the output goes next to the source file.
    When outputting to the source directory, a *timestamp* suffix is
    appended to the stem to avoid overwriting the original file.

    Args:
        input_path: Source file path.
        config: Task configuration (reads output_extension).
        output_dir: Override directory (empty = same as source).
        timestamp: Timestamp string in YYYYMMDD_HHMMSS format.

    Returns:
        Full output path string.
    """
    from datetime import datetime

    src = Path(input_path)
    ext = config.transcode.output_extension or src.suffix

    same_dir = not output_dir
    if same_dir and not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Sanitize stem to strip any path separators (prevent traversal)
    stem = Path(src.stem).name
    if same_dir:
        filename = f"{stem}-{timestamp}{ext}"
    else:
        filename = f"{stem}{ext}"

    if output_dir:
        result = Path(output_dir).resolve() / filename
        parent = Path(output_dir).resolve()
        if not str(result).startswith(str(parent) + ("" if str(parent).endswith(os.sep) else os.sep)):
            raise ValueError(f"Output path escapes target directory: {result}")
        return str(result)
    return str(src.parent / filename)
