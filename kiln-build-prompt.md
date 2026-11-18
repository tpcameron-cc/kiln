# Build "Kiln": a Claude Code plugin that finds one-day project ideas worth building

## What I want

I want a Claude Code plugin called **Kiln**. When I ask it for a project idea, it gives me one excellent idea, or at most three. It only shows me an idea after it has researched whether something similar already exists. When I pick one, it writes a detailed build prompt that I can paste into a fresh Claude Code session and finish in one day.

This is a tool, not a context file. It needs real moving parts: subagents, skills, a Python CLI that queries real prior-art sources, and a local ledger that remembers every idea it has suggested, killed or built, so it never repeats itself and learns my taste over time.

Three things matter most:
1. **No AI slop.** One idea I'd actually build beats ten generic ones. If nothing good survives, Kiln should say so instead of padding the list.
2. **Buildable in one day.** A solo developer working with Claude Code should be able to build it in about 6 to 8 hours and have a working demo at the end.
3. **Checked for novelty.** Before presenting an idea, Kiln searches hard for existing tools. It shows the closest matches it found and explains how the idea is different. It never claims something "doesn't exist." It reports what it searched and how confident it is.

## Before writing anything

1. Check the current Claude Code docs (docs.claude.com) for the exact current formats of **plugins** (`.claude-plugin/plugin.json`, directory layout, local install and marketplace), **skills** (`skills/<name>/SKILL.md` frontmatter), **subagents** (`agents/<name>.md` frontmatter: name, description, tools, model) and **hooks**. Follow what the docs say, not what you remember.
2. Show me a short plan with the file tree, then build it. Don't stop for approval unless a decision is truly ambiguous.

## Architecture

```
kiln/
├── .claude-plugin/plugin.json
├── skills/
│   ├── idea/SKILL.md          # /kiln:idea — main entry point, runs the pipeline
│   ├── brief/SKILL.md         # /kiln:brief <slug> — writes the Claude Code build prompt
│   ├── profile/SKILL.md       # /kiln:profile — sets up and updates my taste profile
│   └── ledger/SKILL.md        # /kiln:ledger — shows past ideas, reject/revive, mark built
├── agents/
│   ├── prior-art-scout.md     # researches ONE idea; run several in parallel
│   └── slop-critic.md         # red-teams the shortlist for slop and day-scope
├── reference/
│   ├── slop-rubric.md         # banned patterns and quality bar (details below)
│   ├── generation-moves.md    # idea-generation techniques (details below)
│   ├── day-scope.md           # what "buildable in a day" means (details below)
│   └── brief-template.md      # structure of the build prompt
├── cli/                       # Python package, installed as the `kiln` command
│   ├── pyproject.toml
│   └── kiln/ ...
├── data/seeds/                # curated ingredient lists for random draws
└── README.md
```

Store per-user state outside the plugin, in `~/.kiln/`: `profile.md`, `kiln.db` (SQLite), and `briefs/`.

## The pipeline (`/kiln:idea [optional theme or constraint]`)

1. **Load context.** Read `~/.kiln/profile.md` and pull recent ledger entries (`kiln ledger recent --json`) so Kiln knows what I've already seen, rejected (and why) or built. If there's no profile yet, ask three quick questions and then continue. Don't make me run the whole setup first.
2. **Draw seeds.** Run `kiln seeds --n 6` to get random ingredients: a public data source or API, an interaction form, a domain, a constraint, a file format or medium, and an "odd angle." These exist to break the model's tendency to keep producing the same ideas. Kiln should use some draws and may ignore others.
3. **Generate a private pool of 15 to 25 raw ideas** using the techniques in `generation-moves.md`, combining the seeds with my profile. I never see this pool.
4. **Self-filter** against `slop-rubric.md` and `day-scope.md`, and drop anything that's close to an idea already in the ledger. Keep the strongest 4 to 6.
5. **Red team.** Give the shortlist to the `slop-critic` subagent. It returns a kill or keep verdict for each idea, with one-line reasons, and may suggest sharpening an idea that's close but generic.
6. **Prior-art research.** Run one `prior-art-scout` subagent per surviving idea, **in parallel**. Each scout:
   - Writes 6 to 10 varied search queries: synonyms, the job the tool does, how a user would describe the problem, and adjacent terms.
   - Runs `kiln search` across all sources, plus WebSearch and WebFetch for broader web results, app stores, Chrome Web Store pages, browser extensions, Show HN posts and subreddits.
   - Opens the top candidate matches and reads what they actually do. Titles alone aren't enough.
   - Returns structured JSON: `verdict` (CLEAR / ADJACENT / CROWDED / EXISTS), `confidence` (low/med/high), `closest_matches` (name, url, what it does, how it differs), `queries_run`, `sources_checked`, and `differentiation` (the one sentence that makes this idea different).
