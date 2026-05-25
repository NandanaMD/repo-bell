from __future__ import annotations

import logging
from typing import Any

import requests

from app.config.models import RepositoryConfig
from app.github.models import CommitInfo

logger = logging.getLogger(__name__)


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, timeout_seconds: int = 10) -> None:
        self._timeout = timeout_seconds

    def fetch_latest_commits(self, repo: RepositoryConfig, limit: int = 10) -> list[CommitInfo]:
        url = f"{self.BASE_URL}/repos/{repo.owner}/{repo.repo}/commits"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "RepoBell/1.0",
        }
        if repo.token:
            headers["Authorization"] = f"Bearer {repo.token}"

        params = {"per_page": max(1, min(limit, 20))}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=self._timeout)
        except requests.RequestException as exc:
            logger.error("Network error while fetching commits for %s: %s", repo.full_name, exc)
            return []

        if response.status_code == 404:
            logger.error("Repository not found: %s", repo.full_name)
            return []

        if response.status_code == 401 or response.status_code == 403:
            if "rate limit" in response.text.lower():
                logger.error("GitHub rate limit exceeded for %s", repo.full_name)
            else:
                logger.error("Access denied for repository %s", repo.full_name)
            return []

        if not response.ok:
            logger.error(
                "GitHub API error for %s: HTTP %s - %s",
                repo.full_name,
                response.status_code,
                response.text[:300],
            )
            return []

        try:
            payload = response.json()
        except ValueError:
            logger.error("Invalid JSON response from GitHub for %s", repo.full_name)
            return []

        if not isinstance(payload, list):
            logger.error("Unexpected payload type for %s commits", repo.full_name)
            return []

        commits: list[CommitInfo] = []
        for item in payload:
            parsed = self._parse_commit(item)
            if parsed:
                commits.append(parsed)
        return commits

    def _parse_commit(self, item: dict[str, Any]) -> CommitInfo | None:
        sha = str(item.get("sha", "")).strip()
        commit = item.get("commit") or {}
        if not sha or not isinstance(commit, dict):
            return None

        message = str(commit.get("message", "")).split("\n", maxsplit=1)[0].strip()
        author_data = commit.get("author") or {}
        author = str(author_data.get("name") or "unknown")
        timestamp = str(author_data.get("date") or "")
        url = str(item.get("html_url") or "")

        return CommitInfo(
            sha=sha,
            message=message or "(no commit message)",
            url=url,
            author=author,
            timestamp=timestamp,
        )
