"""AppSettings load/save to data/settings.json."""

from __future__ import annotations

import json

from core.models import AppSettings
from core.paths import get_data_dir, get_settings_path


def load_settings(
    default: AppSettings | None = None,
) -> AppSettings:
    """Load settings from disk, returning *default* when the file is missing."""
    path = get_settings_path()
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
    get_data_dir()
    path = get_settings_path()
    path.write_text(
        json.dumps(settings.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
