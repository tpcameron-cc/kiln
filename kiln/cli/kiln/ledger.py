"""The idea ledger: every idea Kiln has pooled, killed, presented, briefed or built."""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from kiln import similar

STATUSES = ("pool", "killed", "presented", "rejected", "briefed", "built")
_SLUG = re.compile(r"[^a-z0-9]+")


class LedgerError(Exception):
    pass


def slugify(text: str, max_len: int = 48) -> str:
    s = _SLUG.sub("-", text.lower()).strip("-")
    return s[:max_len].rstrip("-") or "idea"


def _unique_slug(conn: sqlite3.Connection, base: str) -> str:
    slug, i = base, 2
    while conn.execute("SELECT 1 FROM ideas WHERE slug=?", (slug,)).fetchone():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _row(r: sqlite3.Row) -> dict[str, Any]:
    d = dict(r)
    for k in ("scores", "prior_art"):
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except ValueError:
                pass
    return d


def _as_json(v: Any) -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, str):
        json.loads(v)  # validate
        return v
    return json.dumps(v)


def add(
    conn: sqlite3.Connection,
    *,
    title: str,
    pitch: str = "",
    status: str = "pool",
    reason: str | None = None,
    scores: Any = None,
    prior_art: Any = None,
    theme: str | None = None,
    run_id: str | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    if status not in STATUSES:
        raise LedgerError(f"status must be one of {', '.join(STATUSES)}")
    if not title.strip():
        raise LedgerError("title is required")
    base = slugify(slug or title)
    existing = conn.execute("SELECT slug FROM ideas WHERE slug=?", (base,)).fetchone()
    if slug and existing:
        # explicit slug: update in place (pipeline logs the same idea at several stages)
        conn.execute(
            """UPDATE ideas SET title=?, pitch=COALESCE(NULLIF(?, ''), pitch), status=?,
               reason=COALESCE(?, reason), scores=COALESCE(?, scores), prior_art=COALESCE(?, prior_art),
               theme=COALESCE(?, theme), run_id=COALESCE(?, run_id),
               updated_at=strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE slug=?""",
            (title, pitch, status, reason, _as_json(scores), _as_json(prior_art), theme, run_id, base),
        )
        conn.commit()
        return show(conn, base)
    final = _unique_slug(conn, base)
    conn.execute(
        """INSERT INTO ideas(slug, title, pitch, status, reason, scores, prior_art, theme, run_id)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (final, title, pitch, status, reason, _as_json(scores), _as_json(prior_art), theme, run_id),
    )
    conn.commit()
    return show(conn, final)


def show(conn: sqlite3.Connection, slug: str) -> dict[str, Any]:
    r = conn.execute("SELECT * FROM ideas WHERE slug=?", (slug,)).fetchone()
    if not r:
        raise LedgerError(f"no idea with slug '{slug}'")
    return _row(r)


def list_ideas(conn: sqlite3.Connection, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    if status:
        rows = conn.execute(
            "SELECT * FROM ideas WHERE status=? ORDER BY created_at DESC, rowid DESC LIMIT ?", (status, limit)
        )
    else:
        rows = conn.execute("SELECT * FROM ideas ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,))
    return [_row(r) for r in rows]


def recent(conn: sqlite3.Connection, n: int = 30) -> list[dict[str, Any]]:
    """Compact view for loading context: no prior-art blobs."""
    rows = conn.execute(
        "SELECT slug, title, pitch, status, reason, created_at FROM ideas ORDER BY created_at DESC, rowid DESC LIMIT ?",
        (n,),
    )
    return [dict(r) for r in rows]


def set_status(conn: sqlite3.Connection, slug: str, status: str, reason: str | None = None) -> dict[str, Any]:
    if status not in STATUSES:
        raise LedgerError(f"status must be one of {', '.join(STATUSES)}")
    show(conn, slug)
    conn.execute(
        "UPDATE ideas SET status=?, reason=COALESCE(?, reason), updated_at=strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE slug=?",
        (status, reason, slug),
    )
    conn.commit()
    return show(conn, slug)


def similar_to(
    conn: sqlite3.Connection, text: str, threshold: float = 0.3, limit: int = 5, include_pool: bool = False
) -> list[dict[str, Any]]:
    q = "SELECT slug, title, pitch, status, reason FROM ideas"
    if not include_pool:
        q += " WHERE status != 'pool'"
    rows = [dict(r) for r in conn.execute(q)]
    corpus = [(r["slug"], f"{r['title']} {r['title']} {r['pitch']}") for r in rows]
    by_slug = {r["slug"]: r for r in rows}
    return [
        {**by_slug[slug], "similarity": score}
        for slug, score in similar.rank(text, corpus, threshold=threshold, limit=limit)
    ]


def taste(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT slug, title, reason, updated_at FROM ideas WHERE status='rejected' AND reason IS NOT NULL ORDER BY updated_at DESC"
    )
    return [dict(r) for r in rows]
