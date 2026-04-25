"""Preset management: load defaults, CRUD user presets.

Presets use the structured TaskConfig format (transcode + filters),
not the old command_template format.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from core.models import Preset
from core.paths import get_presets_dir


def _get_default_presets_dir() -> Path:
    """Resolve the bundled default presets directory.

    Works in all environments: dev, PyInstaller onefile, onedir.
    """
    if getattr(__import__("sys"), "frozen", False) and hasattr(__import__("sys"), "_MEIPASS"):
        return Path(__import__("sys")._MEIPASS) / "presets"
    return Path(__file__).parent.parent / "presets"


class PresetManager:
    """Manages built-in and user-created FFmpeg presets.

    Built-in presets are loaded from ``presets/default_presets.json`` (read-only).
    User presets are stored as individual JSON files in APPDATA.
    """

    def __init__(self) -> None:
        self._default_presets: list[Preset] = []
        self._user_presets: list[Preset] = []
        self._load_defaults()
        self._load_user_presets()

    def _load_defaults(self) -> None:
        presets_dir = _get_default_presets_dir()
        json_file = presets_dir / "default_presets.json"
        if not json_file.exists():
            return
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._default_presets = [
                    Preset.from_dict(item) for item in data
                ]
        except (json.JSONDecodeError, TypeError, KeyError):
            self._default_presets = []

    def _load_user_presets(self) -> None:
        user_dir = get_presets_dir()
        if not user_dir.exists():
            return
        for fp in user_dir.glob("*.json"):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._user_presets.append(Preset.from_dict(data))
            except (json.JSONDecodeError, TypeError, KeyError):
                pass

    def list_presets(self) -> list[dict]:
        """Return all presets as dicts (defaults first, then user presets)."""
        defaults = [p.to_dict() for p in self._default_presets]
        users = [p.to_dict() for p in self._user_presets]
        return defaults + users

    def get_preset(self, preset_id: str) -> dict | None:
        """Find a preset by ID. Returns dict or None."""
        for p in self._user_presets:
            if p.id == preset_id:
                return p.to_dict()
        for p in self._default_presets:
            if p.id == preset_id:
                return p.to_dict()
        return None

    def save_preset(self, preset_data: dict) -> dict:
        """Create or update a user preset.

        Args:
            preset_data: Dict with at least 'name'. If 'id' is provided
                         and matches an existing user preset, it will be updated.

        Returns:
            The saved preset as dict.
        """
        preset_id = preset_data.get("id", "")
        is_update = bool(preset_id)

        if not is_update:
            preset_id = uuid.uuid4().hex[:8]

        preset = Preset.from_dict({
            "id": preset_id,
            "name": preset_data.get("name", "Unnamed Preset"),
            "description": preset_data.get("description", ""),
            "config": preset_data.get("config", {}),
            "is_default": False,
        })

        # Update or append
        if is_update:
            idx = next(
                (i for i, p in enumerate(self._user_presets) if p.id == preset_id),
                None,
            )
            if idx is not None:
                self._user_presets[idx] = preset
            else:
                self._user_presets.append(preset)
        else:
            self._user_presets.append(preset)

        # Persist to disk
        user_dir = get_presets_dir()
        fp = user_dir / f"{preset_id}.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(preset.to_dict(), f, ensure_ascii=False, indent=2)

        return preset.to_dict()

    def delete_preset(self, preset_id: str) -> None:
        """Delete a user preset.

        Raises:
            ValueError: If the preset is a built-in default or not found.
        """
        # Check if it's a default
        for p in self._default_presets:
            if p.id == preset_id:
                raise ValueError("Cannot delete built-in presets")

        idx = next(
            (i for i, p in enumerate(self._user_presets) if p.id == preset_id),
            None,
        )
        if idx is None:
            raise ValueError(f"Preset '{preset_id}' not found")

        self._user_presets.pop(idx)

        user_dir = get_presets_dir()
        fp = user_dir / f"{preset_id}.json"
        if fp.exists():
            fp.unlink()
