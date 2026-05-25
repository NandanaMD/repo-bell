from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(slots=True)
class RepositoryConfig:
    owner: str
    repo: str
    token: str = ""
    enabled: bool = True

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass(slots=True)
class WebhookConfig:
    enabled: bool = True
    port: int = 8080
    secret: str = ""
    polling_fallback: bool = False


@dataclass(slots=True)
class AppConfig:
    mode: Literal["polling", "webhook"] = "polling"
    poll_interval: int = 60
    webhook: WebhookConfig = field(default_factory=WebhookConfig)
    repositories: list[RepositoryConfig] = field(default_factory=list)
    notify_users: list[str] = field(default_factory=list)
    sound_notification: bool = True
    start_with_windows: bool = False
    log_level: str = "INFO"
