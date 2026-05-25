from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config.models import AppConfig, RepositoryConfig, WebhookConfig


class ConfigError(Exception):
    """Raised when the config file is invalid."""


class ConfigLoader:
    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    @property
    def path(self) -> Path:
        return self._config_path

    def load(self) -> AppConfig:
        if not self._config_path.exists():
            raise ConfigError(f"Config file not found: {self._config_path}")

        try:
            with self._config_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON config: {exc}") from exc

        return self._validate(data)

    def _validate(self, raw: dict[str, Any]) -> AppConfig:
        mode = raw.get("mode", "polling")
        if mode not in {"polling", "webhook"}:
            raise ConfigError("mode must be either 'polling' or 'webhook'")

        poll_interval = raw.get("poll_interval", 60)
        if not isinstance(poll_interval, int) or poll_interval < 10:
            raise ConfigError("poll_interval must be an integer >= 10")

        webhook_raw = raw.get("webhook", {})
        if not isinstance(webhook_raw, dict):
            raise ConfigError("webhook must be an object")

        webhook_port = webhook_raw.get("port", 8080)
        if not isinstance(webhook_port, int) or not (1 <= webhook_port <= 65535):
            raise ConfigError("webhook.port must be between 1 and 65535")

        webhook = WebhookConfig(
            enabled=bool(webhook_raw.get("enabled", True)),
            port=webhook_port,
            secret=str(webhook_raw.get("secret", "")),
            polling_fallback=bool(webhook_raw.get("polling_fallback", False)),
        )

        repositories_raw = raw.get("repositories", [])
        if not isinstance(repositories_raw, list) or not repositories_raw:
            raise ConfigError("repositories must be a non-empty array")

        repositories: list[RepositoryConfig] = []
        for index, repo_raw in enumerate(repositories_raw):
            if not isinstance(repo_raw, dict):
                raise ConfigError(f"repositories[{index}] must be an object")

            owner = str(repo_raw.get("owner", "")).strip()
            repo_name = str(repo_raw.get("repo", "")).strip()
            if not owner or not repo_name:
                raise ConfigError(f"repositories[{index}] owner and repo are required")

            repositories.append(
                RepositoryConfig(
                    owner=owner,
                    repo=repo_name,
                    token=str(repo_raw.get("token", "")),
                    enabled=bool(repo_raw.get("enabled", True)),
                )
            )

        notify_users_raw = raw.get("notify_users", [])
        if not isinstance(notify_users_raw, list):
            raise ConfigError("notify_users must be an array")
        notify_users = [str(item).strip() for item in notify_users_raw if str(item).strip()]

        log_level = str(raw.get("log_level", "INFO")).upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigError("log_level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL")

        return AppConfig(
            mode=mode,
            poll_interval=poll_interval,
            webhook=webhook,
            repositories=repositories,
            notify_users=notify_users,
            sound_notification=bool(raw.get("sound_notification", True)),
            start_with_windows=bool(raw.get("start_with_windows", False)),
            log_level=log_level,
        )
