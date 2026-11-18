"""Lobsters story search. There is no JSON search endpoint, so we parse the HTML."""

from __future__ import annotations

import re

import httpx

from kiln.search.base import Result, SourceError, clean, request

NAME = "lobsters"
BASE = "https://lobste.rs"

_URL = re.compile(r'<a class="u-url" href="([^"]+)"[^>]*>(.*?)</a>', re.S)
_VOTES = re.compile(r'class="upvoter"[^>]*>\s*(-?\d+)\s*<')
_TIME = re.compile(r'<time[^>]*datetime="([^"]+)"')
_TAG = re.compile(r'class="tag tag_[^"]*"[^>]*>([^<]+)<')
_COMMENTS = re.compile(r'href="(/s/\w+/[^"]*)"[^>]*>\s*([^<]*?)\s*</a>', re.S)


def normalize(html: str, limit: int = 15) -> list[Result]:
    out = []
    for chunk in html.split('<li id="story_')[1:]:
        short_id, _, body = chunk.partition('"')
        um = _URL.search(body)
        if not um:
            continue
        url, title = um.group(1), clean(um.group(2))
        if url.startswith("/"):
            url = BASE + url
        votes = _VOTES.search(body)
        when = _TIME.search(body)
        tags = _TAG.findall(body)
        cm = _COMMENTS.search(body)
        discussion = BASE + cm.group(1) if cm else f"{BASE}/s/{short_id}"
        comments = clean(cm.group(2)) if cm else ""
        desc = " · ".join(x for x in ["tags: " + ", ".join(tags) if tags else "", comments] if x)
        out.append(
            Result(
                source=NAME,
                title=title,
                url=url,
                description=desc,
                score=int(votes.group(1)) if votes else None,
                score_label="votes",
                last_updated=when.group(1).replace(" ", "T") + "Z" if when else None,
                extra={"discussion": discussion, "tags": tags},
            )
        )
        if len(out) >= limit:
            break
    return out


async def fetch(client: httpx.AsyncClient, query: str) -> tuple[list[Result], str | None]:
    resp = await request(
        client, "GET", f"{BASE}/search", params={"q": query, "what": "stories", "order": "relevance"}
    )
    if "story_liner" not in resp.text and "No results" not in resp.text and "<ol" not in resp.text:
        raise SourceError("unexpected page layout")
    return normalize(resp.text), "parsed from HTML search page"
