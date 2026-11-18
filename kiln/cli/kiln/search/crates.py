"""crates.io search."""

from __future__ import annotations

from typing import Any

import httpx

from kiln.search.base import Result, clean, json_or_fail, request

NAME = "crates"


def normalize(payload: dict[str, Any]) -> list[Result]:
    out = []
    for c in payload.get("crates") or []:
        cid = c.get("id") or c.get("name") or ""
        out.append(
            Result(
                source=NAME,
                title=c.get("name") or cid,
                url=f"https://crates.io/crates/{cid}",
                description=clean(c.get("description")),
                score=c.get("downloads"),
                score_label="downloads",
                last_updated=c.get("updated_at"),
                extra={"repository": c.get("repository"), "recent_downloads": c.get("recent_downloads")},
            )
        )
    return out


async def fetch(client: httpx.AsyncClient, query: str) -> tuple[list[Result], str | None]:
    resp = await request(
        client, "GET", "https://crates.io/api/v1/crates", params={"q": query, "per_page": 10}
    )
    return normalize(json_or_fail(resp)), None
