"""PyPI.

PyPI has no public search API and its HTML search page sits behind a bot
challenge. Instead we download the simple index once a week (~45 MB JSON of
every project name), keep the names compressed in SQLite, match query tokens
against project names, then fetch each top match's JSON metadata for a summary.
This only finds projects whose *names* fit the query, and the source note says so.
"""

from __future__ import annotations

import asyncio
import re
import time
import zlib
from typing import Any

import httpx

from kiln.db import connect
from kiln.search.base import Result, SourceError, clean, json_or_fail, request

NAME = "pypi"
INDEX_TTL = 7 * 24 * 3600
STOP = {
    "a", "an", "the", "for", "of", "to", "and", "or", "in", "on", "with", "tool", "app",
    "my", "your", "by", "from", "that", "is", "it", "py", "python",
}
_SPLIT = re.compile(r"[^a-z0-9]+")


def tokens(text: str) -> list[str]:
    return [t for t in _SPLIT.split(text.lower()) if len(t) >= 3 and t not in STOP]


def match_names(names: list[str], query: str, limit: int = 8) -> list[str]:
    """Rank project names by how many query tokens they contain.

    A name token that equals a query token counts 2, one that merely contains
    it counts 1. Names need at least one exact token hit. Ties go to the
    name with the most hits relative to its length (tighter names first).
    """
    q = tokens(query)
    if not q:
        return []
    scored: list[tuple[float, str]] = []
    qset = set(q)
    for name in names:
        low = name.lower()
        if not any(t in low for t in qset):
            continue
        parts = [p for p in _SPLIT.split(low) if p]
        exact = sum(1 for t in qset if t in parts)
        if exact == 0:
            continue
        partial = sum(1 for t in qset if t not in parts and t in low)
        score = 2 * exact + partial - 0.01 * max(0, len(parts) - exact)
        scored.append((score, name))
    scored.sort(key=lambda s: (-s[0], len(s[1])))
    return [n for _, n in scored[:limit]]


def normalize_project(payload: dict[str, Any]) -> Result:
    info = payload.get("info") or {}
    urls = payload.get("urls") or []
    uploaded = max((u.get("upload_time_iso_8601") or "" for u in urls), default="") or None
    links = info.get("project_urls") or {}
    return Result(
        source=NAME,
        title=info.get("name") or "",
        url=info.get("package_url") or info.get("project_url") or "",
        description=clean(info.get("summary")),
        last_updated=uploaded,
        extra={"version": info.get("version"), "homepage": info.get("home_page") or next(iter(links.values()), None)},
    )


async def _names(client: httpx.AsyncClient) -> list[str]:
    conn = connect()
    row = conn.execute("SELECT value, fetched_at FROM blobs WHERE key='pypi_names'").fetchone()
    if row and time.time() - row["fetched_at"] < INDEX_TTL:
        return zlib.decompress(row["value"]).decode().split("\n")
    resp = await request(
        client,
        "GET",
        "https://pypi.org/simple/",
        headers={"Accept": "application/vnd.pypi.simple.v1+json"},
        timeout=180,
        retries=1,
    )
    data = json_or_fail(resp)
    names = [p["name"] for p in data.get("projects") or [] if p.get("name")]
    if not names:
        raise SourceError("simple index returned no projects")
    conn.execute(
        "INSERT OR REPLACE INTO blobs(key, value, fetched_at) VALUES ('pypi_names', ?, ?)",
        (zlib.compress("\n".join(names).encode(), 6), time.time()),
    )
    conn.commit()
    return names


async def fetch(client: httpx.AsyncClient, query: str) -> tuple[list[Result], str | None]:
    names = await _names(client)
    picks = match_names(names, query)

    async def one(name: str) -> Result | None:
        try:
            resp = await request(client, "GET", f"https://pypi.org/pypi/{name}/json", retries=1)
            return normalize_project(json_or_fail(resp))
        except SourceError:
            return None

    results = [r for r in await asyncio.gather(*(one(n) for n in picks)) if r]
    return results, f"name match over {len(names):,} projects (PyPI has no search API)"
