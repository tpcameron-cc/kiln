"""Shared types and HTTP helpers for prior-art sources."""

from __future__ import annotations

import asyncio
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

USER_AGENT = "kiln-cli/0.1 (prior-art search for a local Claude Code plugin)"


@dataclass
class Result:
    source: str
    title: str
    url: str
    description: str = ""
    score: int | None = None          # stars / points / downloads / upvotes
    score_label: str | None = None    # what `score` counts
    last_updated: str | None = None   # ISO 8601
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceReport:
    source: str
    status: str                 # ok | failed | skipped
    count: int = 0
    cached: bool = False
    error: str | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceError(Exception):
    """A source could not be searched. The message is shown to the user."""


class SourceSkipped(Exception):
    """A source is deliberately not searched (e.g. missing optional token)."""


_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def clean(text: str | None, limit: int = 280) -> str:
    """Strip HTML tags, collapse whitespace and trim."""
    if not text:
        return ""
    import html

    out = _WS.sub(" ", html.unescape(_TAG.sub(" ", text))).strip()
    return out if len(out) <= limit else out[: limit - 1].rstrip() + "…"


def iso_from_unix(ts: float | int | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    retries: int = 3,
    max_wait: float = 20.0,
    **kwargs: Any,
) -> httpx.Response:
    """HTTP request with backoff on 429/5xx and on GitHub-style rate limits."""
    delay = 1.5
    last: str = ""
    for attempt in range(retries + 1):
        try:
            resp = await client.request(method, url, **kwargs)
        except httpx.TimeoutException:
            last = "timed out"
        except httpx.HTTPError as exc:
            last = f"network error: {exc.__class__.__name__}"
        else:
            limited = resp.status_code == 429 or (
                resp.status_code == 403 and resp.headers.get("x-ratelimit-remaining") == "0"
            )
            if limited or resp.status_code >= 500:
                wait = _retry_after(resp) or delay
                last = f"HTTP {resp.status_code}" + (" (rate limited)" if limited else "")
                if wait > max_wait or attempt == retries:
                    raise SourceError(f"{last}; retry in ~{int(wait)}s")
                await asyncio.sleep(wait)
                delay *= 2
                continue
            if resp.status_code >= 400:
                raise SourceError(f"HTTP {resp.status_code}")
            return resp
        if attempt < retries:
            await asyncio.sleep(delay)
            delay *= 2
    raise SourceError(last or "request failed")


def _retry_after(resp: httpx.Response) -> float | None:
    ra = resp.headers.get("retry-after")
    if ra and ra.isdigit():
        return float(ra)
    reset = resp.headers.get("x-ratelimit-reset")
    if reset and reset.isdigit():
        return max(0.0, float(reset) - datetime.now(timezone.utc).timestamp()) + 1
    return None


def json_or_fail(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except ValueError as exc:
        raise SourceError("response was not JSON (likely blocked or a challenge page)") from exc
