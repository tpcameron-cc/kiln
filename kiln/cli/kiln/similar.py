"""TF-IDF cosine similarity in plain Python, for spotting near-duplicate ideas."""

from __future__ import annotations

import math
import re
from collections import Counter

STOP = set(
    """a an the and or of to in on for with by from at as is are be it its this that these those
    your my our you i we they them their which who what when where how into onto over under than
    then so not no can will just only also very more most less any all each every one two
    tool app build make makes uses using use simple small quick tiny lets let based via""".split()
)
_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    words = [w for w in _WORD.findall(text.lower()) if w not in STOP and len(w) > 1]
    # light stemming so "races"/"racing"/"race" meet
    out = []
    for w in words:
        for suf in ("ing", "ers", "ed", "er", "es", "s"):
            if len(w) - len(suf) >= 3 and w.endswith(suf) and not w.endswith("ss"):
                w = w[: -len(suf)]
                break
        if len(w) > 3 and w.endswith("e"):
            w = w[:-1]
        out.append(w)
    return out


def _vectors(docs: list[list[str]]) -> list[dict[str, float]]:
    n = len(docs)
    df: Counter[str] = Counter()
    for d in docs:
        df.update(set(d))
    vecs = []
    for d in docs:
        tf = Counter(d)
        vec = {t: (c / len(d)) * (math.log((1 + n) / (1 + df[t])) + 1) for t, c in tf.items()} if d else {}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vecs.append({t: v / norm for t, v in vec.items()})
    return vecs


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(t, 0.0) for t, v in a.items())


def rank(query: str, corpus: list[tuple[str, str]], threshold: float = 0.0, limit: int = 10) -> list[tuple[str, float]]:
    """Return (id, score) for corpus entries most similar to `query`.

    `corpus` is a list of (id, text). Scores are TF-IDF cosine in [0, 1].
    """
    if not corpus:
        return []
    docs = [tokenize(text) for _, text in corpus] + [tokenize(query)]
    vecs = _vectors(docs)
    qv = vecs[-1]
    scored = [(cid, round(cosine(qv, v), 3)) for (cid, _), v in zip(corpus, vecs[:-1])]
    scored = [s for s in scored if s[1] >= threshold]
    scored.sort(key=lambda s: -s[1])
    return scored[:limit]
