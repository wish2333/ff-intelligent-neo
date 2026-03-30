# -*- mode: python ; coding: utf-8 -*-
# ============================================================
# PyInstaller spec for FF Intelligent MVP
# ============================================================

import sys
from pathlib import Path

project_root = Path(SPECPATH)


# ========== [MODIFY] Entry point ==========
ENTRY_SCRIPT = str(project_root / "main.py")


# ========== [MODIFY] Output name ==========
APP_NAME = "ff-intelligent-mvp"


# ========== [MODIFY] Frontend assets ==========
_frontend_dist = project_root / "frontend_dist"
datas = [(str(_frontend_dist), "frontend_dist")]

# Bundle default presets
_presets_dir = project_root / "presets"
datas.append((str(_presets_dir), "presets"))


# ========== FFmpeg binaries ==========
_ffmpeg_bin_dir = project_root / "ffmpeg_binaries"
_ffmpeg_suffix = ".exe" if sys.platform == "win32" else ""
binaries = []
for _bin_name in ("ffmpeg", "ffprobe"):
    _bin_path = _ffmpeg_bin_dir / f"{_bin_name}{_ffmpeg_suffix}"
    if _bin_path.exists():
        binaries.append((str(_bin_path), "."))


# ========== [MODIFY] Icon ==========
ICON = None


# ========== [MODIFY] Hidden imports ==========
hiddenimports = [
    "pywebvue",
    "pywebvue.app",
    "pywebvue.bridge",
    "core",
    "core.models",
    "core.ffmpeg_setup",
    "core.file_info",
    "core.preset_manager",
    "core.ffmpeg_runner",
    "core.batch_runner",
    "core.app_info",
    "core.logging",
    "static_ffmpeg",
]


# ========== [MODIFY] GUI framework excludes ==========
EXCLUDES_WIN32 = ["PyQt5", "PyQt6", "PySide2", "PySide6", "tkinter"]
EXCLUDES_LINUX = ["PyQt5", "PyQt6", "PySide2", "PySide6"]
EXCLUDES_DARWIN = ["PyQt5", "PyQt6", "PySide2", "PySide6", "tkinter"]


# ========== Usually no need to modify below ==========

a = Analysis(
    [ENTRY_SCRIPT],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

if sys.platform == "win32":
    a.excludes += EXCLUDES_WIN32
elif sys.platform == "linux":
    a.excludes += EXCLUDES_LINUX
elif sys.platform == "darwin":
    a.excludes += EXCLUDES_DARWIN

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    console=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
