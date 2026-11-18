"""Random ingredient draws from data/seeds/*.txt."""

from __future__ import annotations

import random
from pathlib import Path

from kiln.paths import seeds_dir

ORDER = ["data_sources", "forms", "domains", "constraints", "formats", "odd_angles"]


def load(directory: Path | None = None) -> dict[str, list[str]]:
    d = directory or seeds_dir()
    if not d.is_dir():
        raise FileNotFoundError(f"seed directory not found: {d} (set KILN_SEEDS_DIR)")
    out: dict[str, list[str]] = {}
    for f in sorted(d.glob("*.txt")):
        lines = [
            ln.strip()
            for ln in f.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        ]
        out[f.stem] = lines
    return out


def draw(
    n: int = 6,
    categories: list[str] | None = None,
    rng: random.Random | None = None,
    directory: Path | None = None,
) -> list[dict[str, str]]:
    """Draw n ingredients.

    With categories given, draw round-robin from those. Otherwise cover each
    category once (in ORDER) before repeating any, so n=6 gives one of each.
    Never returns the same entry twice.
    """
    rng = rng or random.SystemRandom()
    pools = load(directory)
    cats = categories or [c for c in ORDER if c in pools] + [c for c in pools if c not in ORDER]
    missing = [c for c in cats if c not in pools]
    if missing:
        raise KeyError(f"unknown category: {', '.join(missing)}; have {', '.join(pools)}")
    remaining = {c: rng.sample(pools[c], len(pools[c])) for c in cats}
    picks: list[dict[str, str]] = []
    i = 0
    while len(picks) < n and any(remaining.values()):
        cat = cats[i % len(cats)]
        if remaining[cat]:
            picks.append({"category": cat, "seed": remaining[cat].pop()})
        i += 1
    return picks
