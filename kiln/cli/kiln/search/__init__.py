"""Run a query across every prior-art source in parallel, with a 7-day cache."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import httpx

from kiln.db import connect
from kiln.search import crates, github, hn, lobsters, npm, producthunt, pypi, reddit
from kiln.search.base import USER_AGENT, Result, SourceError, SourceReport, SourceSkipped

SOURCES = {
    m.NAME: m for m in (github, hn, npm, pypi, crates, reddit, lobsters, producthunt)
}
CACHE_TTL = 7 * 24 * 3600
SOURCE_TIMEOUT = 200  # pypi's first index download is the slow one


def _key(query: str) -> str:
    return " ".join(query.lower().split())


async def _run_one(client: httpx.AsyncClient, name: str, query: str) -> tuple[SourceReport, list[Result]]:
    mod = SOURCES[name]
    try:
        results, note = await asyncio.wait_for(mod.fetch(client, query), SOURCE_TIMEOUT)
    except SourceSkipped as exc:
        return SourceReport(name, "skipped", note=str(exc)), []
    except SourceError as exc:
        return SourceReport(name, "failed", error=str(exc)), []
    except asyncio.TimeoutError:
        return SourceReport(name, "failed", error=f"timed out after {SOURCE_TIMEOUT}s"), []
    except Exception as exc:  # a broken source must never sink the whole search
        return SourceReport(name, "failed", error=f"{exc.__class__.__name__}: {exc}"), []
    return SourceReport(name, "ok", count=len(results), note=note), results


async def _search(query: str, names: list[str], use_cache: bool) -> dict[str, Any]:
    conn = connect()
    key = _key(query)
    reports: dict[str, SourceReport] = {}
    results: dict[str, list[Result]] = {}
    todo: list[str] = []
    now = time.time()
    for name in names:
        row = conn.execute(
            "SELECT payload, note, fetched_at FROM search_cache WHERE source=? AND query=?", (name, key)
        ).fetchone()
        if use_cache and row and now - row["fetched_at"] < CACHE_TTL:
            items = [Result(**d) for d in json.loads(row["payload"])]
            results[name] = items
            reports[name] = SourceReport(name, "ok", count=len(items), cached=True, note=row["note"])
        else:
            todo.append(name)

    if todo:
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=25, follow_redirects=True
        ) as client:
            done = await asyncio.gather(*(_run_one(client, n, query) for n in todo))
        for name, (report, items) in zip(todo, done):
            reports[name], results[name] = report, items
            if report.status == "ok":  # never cache failures
                conn.execute(
                    "INSERT OR REPLACE INTO search_cache(source, query, payload, note, fetched_at) VALUES (?,?,?,?,?)",
                    (name, key, json.dumps([r.to_dict() for r in items]), report.note, time.time()),
                )
        conn.commit()

    ordered = [reports[n] for n in names]
    return {
        "query": query,
        "sources": [r.to_dict() for r in ordered],
        "summary": {
            "ok": [r.source for r in ordered if r.status == "ok"],
            "failed": [r.source for r in ordered if r.status == "failed"],
            "skipped": [r.source for r in ordered if r.status == "skipped"],
        },
        "results": [r.to_dict() for n in names for r in results.get(n, [])],
    }


def search(query: str, sources: list[str] | None = None, use_cache: bool = True) -> dict[str, Any]:
    names = sources or list(SOURCES)
    unknown = [n for n in names if n not in SOURCES]
    if unknown:
        raise ValueError(f"unknown source(s): {', '.join(unknown)}; choose from {', '.join(SOURCES)}")
    return asyncio.run(_search(query, names, use_cache))
