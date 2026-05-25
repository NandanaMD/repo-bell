from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.github.models import CommitInfo, GitHubEvent


def commit_to_event(repository: str, commit: CommitInfo, event_type: str = "push") -> GitHubEvent:
    timestamp = _format_timestamp(commit.timestamp)
    return GitHubEvent(
        event_id=f"commit:{commit.sha}",
        event_type=event_type,
        repository=repository,
        user=commit.author,
        message=commit.message,
        timestamp=timestamp,
        url=commit.url,
    )


def webhook_payload_to_events(
    event_name: str,
    delivery_id: str,
    payload: dict[str, Any],
) -> list[GitHubEvent]:
    repository_name = str((payload.get("repository") or {}).get("full_name") or "unknown/unknown")

    if event_name == "push":
        pusher = str((payload.get("pusher") or {}).get("name") or "unknown")
        commits = payload.get("commits") or []
        repository_html_url = str((payload.get("repository") or {}).get("html_url") or "")
        results: list[GitHubEvent] = []
        for item in commits[:10]:
            sha = str(item.get("id") or "")
            url = str(item.get("url") or "")
            if repository_html_url and sha:
                url = f"{repository_html_url}/commit/{sha}"
            message = str(item.get("message") or "(no commit message)")
            timestamp = _format_timestamp(str(item.get("timestamp") or ""))
            results.append(
                GitHubEvent(
                    event_id=f"{delivery_id}:{sha}",
                    event_type="push",
                    repository=repository_name,
                    user=pusher,
                    message=message.split("\n", maxsplit=1)[0],
                    timestamp=timestamp,
                    url=url,
                )
            )
        return results

    if event_name == "pull_request":
        pr = payload.get("pull_request") or {}
        if str(payload.get("action")) != "closed" or not bool(pr.get("merged")):
            return []

        user = str((pr.get("user") or {}).get("login") or "unknown")
        title = str(pr.get("title") or "Merged pull request")
        merged_at = _format_timestamp(str(pr.get("merged_at") or ""))
        url = str(pr.get("html_url") or "")
        return [
            GitHubEvent(
                event_id=f"{delivery_id}:pr:{pr.get('id')}",
                event_type="pull_request_merged",
                repository=repository_name,
                user=user,
                message=title,
                timestamp=merged_at,
                url=url,
            )
        ]

    if event_name == "release":
        action = str(payload.get("action") or "")
        if action != "published":
            return []
        release = payload.get("release") or {}
        user = str((release.get("author") or {}).get("login") or "unknown")
        name = str(release.get("name") or release.get("tag_name") or "New release")
        published_at = _format_timestamp(str(release.get("published_at") or ""))
        url = str(release.get("html_url") or "")
        return [
            GitHubEvent(
                event_id=f"{delivery_id}:release:{release.get('id')}",
                event_type="release_published",
                repository=repository_name,
                user=user,
                message=name,
                timestamp=published_at,
                url=url,
            )
        ]

    return []


def _format_timestamp(raw: str) -> str:
    if not raw:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return raw
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
