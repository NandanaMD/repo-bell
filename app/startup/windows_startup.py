from __future__ import annotations

import logging
import sys
import winreg
from pathlib import Path

logger = logging.getLogger(__name__)


class StartupManager:
    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "RepoBell"

    def __init__(self) -> None:
        self._executable = Path(sys.executable)
        self._script = Path(sys.argv[0]).resolve()

    def set_enabled(self, enabled: bool) -> None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                if enabled:
                    command = self._startup_command()
                    winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, command)
                else:
                    try:
                        winreg.DeleteValue(key, self.APP_NAME)
                    except FileNotFoundError:
                        pass
        except OSError as exc:
            logger.error("Failed to update startup registry key: %s", exc)

    def is_enabled(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.RUN_KEY, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, self.APP_NAME)
                return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            logger.error("Failed to read startup registry key: %s", exc)
            return False

    def _startup_command(self) -> str:
        if self._is_frozen_executable():
            return f'"{self._executable}"'
        return f'"{self._executable}" "{self._script}"'

    @staticmethod
    def _is_frozen_executable() -> bool:
        return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))
