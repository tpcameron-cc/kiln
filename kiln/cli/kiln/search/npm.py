"""npm registry search."""

from __future__ import annotations

from typing import Any

import httpx

from kiln.search.base import Result, clean, json_or_fail, request

NAME = "npm"


def normalize(payload: dict[str, Any]) -> list[Result]:
    out = []
    for obj in payload.get("objects") or []:
        pkg = obj.get("package") or {}
        name = pkg.get("name") or ""
        links = pkg.get("links") or {}
        downloads = (obj.get("downloads") or {}).get("weekly")
        out.append(
            Result(
                source=NAME,
                title=name,
                url=links.get("npm") or f"https://www.npmjs.com/package/{name}",
                description=clean(pkg.get("description")),
                score=downloads,
                score_label="weekly downloads" if downloads is not None else None,
                last_updated=obj.get("updated") or pkg.get("date"),
                extra={"repository": links.get("repository"), "keywords": pkg.get("keywords") or []},
            )
        )
    return out


async def fetch(client: httpx.AsyncClient, query: str) -> tuple[list[Result], str | None]:
    resp = await request(
        client, "GET", "https://registry.npmjs.org/-/v1/search", params={"text": query, "size": 12}
    )
    return normalize(json_or_fail(resp)), None
