"""SQLite storage: the idea ledger and the search cache."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from kiln.paths import db_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS ideas (
    slug        TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    pitch       TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL CHECK (status IN
                  ('pool','killed','presented','rejected','briefed','built')),
    reason      TEXT,
    scores      TEXT,          -- JSON object
    prior_art   TEXT,          -- JSON object (scout output)
    theme       TEXT,
    run_id      TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX IF NOT EXISTS ideas_status ON ideas(status);
CREATE INDEX IF NOT EXISTS ideas_created ON ideas(created_at);

CREATE TABLE IF NOT EXISTS search_cache (
    source      TEXT NOT NULL,
    query       TEXT NOT NULL,
    payload     TEXT NOT NULL,  -- JSON list of normalized results
    note        TEXT,
    fetched_at  REAL NOT NULL,
    PRIMARY KEY (source, query)
);

CREATE TABLE IF NOT EXISTS blobs (
    key         TEXT PRIMARY KEY,
    value       BLOB NOT NULL,
    fetched_at  REAL NOT NULL
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn
