"""Loguru configuration with a pywebvue frontend sink."""

from __future__ import annotations

import sys

from loguru import logger
from core.paths import get_log_dir

# Remove default handler to avoid duplicate output
logger.remove()

# Console handler for development debugging
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG",
)


try:
    _log_dir = get_log_dir()
    _file_sink_id = logger.add(
        str(_log_dir / "app_{time:YYYY-MM-DD}.log"),
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
except Exception:
    pass  # File logging is best-effort; console still works

# Frontend sink placeholder - will be added when bridge is ready
_frontend_sink_id: int | None = None


def setup_frontend_sink(emit_fn) -> None:
    """Add a loguru sink that forwards log messages to the frontend via pywebvue events."""
    global _frontend_sink_id

    if _frontend_sink_id is not None:
        return

    def _sink(message) -> None:
        try:
            record = message.record
            level = record["level"].name
            line = f"[{level}] {record['message']}"
            emit_fn("log_line", {"line": line})
        except Exception:
            pass

    _frontend_sink_id = logger.add(
        _sink,
        format="{message}",
        level="WARNING",
    )


def get_logger():
    """Return the configured loguru logger instance."""
    return logger
