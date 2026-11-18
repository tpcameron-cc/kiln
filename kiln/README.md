# Kiln

A Claude Code plugin that finds **one-day project ideas worth building**. Ask it
for an idea and you get one (at most three). Each idea has already been
red-teamed for slop and checked against real prior art. Pick one and Kiln writes
a paste-ready build prompt for a fresh Claude Code session.

- **No slop.** A literal rubric kills "chat with X", generic productivity apps,
  dashboards with no question, and buzzword pitches. If nothing survives, Kiln says so.
- **Buildable in a day.** Day-scope rules: at most one keyed API, no auth or payments,
  a core loop of about 3 hours, and a runnable demo by the end of the day.
- **Checked for novelty.** Parallel scouts try to *find* the existing tool across
  GitHub, Hacker News, npm, PyPI, crates.io, Reddit, Lobsters, Product Hunt and the
  web. They report the closest matches, what was searched, and how confident they are.
- **Remembers.** A local SQLite ledger records every idea that was suggested, killed,
  rejected, briefed or built, so ideas don't repeat and reject reasons tune your taste profile.

## Commands

| Command | What it does |
|---------|--------------|
| `/kiln:idea [theme]` | Runs the full pipeline and presents 1–3 researched ideas |
| `/kiln:brief <slug>` | Re-verifies the riskiest assumption against the live source, then writes `~/.kiln/briefs/<slug>.md` |
| `/kiln:profile [change]` | Interview that creates or edits `~/.kiln/profile.md` and rebuilds the taste log |
| `/kiln:ledger [recent\|show\|reject\|revive\|built\|similar …]` | Views and manages past ideas |

## How `/kiln:idea` works

1. **Load context:** your profile, the 40 most recent ledger entries, and your reject reasons.
2. **Draw seeds:** `kiln seeds --n 6` picks a random data source, form, domain,
   constraint, file format and "odd angle" from `data/seeds/`.
3. **Private pool:** 15–25 raw ideas, written with the moves in `reference/generation-moves.md`. You never see the pool.
4. **Self-filter:** the slop rubric, day-scope rules, and `kiln ledger similar` for near-duplicates. The best 4–6 survive.
5. **Red team:** the `slop-critic` subagent returns KEEP, KILL or SHARPEN for each idea, with a one-line reason.
6. **Prior art:** one `prior-art-scout` subagent per idea, all in parallel. Each runs
   6–10 queries through `kiln search` and the web, reads the top matches, and returns JSON:
   a verdict (CLEAR, ADJACENT, CROWDED or EXISTS), a confidence level, the closest matches, the queries and sources it checked, and the differentiation.
7. **Decide:** EXISTS and CROWDED ideas are dropped, and so is an ADJACENT idea whose wedge is only cosmetic. Survivors are scored 1–5 on
   novelty, would-use, demo delight, day feasibility and skill fit.
   **Key penalty:** an idea that needs an API key or account you don't already have loses
   3 points (free instant key) or 5 (paid, approval or OAuth). It also needs a final score of 18 instead of 15, and it must beat
   every open idea. Great keyed ideas still get through, and near-misses are listed as runners-up.
   Keys you already have go in the profile's "Keys and accounts I already have" section and aren't penalized.
8. **Present:** each idea gets a pitch, who it's for, the day-one bullets, its sharp edge, prior-art evidence with links, the riskiest assumption and its scores.
9. **Log:** every pool idea goes into the ledger, killed ones with the reason why.

## Install

