from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ActivityItem:
    event_id: str
    event_type: str
    repository: str
    user: str
    message: str
    timestamp: str
    url: str


@dataclass(slots=True)
class AppState:
    latest_commits: dict[str, str] = field(default_factory=dict)
    processed_events: list[str] = field(default_factory=list)
    recent_activity: list[dict[str, str]] = field(default_factory=list)


class StateStore:
    """Thread-safe JSON-backed state persistence."""

    def __init__(self, state_path: Path) -> None:
        self._state_path = state_path
        self._lock = threading.RLock()
        self._state = AppState()

    def load(self) -> None:
        with self._lock:
            if not self._state_path.exists():
                self._persist()
                return

            try:
                with self._state_path.open("r", encoding="utf-8") as file:
                    raw = json.load(file)
            except (json.JSONDecodeError, OSError) as exc:
                logger.error("Failed to read state file: %s", exc)
                backup = self._state_path.with_suffix(".corrupt.json")
                try:
                    self._state_path.replace(backup)
                    logger.warning("Corrupted state backed up to %s", backup)
                except OSError:
                    logger.warning("Failed to backup corrupted state file")
                self._state = AppState()
                self._persist()
                return

            self._state = AppState(
                latest_commits=dict(raw.get("latest_commits", {})),
                processed_events=list(raw.get("processed_events", []))[-500:],
                recent_activity=list(raw.get("recent_activity", []))[:10],
            )

    def get_latest_commit(self, repo_full_name: str) -> str | None:
        with self._lock:
            return self._state.latest_commits.get(repo_full_name)

    def set_latest_commit(self, repo_full_name: str, sha: str) -> None:
        with self._lock:
            self._state.latest_commits[repo_full_name] = sha
            self._persist()

    def has_event(self, event_id: str) -> bool:
        with self._lock:
            return event_id in self._state.processed_events

    def mark_event_processed(self, event_id: str) -> None:
        with self._lock:
            self._state.processed_events.append(event_id)
            self._state.processed_events = self._state.processed_events[-500:]
            self._persist()

    def add_activity(self, item: ActivityItem) -> None:
        with self._lock:
            serialized = asdict(item)
            self._state.recent_activity.insert(0, serialized)
            self._state.recent_activity = self._state.recent_activity[:10]
            self._persist()

    def get_recent_activity(self) -> list[dict[str, str]]:
        with self._lock:
            return list(self._state.recent_activity)

    def _persist(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "latest_commits": self._state.latest_commits,
            "processed_events": self._state.processed_events,
            "recent_activity": self._state.recent_activity,
            "saved_at": datetime.utcnow().isoformat() + "Z",
        }
        tmp = self._state_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
        tmp.replace(self._state_path)
