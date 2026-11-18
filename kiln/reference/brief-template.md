# Brief template

`/kiln:brief` fills this in and writes it to `~/.kiln/briefs/<slug>.md`. The
brief is a prompt for a **fresh Claude Code session in an empty folder**, so it
must stand on its own: no references to Kiln, the ledger, or this conversation.
Write it in the second person to Claude Code. Replace every `<…>`. Delete
nothing except these instructions.

---

```markdown
# Build: <Name>

> <One-line pitch.> Built for <specific person> at <the moment they reach for it>.

## 1. The demo (acceptance test)

This 60-second walkthrough is how we know it works. Do not call the build done
until every step below works on real data.

1. <command or action>  →  <what appears>
2. …
3. <the "huh, neat" moment>

## 2. Scope

**In (day one):**
- <3–6 bullets>

**Out — do NOT build these:**
- <user accounts / auth>
- <settings UI>
- <…everything tempting but not needed for the demo>

## 3. Stack (and why)

| Piece | Choice | Why |
|-------|--------|-----|
| Language | <e.g. Python 3.12> | <user is fluent; …> |
| … | … | … |

Keep it boring. No framework unless the form requires one.

## 4. Verified data sources

For each source:

### <Source name>
- **Endpoint:** `<URL with example params>`
- **Auth:** <none / header / key, and where to get one>
- **Rate limit:** <documented or observed>
- **Verified on <YYYY-MM-DD>:** <what the check returned: status, a trimmed
  sample of the response, the fields we'll use>
- **Gotchas:** <pagination, User-Agent requirements, odd formats>

## 5. Build order

Each milestone ends with something you can run. Run it before moving on.

- **M0 — Spike (15 min):** <prove the riskiest assumption: e.g. fetch one record and print field X>.
- **M1 — Core loop, ugly (≈2.5 h):** <input → transformation → output, end to end>.
- **M2 — Real data path (≈1.5 h):** <all inputs, caching, the real source not a sample>.
- **M3 — Edge cases & errors (≈1.5 h):** <empty results, source down, malformed input, …>.
- **M4 — Polish (≈1.5 h):** <output formatting, README with a screenshot or GIF, install steps>.

## 6. Quality bar

- Tests for the core logic: <name the functions/cases that must be covered>.
- No placeholder or mock data in the final demo. Fixtures are for tests only.
- Graceful failures: <what the user sees when the source is down / input is bad>.
- <Domain-specific correctness rule, e.g. "every legal claim links to its source">.

## 7. How to work

- Start by writing a short plan. Then build milestone by milestone.
- After each milestone, run it and show the output.
- Only stop to ask me if something in "Out" starts to look required.
- Commit after each milestone if this is a git repo.

## 8. Prior art (stay different from these)

| Existing tool | What it does | How this build differs |
|---------------|--------------|------------------------|
| <name + link> | … | … |

The wedge, in one sentence: <differentiation>.
```
