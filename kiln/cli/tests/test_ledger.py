import json

import pytest

from kiln import ledger as L


def test_add_and_show(conn):
    idea = L.add(conn, title="Pit Stop Delta", pitch="Compare pit times", status="presented",
                 scores={"novelty": 4}, prior_art={"verdict": "CLEAR", "closest_matches": []})
    assert idea["slug"] == "pit-stop-delta"
    got = L.show(conn, "pit-stop-delta")
    assert got["scores"] == {"novelty": 4}
    assert got["prior_art"]["verdict"] == "CLEAR"


def test_slug_collisions_get_suffix(conn):
    a = L.add(conn, title="Same Name")
    b = L.add(conn, title="Same Name")
    assert (a["slug"], b["slug"]) == ("same-name", "same-name-2")


def test_explicit_slug_updates_in_place(conn):
    L.add(conn, title="Idea", slug="idea-x", status="pool", pitch="first")
    updated = L.add(conn, title="Idea", slug="idea-x", status="presented", prior_art={"verdict": "ADJACENT"})
    assert updated["status"] == "presented"
    assert updated["pitch"] == "first"  # empty pitch does not wipe it
    assert updated["prior_art"]["verdict"] == "ADJACENT"
    assert len(L.list_ideas(conn)) == 1


def test_status_transitions_and_taste(conn):
    L.add(conn, title="Lap Ghost", status="presented")
    L.set_status(conn, "lap-ghost", "rejected", "too close to Garage 61")
    assert L.show(conn, "lap-ghost")["status"] == "rejected"
    assert L.taste(conn)[0]["reason"] == "too close to Garage 61"
    L.set_status(conn, "lap-ghost", "presented")  # revive keeps the old reason
    assert L.show(conn, "lap-ghost")["reason"] == "too close to Garage 61"
    L.set_status(conn, "lap-ghost", "built")
    assert L.list_ideas(conn, "built")[0]["slug"] == "lap-ghost"


def test_bad_status_and_missing(conn):
    with pytest.raises(L.LedgerError):
        L.add(conn, title="x", status="maybe")
    with pytest.raises(L.LedgerError):
        L.show(conn, "nope")
    with pytest.raises(L.LedgerError):
        L.set_status(conn, "nope", "built")


def test_recent_is_compact_and_ordered(conn):
    for t in ("one", "two", "three"):
        L.add(conn, title=t, prior_art={"big": "blob"})
    rows = L.recent(conn, 2)
    assert [r["title"] for r in rows] == ["three", "two"]
    assert "prior_art" not in rows[0]


def test_json_string_inputs_are_validated(conn):
    L.add(conn, title="ok", scores='{"novelty": 3}')
    assert L.show(conn, "ok")["scores"] == {"novelty": 3}
    with pytest.raises(json.JSONDecodeError):
        L.add(conn, title="bad", scores="{not json")


def test_cli_roundtrip(kiln_home):
    from typer.testing import CliRunner

    from kiln.cli import app

    r = CliRunner()
    res = r.invoke(app, ["ledger", "add", "--title", "Docket Bell", "--pitch", "PACER alerts", "--status",
                         "presented", "--json"])
    assert res.exit_code == 0, res.output
    assert json.loads(res.output)["slug"] == "docket-bell"
    res = r.invoke(app, ["ledger", "reject", "docket-bell", "--reason", "needs PACER fees"])
    assert res.exit_code == 0
    res = r.invoke(app, ["ledger", "recent", "--json"])
    assert json.loads(res.output)[0]["status"] == "rejected"
    batch = json.dumps([{"title": "A thing", "status": "killed", "reason": "slop"}, {"title": "B thing"}])
    res = r.invoke(app, ["ledger", "add", "--from-json", batch, "--json"])
    assert res.exit_code == 0, res.output
    assert {i["status"] for i in json.loads(res.output)} == {"killed", "pool"}
