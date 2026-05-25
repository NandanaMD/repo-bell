from __future__ import annotations

import logging

from win10toast import ToastNotifier

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._notifier = ToastNotifier()

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
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to show toast notification: %s", exc)
