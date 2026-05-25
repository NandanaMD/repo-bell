from __future__ import annotations

import threading
from typing import Callable

from app.github.models import GitHubEvent

ActivitySubscriber = Callable[[list[GitHubEvent]], None]


class ActivityFeed:
    """In-memory rolling cache for latest events with subscriber callbacks."""

    def __init__(self, max_items: int = 10) -> None:
        self._max_items = max_items
        self._events: list[GitHubEvent] = []
        self._subscribers: list[ActivitySubscriber] = []
        self._lock = threading.RLock()

    def load_initial(self, events: list[GitHubEvent]) -> None:
        with self._lock:
            self._events = events[: self._max_items]

    def add(self, event: GitHubEvent) -> None:
        with self._lock:
            self._events.insert(0, event)
            self._events = self._events[: self._max_items]
            snapshot = list(self._events)
            subscribers = list(self._subscribers)

        for callback in subscribers:
            callback(snapshot)

    def list_events(self) -> list[GitHubEvent]:
        with self._lock:
            return list(self._events)

    def subscribe(self, callback: ActivitySubscriber) -> None:
        with self._lock:
            self._subscribers.append(callback)
