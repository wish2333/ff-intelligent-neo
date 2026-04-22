"""AppSettings load/save to APPDATA/settings.json."""

from __future__ import annotations

import json
import os
from pathlib import Path

from core.models import AppSettings

APP_NAME = "ff-intelligent-neo"


def _appdata_dir() -> Path:
    """Return the APPDATA directory for this application."""
    base = os.environ.get("APPDATA", "")
    if not base:
        base = os.path.expanduser("~")
    return Path(base) / APP_NAME


def _settings_path() -> Path:
    return _appdata_dir() / "settings.json"


def _ensure_dir() -> Path:
    d = _appdata_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_settings(
    default: AppSettings | None = None,
) -> AppSettings:
    """Load settings from disk, returning *default* when the file is missing."""
    path = _settings_path()
    if not path.exists():
        return default or AppSettings()
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        return AppSettings.from_dict(data)
    except (json.JSONDecodeError, OSError) as exc:
        # If the user already has a custom fallback, delegate to it
        if default is not None:
            return default
        return AppSettings()


def save_settings(settings: AppSettings) -> None:
    """Persist settings to disk, creating the directory if necessary."""
    _ensure_dir()
    path = _settings_path()
    path.write_text(
        json.dumps(settings.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
