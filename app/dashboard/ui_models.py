from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DashboardRow:
    event_id: str
    repository: str
    user: str
    message: str
    timestamp: str
    event_type: str
    url: str
