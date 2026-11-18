"""Product Hunt (only when PRODUCT_HUNT_TOKEN is set).

The v2 GraphQL API has no free-text post search, so we look up the topics that
match the query and list the top-voted posts in the best matching topics.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from kiln.search.base import Result, SourceError, SourceSkipped, clean, json_or_fail, request

NAME = "producthunt"
API = "https://api.producthunt.com/v2/api/graphql"

TOPICS_Q = """query($q: String!) { topics(query: $q, first: 2) { edges { node { slug name } } } }"""
POSTS_Q = """query($t: String!) { posts(topic: $t, order: VOTES, first: 10) {
  edges { node { name tagline url website votesCount createdAt } } } }"""


def normalize_posts(payload: dict[str, Any], topic: str = "") -> list[Result]:
    edges = (((payload.get("data") or {}).get("posts") or {}).get("edges")) or []
    out = []
    for e in edges:
        n = e.get("node") or {}
        out.append(
            Result(
                source=NAME,
                title=n.get("name") or "",
                url=n.get("url") or "",
                description=clean(n.get("tagline")) + (f" · topic: {topic}" if topic else ""),
                score=n.get("votesCount"),
                score_label="votes",
                last_updated=n.get("createdAt"),
                extra={"website": n.get("website")},
            )
        )
    return out


async def fetch(client: httpx.AsyncClient, query: str) -> tuple[list[Result], str | None]:
    token = os.environ.get("PRODUCT_HUNT_TOKEN")
    if not token:
        raise SourceSkipped("PRODUCT_HUNT_TOKEN not set")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def gql(q: str, variables: dict[str, Any]) -> dict[str, Any]:
        resp = await request(client, "POST", API, json={"query": q, "variables": variables}, headers=headers)
        data = json_or_fail(resp)
        if data.get("errors"):
            raise SourceError(str(data["errors"][0].get("message", "GraphQL error")))
        return data

    topics = await gql(TOPICS_Q, {"q": query})
    slugs = [
        (e["node"]["slug"], e["node"]["name"])
        for e in ((topics.get("data") or {}).get("topics") or {}).get("edges") or []
    ]
    results: list[Result] = []
    for slug, name in slugs:
        results += normalize_posts(await gql(POSTS_Q, {"t": slug}), name)
    return results, "top posts in matching topics (no free-text search in PH API)"
