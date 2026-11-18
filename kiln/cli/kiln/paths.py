"""Where Kiln keeps things.

Per-user state lives in ~/.kiln (override with KILN_HOME). Seed lists ship with
the plugin in <plugin>/data/seeds (override with KILN_SEEDS_DIR).
"""

from __future__ import annotations

import os
from pathlib import Path


def kiln_home() -> Path:
    home = Path(os.environ.get("KILN_HOME") or Path.home() / ".kiln")
    home.mkdir(parents=True, exist_ok=True)
    (home / "briefs").mkdir(exist_ok=True)
    return home


def db_path() -> Path:
    return kiln_home() / "kiln.db"


def profile_path() -> Path:
    return kiln_home() / "profile.md"


def briefs_dir() -> Path:
    return kiln_home() / "briefs"


def seeds_dir() -> Path:
    env = os.environ.get("KILN_SEEDS_DIR")
    if env:
        return Path(env)
    # cli/kiln/paths.py -> plugin root is three levels up from this file's folder
    return Path(__file__).resolve().parents[2] / "data" / "seeds"
