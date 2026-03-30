"""Preset management: load defaults, CRUD user presets, resolve commands."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from core.models import Preset


def _get_default_presets_dir() -> Path:
    """Resolve the bundled default presets directory.

    Works in all environments: dev, PyInstaller onefile, onedir.
    """
    if getattr(__import__("sys"), "frozen", False) and hasattr(__import__("sys"), "_MEIPASS"):
        return Path(__import__("sys")._MEIPASS) / "presets"
    return Path(__file__).parent.parent / "presets"


def _get_user_presets_dir() -> Path:
    """User-writable directory for custom presets.

    On Windows: %APPDATA%/ff-intelligent-mvp/presets/
    On macOS/Linux: ~/.config/ff-intelligent-mvp/presets/
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    d = Path(base) / "ff-intelligent-mvp" / "presets"
    d.mkdir(parents=True, exist_ok=True)
    return d


class PresetManager:
    """Manages built-in and user-created FFmpeg presets."""

    def __init__(self) -> None:
        self._default_presets: list[Preset] = []
        self._user_presets: list[Preset] = []
        self._load_defaults()
        self._load_user_presets()

    def _load_defaults(self) -> None:
        presets_dir = _get_default_presets_dir()
        json_file = presets_dir / "default_presets.json"
        if json_file.exists():
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._default_presets = [
                Preset(**item) for item in data
            ]

    def _load_user_presets(self) -> None:
        user_dir = _get_user_presets_dir()
        if not user_dir.exists():
            return
        for fp in user_dir.glob("*.json"):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._user_presets.append(Preset(**data))
            except (json.JSONDecodeError, TypeError):
                pass

    def list_presets(self) -> list[Preset]:
        """Return all presets (defaults first, then user presets)."""
        return list(self._default_presets) + list(self._user_presets)

    def get_preset(self, preset_id: str) -> Preset | None:
        """Find a preset by ID (checks user presets first, then defaults)."""
        for p in self._user_presets:
            if p.id == preset_id:
                return p
        for p in self._default_presets:
            if p.id == preset_id:
                return p
        return None

    def save_preset(self, preset: Preset) -> Preset:
        """Create or update a user preset. Returns the saved preset."""
        idx = next(
            (i for i, p in enumerate(self._user_presets) if p.id == preset.id),
            None,
        )
        if idx is not None:
            self._user_presets[idx] = preset
        else:
            self._user_presets.append(preset)

        user_dir = _get_user_presets_dir()
        fp = user_dir / f"{preset.id}.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(preset.__dict__, f, ensure_ascii=False, indent=2)

        return preset

    def delete_preset(self, preset_id: str) -> None:
        """Delete a user preset. Raises ValueError if it's a default preset."""
        idx = next(
            (i for i, p in enumerate(self._default_presets) if p.id == preset_id),
            None,
        )
        if idx is not None:
            raise ValueError("Cannot delete built-in presets")

        idx = next(
            (i for i, p in enumerate(self._user_presets) if p.id == preset_id),
            None,
        )
        if idx is None:
            raise ValueError(f"Preset '{preset_id}' not found")

        self._user_presets.pop(idx)

        user_dir = _get_user_presets_dir()
        fp = user_dir / f"{preset_id}.json"
        if fp.exists():
            fp.unlink()

    def resolve_command(
        self,
        preset: Preset,
        input_path: str,
        output_path: str,
    ) -> list[str]:
        """Resolve a preset template into an ffmpeg argument list.

        Splits the template on whitespace first, then replaces ``{input}``
        and ``{output}`` placeholders with the actual paths. This ensures
        paths containing spaces remain as single list elements, which
        subprocess.Popen handles correctly.
        """
        args = []
        for token in preset.command_template.split():
            if token == "{input}":
                args.append(input_path)
            elif token == "{output}":
                args.append(output_path)
            else:
                args.append(token)
        return args
