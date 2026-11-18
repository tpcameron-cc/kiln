import random

from kiln import ledger as L
from kiln import seeds as S
from kiln import similar


def test_tokenize_stems_and_drops_stopwords():
    assert similar.tokenize("The racing racers and races") == ["rac", "rac", "rac"]
    assert "the" not in similar.tokenize("the tool for the job")


def test_identical_text_scores_one():
    score = similar.rank("iRacing setup diff viewer", [("a", "iRacing setup diff viewer")])[0][1]
    assert abs(score - 1.0) < 1e-6


def test_rank_orders_by_overlap():
    corpus = [
        ("tide", "printable tide chart calendar for surf spots"),
        ("setup", "diff two iRacing car setup files and explain the changes"),
        ("court", "PACER docket alert email digest"),
    ]
    ranked = similar.rank("compare iRacing setups side by side and show what changed", corpus)
    assert ranked[0][0] == "setup"
    assert ranked[0][1] > ranked[1][1]


def test_threshold_filters():
    corpus = [("x", "weather radar for golf"), ("y", "sec edgar insider trades")]
    assert similar.rank("insider trading form 4 filings edgar", corpus, threshold=0.2)[0][0] == "y"
    assert all(s >= 0.2 for _, s in similar.rank("insider trading form 4 filings edgar", corpus, threshold=0.2))


def test_empty_inputs():
    assert similar.rank("anything", []) == []
    assert similar.rank("", [("a", "text")])[0][1] == 0.0


def test_ledger_similar_skips_pool_by_default(conn):
    L.add(conn, title="Setup Diff", pitch="diff two iRacing car setups", status="presented")
    L.add(conn, title="Setup Diff Pool", pitch="diff two iRacing car setups", status="pool")
    hits = L.similar_to(conn, "iRacing setup diff tool", threshold=0.2)
    assert [h["slug"] for h in hits] == ["setup-diff"]
    hits = L.similar_to(conn, "iRacing setup diff tool", threshold=0.2, include_pool=True)
    assert len(hits) == 2


def test_seed_draw_covers_categories(tmp_path):
    for cat in ("data_sources", "forms", "domains"):
        (tmp_path / f"{cat}.txt").write_text("# comment\n" + "\n".join(f"{cat}-{i}" for i in range(5)))
    picks = S.draw(3, rng=random.Random(1), directory=tmp_path)
    assert [p["category"] for p in picks] == ["data_sources", "forms", "domains"]
    picks = S.draw(20, rng=random.Random(1), directory=tmp_path)
    assert len(picks) == 15  # never repeats; stops when pools run dry
    assert len({p["seed"] for p in picks}) == 15
    picks = S.draw(4, categories=["forms"], rng=random.Random(2), directory=tmp_path)
    assert all(p["category"] == "forms" for p in picks)
