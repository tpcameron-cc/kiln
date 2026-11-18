"""Reddit search.

reddit.com's public search.json often answers 403 to clients without OAuth. When
that happens we fall back to the PullPush archive (api.pullpush.io), which mirrors
Reddit submissions, and say so in the source note so the scout can report it.
"""

from __future__ import annotations

from typing import Any

import httpx

from kiln.search.base import Result, SourceError, clean, iso_from_unix, json_or_fail, request

NAME = "reddit"


def _post(d: dict[str, Any]) -> Result:
    permalink = d.get("permalink") or ""
    url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else (d.get("url") or "")
    sub = d.get("subreddit") or ""
    body = clean(d.get("selftext"), 200)
    desc = " · ".join(x for x in [f"r/{sub}" if sub else "", f"{d.get('num_comments') or 0} comments", body] if x)
    return Result(
        source=NAME,
        title=clean(d.get("title"), 200),
        url=url,
        description=desc,
        score=d.get("score"),
        score_label="upvotes",
        last_updated=iso_from_unix(d.get("created_utc")),
        extra={"subreddit": sub, "link": d.get("url")},
    )


def normalize_listing(payload: dict[str, Any]) -> list[Result]:
    """reddit.com/search.json shape: {data: {children: [{data: {...}}]}}"""
    children = ((payload.get("data") or {}).get("children")) or []
    return [_post(c.get("data") or {}) for c in children]


def normalize_pullpush(payload: dict[str, Any]) -> list[Result]:
    """api.pullpush.io shape: {data: [{...}]}"""
    return [_post(d) for d in payload.get("data") or []]


async def fetch(client: httpx.AsyncClient, query: str) -> tuple[list[Result], str | None]:
    try:
        resp = await request(
            client,
            "GET",
            "https://www.reddit.com/search.json",
            params={"q": query, "limit": 15, "sort": "relevance", "type": "link"},
            retries=0,
        )
        return normalize_listing(json_or_fail(resp)), "reddit.com search"
    except SourceError as primary:
        try:
            resp = await request(
                client,
                "GET",
                "https://api.pullpush.io/reddit/search/submission/",
                params={"q": query, "size": 15},
                retries=1,
            )
        except SourceError as fallback:
            raise SourceError(f"reddit.com: {primary}; pullpush: {fallback}") from fallback
        return normalize_pullpush(json_or_fail(resp)), f"via PullPush archive (reddit.com: {primary})"
