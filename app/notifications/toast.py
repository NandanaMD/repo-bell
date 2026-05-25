from __future__ import annotations

import logging
from pathlib import Path

from win10toast import ToastNotifier

from app.utils.paths import icon_path

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._notifier = ToastNotifier()
        self._icon_file: Path | None = None

        candidate = icon_path()
        if candidate.exists():
            self._icon_file = candidate

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def notify(self, title: str, message: str, duration: int = 6) -> None:
        if not self._enabled:
            return

        try:
            self._notifier.show_toast(
                title=title,
                msg=message,
                duration=duration,
                threaded=True,
                icon_path=str(self._icon_file) if self._icon_file is not None else None,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to show toast notification: %s", exc)