Requirements: [Claude Code](https://code.claude.com), and [uv](https://docs.astral.sh/uv/)
(uv fetches Python 3.11+ on its own). `gh` is optional but recommended.

```powershell
git clone https://github.com/tpcameron-cc/kiln
cd kiln
```

**Try it for one session** (no install):

```powershell
claude --plugin-dir ./kiln
```

**Install it permanently** from the bundled local marketplace. Inside Claude Code:

```
/plugin marketplace add C:/path/to/kiln
/plugin install kiln@kiln-local
```

The first `kiln` call creates the CLI's virtual environment in `kiln/cli/.venv`
(a few seconds). While the plugin is enabled, Claude Code puts the plugin's `bin/`
directory on the Bash PATH, so the skills and agents call `kiln` directly.

### Using `kiln` in your own terminal

`bin/kiln` (sh) and `bin/kiln.cmd` (PowerShell/cmd) wrap
`uv run --project kiln/cli python -m kiln`. Add `kiln/bin` to your PATH, or call it by path:

```powershell
.\kiln\bin\kiln.cmd search "sim racing telemetry"
```

If your machine allows `.exe` launchers, `uv tool install -e ./kiln/cli` also works.
On machines with Windows Smart App Control or WDAC, the generated `kiln.exe`
launcher may be blocked. The `bin/` wrappers avoid that.

### Optional tokens

| Variable | Effect |
|----------|--------|
| `GITHUB_TOKEN` | Used for GitHub search when `gh` isn't installed and logged in. Without either, GitHub search runs unauthenticated (10 requests/min, with backoff). |
| `PRODUCT_HUNT_TOKEN` | Turns on Product Hunt (developer token from producthunt.com/v2/oauth/applications). Without it the source shows as `SKIPPED`. |

## The `kiln` CLI

```
kiln search "<query>" [--sources github,hn,npm,pypi,crates,reddit,lobsters,producthunt] [--json] [--no-cache]
kiln seeds [--n 6] [--category forms] [--list] [--json]
kiln ledger add --title … [--pitch …] [--status …] [--reason …] [--scores JSON] [--prior-art JSON|@file] [--slug …]
kiln ledger add --from-json @ideas.json
kiln ledger recent|list|show <slug>|reject <slug> --reason …|revive|built|briefed|taste
kiln ledger similar "<text>" [--threshold 0.3] [--include-pool]
kiln profile init|show|path
kiln home
```

Search notes:
- Every source reports `ok`, `failed` (with the error) or `skipped`. A source never drops out silently.
- Results are cached in SQLite for 7 days. Failures are never cached. Use `--no-cache` to force a fresh search.
- **GitHub:** repositories plus topics. Uses `gh api` when it's logged in, otherwise `GITHUB_TOKEN`, otherwise no auth.
- **Hacker News:** the Algolia API. Show HN posts are ranked first.
- **PyPI:** PyPI has no search API, and its search page is behind a bot challenge. Kiln downloads the
  simple index once a week (about 45 MB), matches project *names*, and fetches metadata for the top hits.
  The source note says this.
- **Reddit:** reddit.com answers 403 to clients without OAuth, so Kiln falls back to the PullPush
  archive. The note says `via PullPush archive`.
- **Lobsters:** parsed from the HTML search page.
- **Product Hunt:** the API has no text search, so Kiln lists top posts in the topics that match the query.

## Files

```
kiln/
├── .claude-plugin/plugin.json
├── skills/{idea,brief,profile,ledger}/SKILL.md
├── agents/{prior-art-scout,slop-critic}.md
├── reference/{slop-rubric,generation-moves,day-scope,brief-template}.md
├── data/seeds/*.txt          # 6 lists, 49–84 entries each
├── bin/kiln, bin/kiln.cmd    # CLI wrappers (on Claude's PATH while enabled)
└── cli/                      # Python package (httpx, typer, sqlite3) + tests
```

Your state lives in `~/.kiln/` (override with `KILN_HOME`): `profile.md`, `kiln.db`,
`briefs/`, and `runs/` (the JSON each `/kiln:idea` run logs).

## Tests

```powershell
cd kiln/cli
uv run --group dev python -m pytest -q
```

The normalizer tests run against recorded responses in `cli/tests/fixtures/`, with no live
calls. The Reddit-listing and Product Hunt fixtures are hand-built in each API's documented shape,
because neither source was reachable unauthenticated when the fixtures were recorded.

## Example session

An illustration of the shape of a session (the idea is a made-up example, not a real run).
Your own ideas and briefs are written only to `~/.kiln/` on your machine and never into this repo.

```
> /kiln:idea

One idea won clearly. It scored 20/25; the runner-up scored 16.

## Tide Window  ·  `tide-window`
Turns NOAA tide predictions into calendar events for the hours a beach is walkable.

**For / when:** You, Sunday night, planning a low-tide walk for the week.
**Day-one version does:**
- Pulls predictions for one station from the NOAA CO-OPS API (no key needed)
- Finds the windows below a height you choose
- Writes an .ics feed you can subscribe to
**Sharp edge:** The output is your calendar, not another app to open.
**Prior art** (ADJACENT, medium confidence · 9 queries across 7 sources plus the web):
- [<closest match>](<url>): tide charts and apps, with no calendar export of walkable windows
**Riskiest assumption:** The predictions endpoint returns hi/lo times 30 days ahead.
**Access:** open: no keys needed
**Scores:** novelty 4 · would-use 4 · demo 4 · feasibility 4 · skill fit 4 = 20/25 · key penalty −0 = **20**

> /kiln:brief tide-window
Checked the predictions endpoint live (200, 30 days of hi/lo times). Brief written to
~/.kiln/briefs/tide-window.md and marked as briefed.

> /kiln:ledger reject <slug> <reason>
```

When a data source fails its live check (for example, it turns out to need a login),
`/kiln:brief` stops, reports what it found, and suggests the smallest fix instead of
writing a brief it can't back up.
