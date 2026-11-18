"""GitHub repositories + topics.

Auth order: `gh api` if gh is installed and logged in, else GITHUB_TOKEN, else
unauthenticated (10 search requests/minute, handled with backoff).
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from functools import lru_cache
from typing import Any

import httpx

from kiln.search.base import Result, SourceError, USER_AGENT, clean, json_or_fail, request

NAME = "github"


def normalize_repos(payload: dict[str, Any]) -> list[Result]:
    out = []
    for item in payload.get("items") or []:
        out.append(
            Result(
                source=NAME,
                title=item.get("full_name") or item.get("name") or "",
                url=item.get("html_url") or "",
                description=clean(item.get("description")),
                score=item.get("stargazers_count"),
                score_label="stars",
                last_updated=item.get("pushed_at") or item.get("updated_at"),
                extra={
                    "kind": "repo",
                    "language": item.get("language"),
                    "topics": item.get("topics") or [],
                    "archived": bool(item.get("archived")),
                },
            )
        )
    return out


def normalize_topics(payload: dict[str, Any]) -> list[Result]:
    out = []
    for item in payload.get("items") or []:
        name = item.get("name") or ""
        out.append(
            Result(
                source=NAME,
                title=f"topic: {item.get('display_name') or name}",
                url=f"https://github.com/topics/{name}",
                description=clean(item.get("short_description") or item.get("description")),
                last_updated=item.get("updated_at"),
                extra={"kind": "topic"},
            )
        )
    return out


@lru_cache(maxsize=1)
def gh_available() -> bool:
    if not shutil.which("gh"):
        return False
    try:
        r = subprocess.run(["gh", "auth", "status"], capture_output=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


def _gh_api(path: str, params: dict[str, str]) -> dict[str, Any]:
    args = ["gh", "api", "-X", "GET", path]
    for k, v in params.items():
        args += ["-f", f"{k}={v}"]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=45)
    if r.returncode != 0:
        msg = (r.stderr or r.stdout).strip().splitlines()
        raise SourceError("gh api: " + (msg[-1] if msg else f"exit {r.returncode}"))
    return json.loads(r.stdout)


async def _get(client: httpx.AsyncClient, path: str, params: dict[str, str]) -> tuple[dict, str]:
    if gh_available():
        return await asyncio.to_thread(_gh_api, path, params), "gh api (authenticated)"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
    token = os.environ.get("GITHUB_TOKEN")
    mode = "GITHUB_TOKEN" if token else "unauthenticated"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = await request(client, "GET", f"https://api.github.com/{path}", params=params, headers=headers)
    return json_or_fail(resp), mode


async def fetch(client: httpx.AsyncClient, query: str) -> tuple[list[Result], str | None]:
    repos, mode = await _get(client, "search/repositories", {"q": query, "per_page": "12"})
    results = normalize_repos(repos)
    try:
        topics, _ = await _get(client, "search/topics", {"q": query, "per_page": "3"})
        results = normalize_topics(topics) + results
    except SourceError:
        pass  # topics are a bonus; repos are the real signal
    return results, mode