7. **Decide.** Drop EXISTS and CROWDED. An ADJACENT idea survives only if its differentiation is real and not cosmetic. Score the survivors on a simple 1–5 rubric: novelty, would-I-use-it (based on my profile), demo delight, day-feasibility and how well it fits my skills. Show the scores.
8. **Present** one idea if one clearly wins, otherwise at most three. Each idea gets:
   - A name and a one-sentence pitch
   - Who it's for and the moment they reach for it
   - What the finished day-one version does (3 to 5 bullets)
   - The non-obvious insight or "sharp edge," meaning why this isn't generic
   - A prior-art summary: the closest matches with links, how it differs, the scout's confidence, and how many queries and sources were checked
   - The riskiest assumption (for example, "the API actually returns X")
   - Scores
9. **Log everything** to the ledger: presented ideas, killed ideas with the reason, and the prior-art evidence. Then ask whether I want to `/kiln:brief` one, reject one (with a quick reason that feeds my taste profile), or reroll.

If nothing survives, say that plainly and show the best near-miss and why it died. Do not lower the bar to fill a slot.

## `kiln` CLI (Python 3.11+, httpx, typer, sqlite3)

**`kiln search "<query>" [--sources ...] [--json]`** runs searches in parallel and returns normalized results (`source, title, url, description, stars/points/downloads, last_updated`):
- **GitHub** repositories and topics. Use `gh api` if `gh` is authenticated, otherwise `GITHUB_TOKEN`, otherwise unauthenticated with backoff.
- **Hacker News** via Algolia (`hn.algolia.com/api/v1/search`), weighting "Show HN" posts.
- **npm** registry search, **PyPI** (via the simple index or a search fallback), **crates.io**
- **Reddit** search JSON for relevant subreddits
- **Lobsters** search
- **Product Hunt** only if `PRODUCT_HUNT_TOKEN` is set. Otherwise skip it quietly.

Cache responses in SQLite for 7 days. Handle rate limits gracefully. When a source fails, show it in the output as failed. Never drop it silently, because the scout needs to report what it actually checked.

**`kiln seeds [--n 6] [--category ...]`** makes random draws from `data/seeds/*.txt`. Write good seed lists of at least 40 to 80 entries each. These lists are where much of the anti-slop work happens, so make them specific and surprising:
- `data_sources.txt`: real, free, keyless or easy-key public APIs and datasets (government open data, court and legislative data, sports timing feeds, weather and tides, transit GTFS, library catalogs, OpenStreetMap, Wikidata, SEC EDGAR, FRED, public RSS feeds, and so on)
- `forms.txt`: CLI, browser extension, menu-bar app, single HTML file, printable PDF, local web dashboard, TUI, bookmarklet, Raycast or Alfred extension, Obsidian plugin, iCal feed, email digest, physical printout, and so on
- `domains.txt`, `constraints.txt` (for example "works offline," "zero UI, outputs a file," "uses only one keyboard key"), `formats.txt`, `odd_angles.txt` (for example "make an invisible thing visible," "invert the usual workflow," "port a tool from another profession")

**`kiln ledger add|recent|list|reject|revive|built|show <slug>`** is a SQLite store for ideas with these fields: slug, title, pitch, status (pool/killed/presented/rejected/briefed/built), kill or reject reason, scores, prior-art JSON, created_at. Include a `similar "<text>"` command that does simple TF-IDF or token-overlap matching so the pipeline can skip near-duplicates of past ideas.

Write tests for the search normalizers (using recorded fixtures, not live calls), the ledger and the similarity check.

## `reference/slop-rubric.md`

Kill an idea automatically if it matches any of these, unless it has a truly unusual twist:
- An LLM wrapper whose core value is "chat with X" or "AI summarizes X"
- A generic productivity app: to-do lists, habit trackers, Pomodoro timers, note apps, journaling apps, bookmark managers
- An "AI-powered assistant for <profession>"
- Dashboards with no specific question they answer
- Ideas that require a user base, network effects, marketplaces or social features to have any value
- Resume or cover-letter builders, prompt libraries, "Uber for X," newsletter generators
- Anything whose pitch only works with buzzwords such as "seamless," "revolutionize," "leverage" or "empower"
- Anything I'd describe as "a nicer version of an existing popular tool" with no real wedge

