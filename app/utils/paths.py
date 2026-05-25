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
