from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GitHubEvent:
    event_id: str
    event_type: str
    repository: str
    user: str
    message: str
    timestamp: str
    url: str


@dataclass(slots=True)
class CommitInfo:
    sha: str
    message: str
    url: str
    author: str
    timestamp: str
