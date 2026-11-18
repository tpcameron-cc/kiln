"""Hacker News via the Algolia API. Show HN posts are ranked first."""

from __future__ import annotations

from typing import Any

import httpx

from kiln.search.base import Result, clean, json_or_fail, request

NAME = "hn"
API = "https://hn.algolia.com/api/v1/search"


def normalize(payload: dict[str, Any]) -> list[Result]:
    out = []
    for hit in payload.get("hits") or []:
        oid = hit.get("objectID")
        hn_url = f"https://news.ycombinator.com/item?id={oid}"
        title = hit.get("title") or hit.get("story_title") or ""
        tags = hit.get("_tags") or []
        show = "show_hn" in tags or title.lower().startswith("show hn")
        snippet = clean(hit.get("story_text"), 220)
        bits = ["Show HN" if show else "HN story", f"{hit.get('num_comments') or 0} comments"]
        if snippet:
            bits.append(snippet)
        out.append(
            Result(
                source=NAME,
                title=title,
                url=hit.get("url") or hn_url,
                description=" · ".join(bits),
                score=hit.get("points"),
                score_label="points",
                last_updated=hit.get("created_at"),
                extra={"show_hn": show, "hn_url": hn_url},
            )
        )
    return out


def merge(show: list[Result], stories: list[Result], limit: int = 15) -> list[Result]:
    """Show HN first (by points), then other stories, de-duplicated."""
    seen: set[str] = set()
    out: list[Result] = []
    ranked = sorted(show, key=lambda r: -(r.score or 0)) + sorted(stories, key=lambda r: -(r.score or 0))
    for r in ranked:
        key = r.extra.get("hn_url", r.url)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out[:limit]


async def fetch(client: httpx.AsyncClient, query: str) -> tuple[list[Result], str | None]:
    show = await request(client, "GET", API, params={"query": query, "tags": "show_hn", "hitsPerPage": 10})
    stories = await request(client, "GET", API, params={"query": query, "tags": "story", "hitsPerPage": 15})
    return merge(normalize(json_or_fail(show)), normalize(json_or_fail(stories))), None
