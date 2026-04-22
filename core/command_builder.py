"""Build FFmpeg command-line arguments from TaskConfig.

Supports transcode parameters, filter chains (crop, scale, rotate,
speed, watermark overlay, volume), and parameter validation with
priority-based automatic filter ordering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from core.models import TaskConfig

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_VIDEO_CODECS = {"libx264", "libx265", "copy", "none"}
VALID_AUDIO_CODECS = {"aac", "libmp3lame", "copy", "none"}
VALID_OUTPUT_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".mp3", ".aac", ".flac", ".wav"
}
VALID_ROTATE_OPTIONS = {"", "none", "transpose=1", "transpose=2", "transpose=3"}
VALID_WATERMARK_POSITIONS = {"", "top-left", "top-right", "bottom-left", "bottom-right"}

# ---------------------------------------------------------------------------
# Validation context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationContext:
    """Extra context for parameter validation."""
    file_info: dict | None = None
    ffmpeg_version: str | None = None


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
        extra_inputs.extend(["-i", fc.watermark_path])

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
                [{"level": "error", "message": "Speed must be between 0.25 and 100 (atempo limit)"}]
                if float(val) < 0.25 or float(val) > 100
                else (
                    [{"level": "warning", "message": "Speed < 0.5 or > 4.0 may cause audio-video desync"}]
                    if float(val) < 0.5 or float(val) > 4.0
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
    pos_map = {
        "top-left": f"overlay={margin}:{margin}",
        "top-right": "overlay=W-w-10:10",
        "bottom-left": "overlay=10:H-h-10",
        "bottom-right": "overlay=W-w-10:H-h-10",
    }

    # Use margin for all positions
    exprs = {
        "top-left": f"overlay={margin}:{margin}",
        "top-right": f"overlay=main_w-overlay_w-{margin}:{margin}",
        "bottom-left": f"overlay={margin}:main_h-overlay_h-{margin}",
        "bottom-right": f"overlay=main_w-overlay_w-{margin}:main_h-overlay_h-{margin}",
    }
    return [exprs.get(position, exprs["bottom-right"])]


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
    New parameters only need to be registered once in _TRANSPILE_PARAMS
    or _FILTERS to appear in both the command and the validation.

    Args:
        config: Task configuration containing transcode and filter params.
        input_path: Source media file path.
        output_path: Destination file path.

    Returns:
        List of arguments to pass to subprocess.Popen.
    """
    tc = config.transcode
    fc = config.filters
    ctx = ValidationContext()

    # --- transcode args (built from registry for consistency) ---
    transcode_args = _build_transcode_args(tc, ctx)

    # --- filter chain ---
    has_filters = any([
        fc.rotate,
        fc.crop,
        fc.watermark_path,
        fc.volume,
        fc.speed,
        tc.resolution,
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

    # --- assemble: input, extra inputs, transcode, filters, output ---
    args = ["-i", input_path]
    args.extend(extra_inputs)
    args.extend(transcode_args)
    args.extend(filter_args)
    args.extend(["-y", output_path])

    return args


def build_command_preview(config: TaskConfig) -> str:
    """Build a human-readable FFmpeg command string for preview.

    Uses placeholder 'input.mp4' for the input and derives the
    output filename from the configured extension.
    """
    ext = config.transcode.output_extension or ".mp4"
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

    has_filters = any([fc.rotate, fc.crop, fc.watermark_path, fc.volume, fc.speed])
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

    errors = [i["message"] for i in issues if i["level"] == "error"]
    warnings = [i["message"] for i in issues if i["level"] == "warning"]

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

    stem = src.stem
    if same_dir:
        filename = f"{stem}-{timestamp}{ext}"
    else:
        filename = f"{stem}{ext}"

    if output_dir:
        return str(Path(output_dir) / filename)
    return str(src.parent / filename)
