from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        return executable_dir
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return project_root() / "data"


def logs_dir() -> Path:
    return data_dir() / "logs"


def bundle_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return project_root()


def assets_dir() -> Path:
    return bundle_dir() / "assets"


def icon_path() -> Path:
    return assets_dir() / "icon.ico"
