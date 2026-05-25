from __future__ import annotations

import logging
import threading
import time
from typing import Callable

from app.config.models import AppConfig, RepositoryConfig
from app.github.client import GitHubClient
from app.github.event_factory import commit_to_event
from app.github.models import GitHubEvent
from app.storage.state_store import StateStore

logger = logging.getLogger(__name__)

EventCallback = Callable[[GitHubEvent], None]


class PollingMonitor:
    def __init__(
        self,
        config: AppConfig,
        client: GitHubClient,
        state_store: StateStore,
        on_event: EventCallback,
    ) -> None:
        self._config = config
        self._client = client
        self._state_store = state_store
        self._on_event = on_event
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="polling-monitor", daemon=True)
        self._thread.start()
        logger.info("Polling monitor started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        logger.info("Polling monitor stopped")

    def _run(self) -> None:
        while not self._stop.is_set():
            started_at = time.monotonic()
            for repository in self._config.repositories:
                if not repository.enabled:
                    continue
                try:
                    self._poll_repository(repository)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Unexpected polling error for %s: %s", repository.full_name, exc)

            elapsed = time.monotonic() - started_at
            sleep_seconds = max(1, self._config.poll_interval - int(elapsed))
            self._stop.wait(timeout=sleep_seconds)

    def _poll_repository(self, repo: RepositoryConfig) -> None:
        commits = self._client.fetch_latest_commits(repo, limit=10)
        if not commits:
            return

        latest_sha = self._state_store.get_latest_commit(repo.full_name)
        newest_sha = commits[0].sha

        if latest_sha is None:
            self._state_store.set_latest_commit(repo.full_name, newest_sha)
            logger.info("Initialized state for %s at %s", repo.full_name, newest_sha)
            return

        if latest_sha == newest_sha:
            return

        new_commits = []
        for commit in commits:
            if commit.sha == latest_sha:
                break
            new_commits.append(commit)

        for commit in reversed(new_commits):
            event = commit_to_event(repo.full_name, commit)
            self._on_event(event)

        self._state_store.set_latest_commit(repo.full_name, newest_sha)
