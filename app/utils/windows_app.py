from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def set_process_app_id(app_id: str = "RepoBell.Desktop") -> None:
    """Set explicit Windows AppUserModelID for proper toast app identity."""
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Unable to set process app id: %s", exc)
