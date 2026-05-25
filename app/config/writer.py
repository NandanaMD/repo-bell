from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.config.models import AppConfig


class ConfigWriter:
    """Persists validated app config to disk safely using atomic replace."""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    def save(self, config: AppConfig) -> None:
        payload = asdict(config)
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._config_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
        tmp_path.replace(self._config_path)
