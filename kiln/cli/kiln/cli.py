"""`kiln` command line."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from kiln import __version__, ledger as L
from kiln import profile as P
from kiln import seeds as S
from kiln.db import connect
from kiln.paths import briefs_dir, db_path, kiln_home, profile_path, seeds_dir

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    except (AttributeError, ValueError):
        pass

app = typer.Typer(help="Kiln: prior-art search, seed draws and the idea ledger.", no_args_is_help=True)
ledger_app = typer.Typer(help="The idea ledger (~/.kiln/kiln.db).", no_args_is_help=True)
profile_app = typer.Typer(help="Your taste profile (~/.kiln/profile.md).", no_args_is_help=True)
app.add_typer(ledger_app, name="ledger")
app.add_typer(profile_app, name="profile")

out = Console(soft_wrap=True)
err = Console(stderr=True)


def _emit_json(data: Any) -> None:
    sys.stdout.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _fail(msg: str, code: int = 1) -> None:
    err.print(f"[red]error:[/red] {escape(msg)}")
    raise typer.Exit(code)


def _load_json_arg(value: Optional[str]) -> Any:
    """Accept inline JSON, @path/to/file.json, or '-' for stdin."""
    if value is None:
        return None
    if value == "-":
        return json.loads(sys.stdin.read())
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    return json.loads(value)


@app.callback(invoke_without_command=True)
def main(version: bool = typer.Option(False, "--version", help="Show version and exit.")) -> None:
    if version:
        out.print(f"kiln {__version__}")
        raise typer.Exit()


@app.command()
def home(as_json: bool = typer.Option(False, "--json")) -> None:
    """Show where Kiln keeps its files (creates ~/.kiln if needed)."""
    info = {
        "home": str(kiln_home()),
        "db": str(db_path()),
        "profile": str(profile_path()),
        "profile_exists": profile_path().exists(),
        "briefs": str(briefs_dir()),
        "seeds": str(seeds_dir()),
    }
    connect().close()
    if as_json:
        _emit_json(info)
    else:
        for k, v in info.items():
            out.print(f"[bold]{k:>14}[/bold]  {escape(str(v))}")


# ---------------------------------------------------------------- search


@app.command()
def search(
    query: str = typer.Argument(..., help="What to look for."),
    sources: Optional[str] = typer.Option(
        None, "--sources", "-s", help="Comma list: github,hn,npm,pypi,crates,reddit,lobsters,producthunt"
    ),
    as_json: bool = typer.Option(False, "--json", help="Machine-readable output."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Ignore the 7-day cache."),
    per_source: int = typer.Option(6, "--per-source", "-k", help="Rows per source in table view."),
) -> None:
    """Search every prior-art source in parallel. Failed sources are always listed."""
    from kiln.search import search as run

    names = [s.strip() for s in sources.split(",") if s.strip()] if sources else None
    try:
        data = run(query, names, use_cache=not no_cache)
    except ValueError as exc:
        _fail(str(exc))
        return
    if as_json:
        _emit_json(data)
        return

    status = Table(title=f'Sources for "{escape(query)}"', show_lines=False)
    for col in ("source", "status", "results", "note"):
        status.add_column(col)
    for s in data["sources"]:
        colour = {"ok": "green", "failed": "red", "skipped": "yellow"}[s["status"]]
        label = s["status"].upper() + (" (cached)" if s["cached"] else "")
        status.add_row(
            s["source"], f"[{colour}]{label}[/{colour}]", str(s["count"]), escape(s["error"] or s["note"] or "")
        )
    out.print(status)

    by_source: dict[str, list[dict]] = {}
    for r in data["results"]:
        by_source.setdefault(r["source"], []).append(r)
    for name, rows in by_source.items():
        out.print(f"\n[bold underline]{name}[/bold underline]")
        for r in rows[:per_source]:
            metric = f" [dim]({r['score']} {r['score_label']})[/dim]" if r["score"] is not None else ""
            out.print(f"• [bold]{escape(r['title'])}[/bold]{metric}  {escape(r['url'])}")
            if r["description"]:
                out.print(f"  [dim]{escape(r['description'][:200])}[/dim]")
    s = data["summary"]
    out.print(
        f"\n[green]{len(s['ok'])} ok[/green] · [red]{len(s['failed'])} failed[/red]"
        f"{' (' + ', '.join(s['failed']) + ')' if s['failed'] else ''} · "
        f"[yellow]{len(s['skipped'])} skipped[/yellow] · {len(data['results'])} results"
    )


# ---------------------------------------------------------------- seeds


@app.command()
def seeds(
    n: int = typer.Option(6, "--n", help="How many ingredients to draw."),
    category: Optional[list[str]] = typer.Option(None, "--category", "-c", help="Limit to category (repeatable)."),
    as_json: bool = typer.Option(False, "--json"),
    list_categories: bool = typer.Option(False, "--list", help="List categories and sizes."),
) -> None:
    """Random ingredients to knock idea generation off its usual rails."""
    try:
        if list_categories:
            pools = S.load()
            if as_json:
                _emit_json({k: len(v) for k, v in pools.items()})
            else:
                for k, v in pools.items():
                    out.print(f"{k:>14}  {len(v)} entries")
            return
        picks = S.draw(n, category or None)
    except (FileNotFoundError, KeyError) as exc:
        _fail(str(exc).strip("'\""))
        return
    if as_json:
        _emit_json(picks)
    else:
        for p in picks:
            out.print(f"[bold]{p['category']:>14}[/bold]  {escape(p['seed'])}")


# ---------------------------------------------------------------- ledger


def _print_ideas(rows: list[dict], as_json: bool) -> None:
    if as_json:
        _emit_json(rows)
        return
    if not rows:
        out.print("[dim]ledger is empty[/dim]")
        return
    t = Table()
    for col in ("slug", "status", "title", "reason", "created"):
        t.add_column(col, overflow="fold")
    for r in rows:
        t.add_row(r["slug"], r["status"], escape(r["title"]), escape(r.get("reason") or ""), r["created_at"][:10])
    out.print(t)


@ledger_app.command("add")
def ledger_add(
    title: Optional[str] = typer.Option(None, "--title"),
    pitch: str = typer.Option("", "--pitch"),
    status: str = typer.Option("pool", "--status", help="pool|killed|presented|rejected|briefed|built"),
    reason: Optional[str] = typer.Option(None, "--reason", help="Why it was killed/rejected."),
    scores: Optional[str] = typer.Option(None, "--scores", help="JSON, @file or -"),
    prior_art: Optional[str] = typer.Option(None, "--prior-art", help="Scout JSON, @file or -"),
    theme: Optional[str] = typer.Option(None, "--theme"),
    run_id: Optional[str] = typer.Option(None, "--run-id"),
    slug: Optional[str] = typer.Option(None, "--slug", help="Explicit slug; updates the idea if it exists."),
    from_json: Optional[str] = typer.Option(
        None, "--from-json", help="Add many: JSON list (or one object) of ideas, @file or -"
    ),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Add an idea (or a batch with --from-json). Re-adding an explicit slug updates it."""
    conn = connect()
    try:
        if from_json:
            items = _load_json_arg(from_json)
            items = items if isinstance(items, list) else [items]
            added = []
            for it in items:
                if "prior_art" in it and isinstance(it["prior_art"], str) and it["prior_art"].startswith("@"):
                    it["prior_art"] = _load_json_arg(it["prior_art"])
                added.append(
                    L.add(
                        conn,
                        **{k: it.get(k) for k in ("title", "reason", "scores", "prior_art", "theme", "run_id", "slug")},
                        pitch=it.get("pitch") or "",
                        status=it.get("status") or "pool",
                    )
                )
            _print_ideas(added, as_json)
            return
        if not title:
            _fail("--title is required (or use --from-json)")
        idea = L.add(
            conn,
            title=title,
            pitch=pitch,
            status=status,
            reason=reason,
            scores=_load_json_arg(scores),
            prior_art=_load_json_arg(prior_art),
            theme=theme,
            run_id=run_id,
            slug=slug,
        )
    except (L.LedgerError, json.JSONDecodeError, OSError) as exc:
        _fail(str(exc))
        return
    if as_json:
        _emit_json(idea)
    else:
        out.print(f"added [bold]{idea['slug']}[/bold] ({idea['status']})")


