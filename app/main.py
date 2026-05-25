from __future__ import annotations

import copy
import json
import logging
import signal
import sys
import threading
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.loader import ConfigError, ConfigLoader
from app.config.models import AppConfig
from app.config.writer import ConfigWriter
from app.github.client import GitHubClient
from app.github.models import GitHubEvent
from app.github.polling_monitor import PollingMonitor
from app.logging.setup import configure_logging
from app.notifications.toast import NotificationService
from app.startup.windows_startup import StartupManager
from app.storage.activity_feed import ActivityFeed
from app.storage.state_store import ActivityItem, StateStore
from app.tray.tray_app import TrayApp
from app.utils.paths import data_dir, logs_dir
from app.utils.windows_app import set_process_app_id
from app.webhook.server import WebhookServer

logger = logging.getLogger(__name__)


class RepoBellApplication:
    """Coordinates monitoring services, tray controls, and persistence."""

    def __init__(self) -> None:
        self._data_dir = data_dir()
        self._config_path = self._data_dir / "config.json"
        self._state_path = self._data_dir / "state.json"
        self._logs_dir = logs_dir()

        self._loader = ConfigLoader(self._config_path)
        self._writer = ConfigWriter(self._config_path)
        self._config = self._load_config_or_raise()
        configure_logging(self._logs_dir, self._config.log_level)

        self._state_store = StateStore(self._state_path)
        self._state_store.load()

        self._feed = ActivityFeed(max_items=10)
        self._feed.load_initial(self._restore_activity_events())

        self._client = GitHubClient(timeout_seconds=10)
        self._notifications = NotificationService(enabled=True)
        self._startup = StartupManager()

        self._polling_monitor: PollingMonitor | None = None
        self._webhook_server: WebhookServer | None = None
        self._monitoring_enabled = False
        self._lock = threading.RLock()

        self._tray = TrayApp(
            on_start_monitoring=self.start_monitoring,
            on_stop_monitoring=self.stop_monitoring,
            on_reload_config=self.reload_config,
            on_save_config=self.save_config,
            get_current_config=self.get_current_config,
            on_toggle_notifications=self.toggle_notifications,
            on_exit=self.shutdown,
            logs_path=self._logs_dir,
            config_path=self._config_path,
        )
        self._feed.subscribe(self._tray.update_dashboard)
        self._tray.update_dashboard(self._feed.list_events())

        self._apply_startup_setting()

    def run(self) -> None:
        self.start_monitoring()
        self._register_signal_handlers()
        self._tray.run()

    def start_monitoring(self) -> None:
        with self._lock:
            if self._monitoring_enabled:
                return

            if self._config.mode == "polling":
                self._start_polling()
            else:
                self._start_webhook()
                if self._config.webhook.polling_fallback:
                    self._start_polling()

            self._monitoring_enabled = True
            logger.info("Monitoring started in %s mode", self._config.mode)

    def stop_monitoring(self) -> None:
        with self._lock:
            self._stop_services()
            self._monitoring_enabled = False
            logger.info("Monitoring stopped")

    def reload_config(self) -> None:
        logger.info("Reloading configuration")
        try:
            new_config = self._loader.load()
        except ConfigError as exc:
            logger.error("Config reload failed: %s", exc)
            self._notifications.notify("Repo Bell", f"Config reload failed: {exc}")
            return

        with self._lock:
            was_running = self._monitoring_enabled
            self._stop_services()
            self._config = new_config
            configure_logging(self._logs_dir, self._config.log_level)
            self._apply_startup_setting()
            if was_running:
                if self._config.mode == "polling":
                    self._start_polling()
                else:
                    self._start_webhook()
                    if self._config.webhook.polling_fallback:
                        self._start_polling()
            self._monitoring_enabled = was_running

        self._notifications.notify("Repo Bell", "Configuration reloaded")

    def get_current_config(self) -> AppConfig:
        with self._lock:
            return copy.deepcopy(self._config)

    def save_config(self, new_config: AppConfig) -> None:
        logger.info("Saving configuration from settings window")
        self._writer.save(new_config)
        self.reload_config()

    def toggle_notifications(self) -> None:
        enabled = not self._notifications.enabled
        state = "enabled" if enabled else "disabled"
        if not enabled:
            self._notifications.notify("Repo Bell", "Notifications disabled")
        self._notifications.set_enabled(enabled)
        logger.info("Notifications %s", state)
        if enabled:
            self._notifications.notify("Repo Bell", "Notifications enabled")

    def shutdown(self) -> None:
        logger.info("Shutting down Repo Bell")
        self.stop_monitoring()
        self._tray.stop()

    def _start_polling(self) -> None:
        if self._polling_monitor is not None:
            return

        self._polling_monitor = PollingMonitor(
            config=self._config,
            client=self._client,
            state_store=self._state_store,
            on_event=self._handle_event,
        )
        self._polling_monitor.start()

    def _start_webhook(self) -> None:
        if not self._config.webhook.enabled:
            logger.warning("Webhook mode selected but webhook is disabled in config")
            return

        if self._webhook_server is not None:
            return

        try:
            self._webhook_server = WebhookServer(
                port=self._config.webhook.port,
                secret=self._config.webhook.secret,
                on_event=self._handle_event,
            )
        except RuntimeError as exc:
            logger.error("Failed to initialize webhook server: %s", exc)
            self._notifications.notify("Repo Bell", f"Webhook unavailable: {exc}")
            self._webhook_server = None
            return
        try:
            self._webhook_server.start()
        except (OSError, RuntimeError) as exc:
            logger.error("Failed to start webhook server: %s", exc)
            self._webhook_server = None

    def _stop_services(self) -> None:
        if self._polling_monitor is not None:
            self._polling_monitor.stop()
            self._polling_monitor = None

        if self._webhook_server is not None:
            self._webhook_server.stop()
            self._webhook_server = None

    def _handle_event(self, event: GitHubEvent) -> None:
        if self._state_store.has_event(event.event_id):
            return

        self._state_store.mark_event_processed(event.event_id)

        if self._config.notify_users and event.user not in self._config.notify_users:
            logger.debug("Skipping event for user %s due to notify_users filter", event.user)
            return

        self._state_store.add_activity(
            ActivityItem(
                event_id=event.event_id,
                event_type=event.event_type,
                repository=event.repository,
                user=event.user,
                message=event.message,
                timestamp=event.timestamp,
                url=event.url,
            )
        )

        self._feed.add(event)

        title = f"Repo Bell | {event.event_type}"
        message = (
            f"{event.user} | {event.repository}\n"
            f"{event.message}\n"
            f"{event.timestamp}"
        )
        self._notifications.notify(title, message)

    def _restore_activity_events(self) -> list[GitHubEvent]:
        events: list[GitHubEvent] = []
        for item in self._state_store.get_recent_activity():
            events.append(
                GitHubEvent(
                    event_id=str(item.get("event_id", "")),
                    event_type=str(item.get("event_type", "unknown")),
                    repository=str(item.get("repository", "unknown/unknown")),
                    user=str(item.get("user", "unknown")),
                    message=str(item.get("message", "")),
                    timestamp=str(item.get("timestamp", "")),
                    url=str(item.get("url", "")),
                )
            )
        return events

    def _load_config_or_raise(self) -> AppConfig:
        try:
            return self._loader.load()
        except ConfigError as exc:
            raise RuntimeError(f"Invalid config: {exc}") from exc

    def _apply_startup_setting(self) -> None:
        self._startup.set_enabled(self._config.start_with_windows)

    def _register_signal_handlers(self) -> None:
        def _handler(_signum, _frame) -> None:
            self.shutdown()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _handler)
            except ValueError:
                logger.debug("Signal registration skipped for %s", sig)


def ensure_data_paths() -> None:
    data_path = data_dir()
    log_path = logs_dir()
    data_path.mkdir(parents=True, exist_ok=True)
    log_path.mkdir(parents=True, exist_ok=True)

    config_path = data_path / "config.json"
    if not config_path.exists():
        config_path.write_text(
            json.dumps(
                {
                    "mode": "polling",
                    "poll_interval": 60,
                    "webhook": {
                        "enabled": True,
                        "port": 8080,
                        "secret": "",
                        "polling_fallback": False,
                    },
                    "repositories": [
                        {
                            "owner": "microsoft",
                            "repo": "vscode",
                            "token": "",
                            "enabled": True,
                        }
                    ],
                    "notify_users": [],
                    "sound_notification": True,
                    "start_with_windows": False,
                    "log_level": "INFO",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    state_path = data_path / "state.json"
    if not state_path.exists():
        state_path.write_text(
            json.dumps(
                {
                    "latest_commits": {},
                    "processed_events": [],
                    "recent_activity": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    set_process_app_id("RepoBell.Desktop")
    ensure_data_paths()
    app = RepoBellApplication()
    app.run()
