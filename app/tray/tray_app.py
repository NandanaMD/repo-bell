from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

import pystray
from pystray import MenuItem as Item

from app.dashboard.dashboard_window import DashboardWindow
from app.dashboard.ui_models import DashboardRow
from app.github.models import GitHubEvent
from app.tray.icon_factory import build_tray_icon
from app.tray.settings_window import SettingsWindow
from app.utils.paths import icon_path

logger = logging.getLogger(__name__)


class TrayApp:
    def __init__(
        self,
        on_start_monitoring,
        on_stop_monitoring,
        on_reload_config,
        on_save_config,
        get_current_config,
        on_toggle_notifications,
        on_exit,
        logs_path: Path,
        config_path: Path,
    ) -> None:
        self._on_start_monitoring = on_start_monitoring
        self._on_stop_monitoring = on_stop_monitoring
        self._on_reload_config = on_reload_config
        self._on_save_config = on_save_config
        self._get_current_config = get_current_config
        self._on_toggle_notifications = on_toggle_notifications
        self._on_exit = on_exit
        self._logs_path = logs_path
        self._config_path = config_path
        self._icon_path = icon_path()

        self._dashboard = DashboardWindow(icon_file=self._icon_path)
        self._dashboard_thread: threading.Thread | None = None
        self._latest_rows: list[DashboardRow] = []
        self._settings = SettingsWindow(on_save=self._on_save_config, icon_file=self._icon_path)
        self._settings_thread: threading.Thread | None = None

        self._icon = pystray.Icon(
            "RepoBell",
            icon=build_tray_icon(),
            title="Repo Bell",
            menu=pystray.Menu(
                Item("Start Monitoring", self._start_monitoring),
                Item("Stop Monitoring", self._stop_monitoring),
                Item("Reload Config", self._reload_config),
                Item("Open Settings", self._open_settings),
                Item("Open Activity Dashboard", self._open_dashboard),
                Item("Open Logs Folder", self._open_logs_folder),
                Item("Open Config Folder", self._open_config_folder),
                Item("Enable/Disable Notifications", self._toggle_notifications),
                Item("Exit", self._exit),
            ),
        )

    def run(self) -> None:
        self._icon.run()

    def stop(self) -> None:
        self._icon.stop()

    def update_dashboard(self, events: list[GitHubEvent]) -> None:
        rows = [
            DashboardRow(
                event_id=e.event_id,
                repository=e.repository,
                user=e.user,
                message=e.message,
                timestamp=e.timestamp,
                event_type=e.event_type,
                url=e.url,
            )
            for e in events
        ]
        self._latest_rows = rows

        if self._dashboard_thread and self._dashboard_thread.is_alive():
            self._dashboard.update_rows(rows)

    def _start_monitoring(self, _icon, _item) -> None:
        self._on_start_monitoring()

    def _stop_monitoring(self, _icon, _item) -> None:
        self._on_stop_monitoring()

    def _reload_config(self, _icon, _item) -> None:
        self._on_reload_config()

    def _open_dashboard(self, _icon, _item) -> None:
        if self._dashboard_thread and self._dashboard_thread.is_alive():
            self._dashboard.show(self._latest_rows)
            self._dashboard.update_rows(self._latest_rows)
            return

        self._dashboard_thread = threading.Thread(
            target=self._dashboard.show,
            args=(self._latest_rows,),
            name="dashboard-ui",
            daemon=True,
        )
        self._dashboard_thread.start()

    def _open_settings(self, _icon, _item) -> None:
        config = self._get_current_config()
        if self._settings_thread and self._settings_thread.is_alive():
            self._settings.show(config)
            return

        self._settings_thread = threading.Thread(
            target=self._settings.show,
            args=(config,),
            name="settings-ui",
            daemon=True,
        )
        self._settings_thread.start()

    def _open_logs_folder(self, _icon, _item) -> None:
        try:
            os.startfile(self._logs_path)
        except OSError as exc:
            logger.error("Failed to open logs folder: %s", exc)

    def _open_config_folder(self, _icon, _item) -> None:
        try:
            os.startfile(self._config_path.parent)
        except OSError as exc:
            logger.error("Failed to open config folder: %s", exc)

    def _toggle_notifications(self, _icon, _item) -> None:
        self._on_toggle_notifications()

    def _exit(self, _icon, _item) -> None:
        logger.info("Exit requested from tray menu")
        self._on_exit()