@ledger_app.command("recent")
def ledger_recent(n: int = typer.Option(30, "--n"), as_json: bool = typer.Option(False, "--json")) -> None:
    """Most recent ideas, compact (no prior-art blobs)."""
    _print_ideas(L.recent(connect(), n), as_json)


@ledger_app.command("list")
def ledger_list(
    status: Optional[str] = typer.Option(None, "--status"),
    limit: int = typer.Option(50, "--limit"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """List ideas, optionally by status."""
    _print_ideas(L.list_ideas(connect(), status, limit), as_json)


@ledger_app.command("show")
def ledger_show(slug: str, as_json: bool = typer.Option(False, "--json")) -> None:
    """Everything stored for one idea, including prior-art evidence."""
    try:
        idea = L.show(connect(), slug)
    except L.LedgerError as exc:
        _fail(str(exc))
        return
    if as_json:
        _emit_json(idea)
        return
    out.print(f"[bold]{escape(idea['title'])}[/bold]  [dim]{idea['slug']} · {idea['status']} · {idea['created_at']}[/dim]")
    if idea["pitch"]:
        out.print(escape(idea["pitch"]))
    if idea.get("reason"):
        out.print(f"[yellow]reason:[/yellow] {escape(idea['reason'])}")
    if idea.get("scores"):
        out.print(f"[cyan]scores:[/cyan] {escape(json.dumps(idea['scores']))}")
    pa = idea.get("prior_art")
    if isinstance(pa, dict):
        out.print(f"[cyan]prior art:[/cyan] {pa.get('verdict')} ({pa.get('confidence')} confidence)")
        for m in pa.get("closest_matches") or []:
            out.print(f"  • {escape(str(m.get('name')))} {escape(str(m.get('url')))}")
            if m.get("how_it_differs"):
                out.print(f"    [dim]{escape(str(m['how_it_differs']))}[/dim]")


def _status_cmd(slug: str, status: str, reason: Optional[str], as_json: bool) -> None:
    try:
        idea = L.set_status(connect(), slug, status, reason)
    except L.LedgerError as exc:
        _fail(str(exc))
        return
    if as_json:
        _emit_json(idea)
    else:
        out.print(f"{idea['slug']} → [bold]{status}[/bold]")


@ledger_app.command("reject")
def ledger_reject(
    slug: str,
    reason: str = typer.Option(..., "--reason", "-r", help="Why. Feeds the taste log."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Reject an idea, with a reason that feeds your taste profile."""
    _status_cmd(slug, "rejected", reason, as_json)


@ledger_app.command("revive")
def ledger_revive(slug: str, as_json: bool = typer.Option(False, "--json")) -> None:
    """Bring a killed or rejected idea back to 'presented'."""
    _status_cmd(slug, "presented", None, as_json)


@ledger_app.command("built")
def ledger_built(slug: str, as_json: bool = typer.Option(False, "--json")) -> None:
    """Mark an idea as built."""
    _status_cmd(slug, "built", None, as_json)


@ledger_app.command("briefed")
def ledger_briefed(slug: str, as_json: bool = typer.Option(False, "--json")) -> None:
    """Mark an idea as briefed (done by /kiln:brief)."""
    _status_cmd(slug, "briefed", None, as_json)


@ledger_app.command("similar")
def ledger_similar(
    text: str,
    threshold: float = typer.Option(0.3, "--threshold", "-t", help="Minimum TF-IDF cosine (0–1)."),
    limit: int = typer.Option(5, "--limit"),
    include_pool: bool = typer.Option(False, "--include-pool", help="Also match unseen pool ideas."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Past ideas that look like TEXT (for skipping near-duplicates)."""
    rows = L.similar_to(connect(), text, threshold, limit, include_pool)
    if as_json:
        _emit_json(rows)
        return
    if not rows:
        out.print("[dim]no similar past ideas[/dim]")
    for r in rows:
        out.print(f"{r['similarity']:.2f}  [bold]{r['slug']}[/bold] ({r['status']}) {escape(r['title'])}")


@ledger_app.command("taste")
def ledger_taste(as_json: bool = typer.Option(False, "--json")) -> None:
    """Reject reasons, newest first (the raw material for the taste log)."""
    rows = L.taste(connect())
    if as_json:
        _emit_json(rows)
        return
    for r in rows:
        out.print(f"{r['updated_at'][:10]}  [bold]{escape(r['title'])}[/bold]: {escape(r['reason'])}")


# ---------------------------------------------------------------- profile


@profile_app.command("path")
def profile_path_cmd() -> None:
    """Print the profile path."""
    out.print(str(profile_path()))


@profile_app.command("init")
def profile_init(force: bool = typer.Option(False, "--force", help="Overwrite an existing profile.")) -> None:
    """Write the starter profile if none exists."""
    created, path = P.init(force)
    out.print(("created " if created else "already exists: ") + path)


@profile_app.command("show")
def profile_show() -> None:
    """Print the profile (exit 2 if missing)."""
    p = profile_path()
    if not p.exists():
        err.print("no profile yet: run `kiln profile init` or /kiln:profile")
        raise typer.Exit(2)
    sys.stdout.write(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    app()
