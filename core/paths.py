"""Centralized application data paths.

All persistent data (settings, logs, presets) lives under <app_dir>/data/.
<app_dir> is the directory containing the executable (PyInstaller onedir)
or the project root (development mode).
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_NAME = "ff-intelligent-neo"


def get_app_dir() -> Path:
    """Return the application base directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """Return (and create) the unified data directory."""
    d = get_app_dir() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_settings_path() -> Path:
    return get_data_dir() / "settings.json"


def get_log_dir() -> Path:
    d = get_data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_presets_dir() -> Path:
    d = get_data_dir() / "presets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _old_appdata_dir() -> Path | None:
    """Return the legacy APPDATA directory, or None if not found."""
    if os.name == "nt":
        base = os.environ.get("APPDATA", "")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", "")
        if not base:
            base = os.path.expanduser("~/.config")
    if not base:
        base = os.path.expanduser("~")
    old = Path(base) / APP_NAME
    return old if old.exists() else None


def migrate_if_needed() -> None:
    """Copy persistent data from legacy APPDATA to <app_dir>/data/.

    Uses copy-not-move: the old files are kept as backup.
    This is idempotent - safe to call on every startup.
    """
    new_data = get_data_dir()
    settings_new = new_data / "settings.json"
    if settings_new.exists():
        return

    old_dir = _old_appdata_dir()
    if old_dir is None:
        return

    # Migrate settings.json
    old_settings = old_dir / "settings.json"
    if old_settings.exists():
        try:
            shutil.copy2(str(old_settings), str(settings_new))
            print(f"[paths] Migrated settings.json from {old_settings} to {settings_new}")
        except OSError as exc:
            print(f"[paths] Failed to migrate settings.json: {exc}")

    # Migrate presets directory
    old_presets = old_dir / "presets"
    if old_presets.is_dir():
        new_presets = get_presets_dir()
        try:
            for item in old_presets.iterdir():
                if item.is_file():
                    dest = new_presets / item.name
                    if not dest.exists():
                        shutil.copy2(str(item), str(dest))
            print(f"[paths] Migrated presets from {old_presets} to {new_presets}")
        except OSError as exc:
            print(f"[paths] Failed to migrate presets: {exc}")

    # Migrate queue_state.json
    old_queue = old_dir / "queue_state.json"
    new_queue = new_data / "queue_state.json"
    if old_queue.exists() and not new_queue.exists():
        try:
            shutil.copy2(str(old_queue), str(new_queue))
            print(f"[paths] Migrated queue_state.json from {old_queue} to {new_queue}")
        except OSError as exc:
            print(f"[paths] Failed to migrate queue_state.json: {exc}")