Quality bar (a keeper hits most of these):
- A **specific person in a specific moment** (ideally me), not "users"
- A **non-obvious insight**: an underused data source, an unexpected form, or a workflow inversion
- **Demoable in 60 seconds** with a "huh, neat" moment
- A **clear done state**: you know when it works
- Useful even if nobody else ever uses it

AI may be part of an idea, but it shouldn't be the whole idea. The test: if the LLM call were removed, would anything interesting be left?

## `reference/day-scope.md`

A one-day idea needs:
- At most one external API that needs a key, and the data is reachable right now (so the scout or brief verifies the endpoint)
- No user accounts or auth system, no payments, no app-store submission, no model training, no scraping that needs to beat bot protection
- A core loop that can be built in about 3 hours, leaving time for polish, edge cases and a README
- A runnable demo by the end of the day: local is fine, deployed is a bonus

## `reference/generation-moves.md`

Write 12 to 15 concrete techniques with an example of each, for instance:
- Collide a seed data source with one of my interests
- Make an invisible thing visible
- Invert a workflow
- Port a professional tool to a hobby, or the reverse
- Find the most annoying 5 minutes in one of my routines
- Turn a boring public dataset into a delightful artifact
- Build "the missing CLI" for a site that only has a GUI
- Build the tool an expert in my field quietly maintains as a spreadsheet
- Cross the format of one domain with the content of another

## `/kiln:brief <slug>`: the build-prompt skill

This skill writes `~/.kiln/briefs/<slug>.md` and prints it, ready to paste into a fresh Claude Code session in an empty folder. Before writing, it re-verifies the riskiest assumption: it actually hits the API or fetches the data source once and records what came back. Structure (put this in `brief-template.md`):

1. **One-line pitch and who it's for**
2. **The demo:** the 60-second walkthrough that proves it works. This is the acceptance test.
3. **Scope in / scope out:** an explicit list of what NOT to build
4. **Stack, with reasons** (keep it boring and minimal; prefer languages and tools I already know from my profile)
5. **Verified data sources:** endpoints, sample responses, rate limits, and any keys needed
6. **Build order as milestones**, each one leaving something runnable: (0) a 15-minute spike on the riskiest assumption, (1) the core loop end to end and ugly, (2) the real data path, (3) edge cases and error states, (4) polish, README with a screenshot or GIF
7. **Quality bar:** tests for the core logic, no placeholder or mock data in the final demo, graceful failures
8. **Instructions to Claude Code:** plan first, build milestone by milestone, run it after each milestone, and stop to ask only if a scope-out item seems to be required
9. **Prior-art note:** the closest existing tools, so the build stays different from them

Mark the idea as `briefed` in the ledger.

## `/kiln:profile`

This skill creates and edits `~/.kiln/profile.md` through a short interview: languages and tools I'm fluent in, platforms I use, interests, recurring annoyances, ideas I'm tired of, and how ambitious I want ideas to be. It also adds a "taste log" built from reject reasons in the ledger. Seed the profile with a starting point the user can edit:

- Education and the languages and tools they're comfortable with.
- Day job and the professional topics they're interested in.
- Hobbies and interests, as specific as possible.
- A preference for ideas grounded in real data and practical use, with no hype.

(The user's real seed profile is kept in `~/.kiln/profile.md`, not in this repo.)

## Subagent notes

- `prior-art-scout`: tools are Bash (for `kiln search`), WebSearch, WebFetch and Read. Its instructions must stress being adversarial toward the idea: its job is to *find* the existing tool, not to confirm novelty. It returns only the structured JSON, no prose.
- `slop-critic`: tools are Read only. It's skeptical and short. It applies the rubric and day-scope literally and must explain each kill in one line.

## Done when

- `claude --plugin-dir ./kiln` (or whatever the current docs specify for local plugins) loads the plugin, and `/kiln:idea`, `/kiln:brief`, `/kiln:profile` and `/kiln:ledger` all appear.
- `kiln search "sim racing telemetry"` returns real results from at least 4 sources, with failures clearly marked.
- A full `/kiln:idea` run completes end to end, logs to the ledger, and presents at least one idea with linked prior-art evidence. Run it once yourself and show me the output.
- `/kiln:brief` on that idea produces a brief that follows the template, including the verified riskiest assumption.
- The README explains install, optional tokens (`GITHUB_TOKEN`, `PRODUCT_HUNT_TOKEN`) and the workflow, and has an example session.
