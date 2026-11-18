"""Normalizers against recorded responses (no network)."""

import re

from kiln.search import crates, github, hn, lobsters, npm, producthunt, pypi, reddit

ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T")


def _common(results, source):
    assert results, f"{source}: no results parsed"
    for r in results:
        assert r.source == source
        assert r.title.strip()
        assert r.url.startswith("https://") or r.url.startswith("http://")
        assert r.last_updated is None or ISO.match(r.last_updated)
        assert "<" not in r.description  # html stripped


def test_github_repos(fixture_json):
    res = github.normalize_repos(fixture_json("github_repos.json"))
    _common(res, "github")
    assert all(r.score_label == "stars" and isinstance(r.score, int) for r in res)
    assert all("/" in r.title for r in res)  # owner/name
    assert res[0].extra["kind"] == "repo"


def test_github_topics(fixture_json):
    res = github.normalize_topics(fixture_json("github_topics.json"))
    _common(res, "github")
    assert res[0].url.startswith("https://github.com/topics/")
    assert res[0].title.startswith("topic: ")


def test_hn_show_first_and_dedupe(fixture_json):
    show = hn.normalize(fixture_json("hn_show.json"))
    story = hn.normalize(fixture_json("hn_story.json"))
    _common(show + story, "hn")
    assert all(r.extra["show_hn"] for r in show)
    merged = hn.merge(show, story)
    # all Show HN posts come before any plain story
    flags = [r.extra["show_hn"] for r in merged]
    assert flags == sorted(flags, reverse=True)
    # Show HN posts also appear in the story feed; merge must de-dupe them
    keys = [r.extra["hn_url"] for r in merged]
    assert len(keys) == len(set(keys))
    assert all(r.score_label == "points" for r in merged)


def test_npm(fixture_json):
    res = npm.normalize(fixture_json("npm.json"))
    _common(res, "npm")
    assert res[0].url.startswith("https://www.npmjs.com/package/")
    assert res[0].score_label == "weekly downloads"


def test_crates(fixture_json):
    res = crates.normalize(fixture_json("crates.json"))
    _common(res, "crates")
    assert res[0].url.startswith("https://crates.io/crates/")
    assert isinstance(res[0].score, int)


def test_lobsters_html(fixture_text):
    res = lobsters.normalize(fixture_text("lobsters.html"))
    _common(res, "lobsters")
    assert res[0].title == "Telemetry in Go 1.23 and beyond"
    assert res[0].url == "https://go.dev/blog/gotelemetry"
    assert res[0].score == 3
    assert res[0].extra["tags"] == ["go"]
    assert res[0].extra["discussion"].startswith("https://lobste.rs/s/")


def test_reddit_listing(fixture_json):
    res = reddit.normalize_listing(fixture_json("reddit_listing.json"))
    _common(res, "reddit")
    assert res[0].url.startswith("https://www.reddit.com/r/iRacing/")
    assert res[0].description.startswith("r/iRacing · 57 comments")
    assert "throttle & brake" in res[0].description
    assert res[0].last_updated == "2024-11-07T17:20:00Z"


def test_reddit_pullpush(fixture_json):
    res = reddit.normalize_pullpush(fixture_json("reddit_pullpush.json"))
    _common(res, "reddit")
    assert all(r.extra["subreddit"] for r in res)


def test_pypi_project(fixture_json):
    r = pypi.normalize_project(fixture_json("pypi_project.json"))
    assert r.source == "pypi"
    assert r.title.lower() == "pyirsdk"
    assert r.url.startswith("https://pypi.org/project/")
    assert r.description


def test_pypi_name_matching():
    names = ["irsdk", "pyirsdk", "iracing-telemetry", "telemetry", "racing", "opentelemetry-api", "requests"]
    picks = pypi.match_names(names, "iracing telemetry tool")
    assert picks[0] == "iracing-telemetry"  # both tokens exact
    assert "requests" not in picks
    assert pypi.match_names(names, "the a of") == []


def test_producthunt(fixture_json):
    res = producthunt.normalize_posts(fixture_json("producthunt_posts.json"), "Sim racing")
    _common(res, "producthunt")
    assert res[0].score == 321
    assert res[0].description.endswith("topic: Sim racing")
