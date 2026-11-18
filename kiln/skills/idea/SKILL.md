---
name: idea
description: Find one excellent, novel, one-day project idea (at most three), each checked against prior art before it is shown. Use when the user asks Kiln for a project idea, something to build, or a weekend/one-day project.
argument-hint: "[optional theme or constraint]"
allowed-tools: Bash(kiln *) Read Write Agent
---

# Kiln: find a project idea worth building

Theme/constraint from the user (may be empty): **$ARGUMENTS**

You are running Kiln's idea pipeline. The bar: one idea the user would actually
build beats ten generic ones. If nothing survives, say so — never lower the bar
to fill a slot.

`kiln` is the plugin's CLI and is on the Bash PATH. If `kiln` is not found, call it
as `"${CLAUDE_PLUGIN_ROOT}/bin/kiln"` instead.

Reference files (read all four before step 3):
- `${CLAUDE_PLUGIN_ROOT}/reference/generation-moves.md`
- `${CLAUDE_PLUGIN_ROOT}/reference/slop-rubric.md`
- `${CLAUDE_PLUGIN_ROOT}/reference/day-scope.md`
- `${CLAUDE_PLUGIN_ROOT}/reference/brief-template.md` (only to know what a brief will need)

## Context already loaded

Profile:
!`"${CLAUDE_PLUGIN_ROOT}/bin/kiln" profile show 2>&1 || true`

Recent ledger (what the user has already seen, rejected, briefed or built):
!`"${CLAUDE_PLUGIN_ROOT}/bin/kiln" ledger recent --n 40 --json 2>&1 || true`

Rejection reasons (taste signal — weight these heavily):
!`"${CLAUDE_PLUGIN_ROOT}/bin/kiln" ledger taste 2>&1 || true`

## Step 1 — Profile check

If the profile above says "no profile yet", ask the user exactly three quick
questions in one message (languages/tools they're fluent in; two or three
interests; one recurring annoyance), then run `kiln profile init` and append
their answers to `~/.kiln/profile.md` under the matching headings. Continue the
pipeline right away — do not make them run `/kiln:profile` first.

Pick a run id: `run-YYYYMMDD-HHMM` (local time). Use it for every ledger write.

## Step 2 — Draw seeds

Run `kiln seeds --n 6 --json`. These ingredients exist to break your habit of
producing the same ideas. Use at least two of them in the pool; you may ignore
the rest. If the user gave a theme, the theme wins over the seeds.

## Step 3 — Private pool (15–25 raw ideas)

Using **several different moves** from `generation-moves.md`, combining seeds
with the profile, write 15–25 one-line ideas:
`name — who/when — what it does — the sharp edge`.
Follow the pool hygiene rules in that file. **Do not show the pool to the user.**

## Step 4 — Self-filter to 4–6

For each pool idea:
1. Apply `slop-rubric.md` (auto-kill codes K1–K8, quality bar Q1–Q5) and
   `day-scope.md` (D1–D8). Kill with a one-line coded reason.
2. Run `kiln ledger similar "<name> <what it does>" --json --threshold 0.3`.
   Any hit with status presented/rejected/briefed/built ≥ 0.45 is a near-duplicate:
   kill it (`dup of <slug>`). Between 0.3 and 0.45, kill only if it's the same idea
   in substance.

Keep the strongest 4–6. For each survivor write a short spec (name, pitch, who
and when, day-one bullets, sharp edge, riskiest assumption, data sources). For
each data source, write down its **access tier** (see *Key penalty* in Step 7).
When two ideas are about equally strong, keep the open one. Still keep a keyed
idea if it's clearly among the strongest, because Step 7 decides whether it's good
enough to pay its penalty. Don't drop keyed ideas from the pool just for needing a key.

## Step 5 — Red team

Launch the `kiln:slop-critic` subagent (Agent tool, `subagent_type: "kiln:slop-critic"`)
with the shortlist specs and the profile summary. Apply its verdicts:
drop KILLs, adopt SHARPEN suggestions if they make the idea more specific.

## Step 6 — Prior-art research (parallel)

For **every** surviving idea, launch one `kiln:prior-art-scout` subagent — **all in
a single message so they run in parallel**. Give each scout the full idea spec
and tell it to return only its JSON object. Do not research ideas yourself.

If a scout's reply isn't valid JSON, extract the object; if it has none, treat the
idea as unresearched and drop it (never present an unresearched idea).

## Step 7 — Decide and score

- Drop `EXISTS` and `CROWDED`.
- `ADJACENT` survives only if the scout's `differentiation` is real (different job,
  user, data, or form) rather than cosmetic (cheaper, cleaner, "with AI").
- Score each survivor 1–5 on: **novelty**, **would-use** (for this profile),
  **demo delight**, **day feasibility**, **skill fit**. Raw total out of 25.
- Apply the **key penalty** below to get the **final** score. Ranking, the
  "clearly wins" check and the presentation cut-offs all use the final score.
- A survivor with any score of 1 does not get presented.
- An **open** idea is presented only if its final score is at least **15**.
- A **keyed** idea (penalty above 0) is presented only if its final score is at
  least **18**, and only if no open idea beats it. A keyed idea that only ties an
  open idea is not presented.

### Key penalty

The user would rather not sign up for keys or accounts, but doesn't want to miss
a great idea that needs one. Give each idea the access tier of its
**most demanding required source**:

| Tier | What counts | Penalty |
|------|-------------|---------|
| **open** | No key or account. Also counts as open: a key or account the user already has (see the profile's "Keys and accounts I already have", plus `gh` when it's logged in), and data from the user's own files or software. | 0 |
| **free key** | A free signup gives a key or token right away (e.g. CourtListener, FRED, Congress.gov). Includes keyless sources that only allow a uselessly low rate without a key. | **−3** |
| **gated** | Paid, needs approval or a waitlist, needs OAuth app registration, or a login to a personal account the user doesn't have. | **−5** |

- Optional keys don't count. If the idea works without the key and the key only
  adds speed or extras, the tier is open.
- If the scout's notes show a source needs a key you thought it didn't (401/403,
  "API key required"), change the tier before scoring.
- If unsure, use the more demanding tier.
- Day-scope D1 still applies: more than one keyed API means the idea is killed, not penalized.

## Step 8 — Present

Show one idea if one clearly wins (≥3 points ahead), otherwise up to three,
best first. For each:

```
## <Name>  ·  `<slug>`
<One-sentence pitch.>

**For / when:** <specific person, specific moment>
**Day-one version does:**
- <3–5 bullets>
**Sharp edge:** <the non-obvious insight — why this isn't generic>
**Prior art** (<verdict>, <confidence> confidence · <N> queries across <M> sources):
- [<closest match>](<url>) — <what it does>; differs: <how>
- … (2–4 matches)
**Riskiest assumption:** <e.g. "the endpoint returns lap-level data for past races">
**Access:** <"open: no keys needed" | "needs a free <X> key: sign up at <url>, ~<n> min" | "gated: <why>">
**Scores:** novelty <n> · would-use <n> · demo <n> · feasibility <n> · skill fit <n> = <raw>/25 · key penalty −<p> = **<final>**
```

If a keyed idea is presented, say in one line why it was worth the penalty. If a
keyed idea scored well but missed the bar because of the penalty, mention it
under the runners-up as `<slug> (<raw> raw, <final> after key penalty: needs <X> key)`,
so the user can still go after it.

Never say something "doesn't exist". Say what was searched and how confident the scout is.

**If nothing survives:** say so plainly. Show the best near-miss with the exact
reason it died (kill code, scout verdict, or score), and suggest a reroll with a
narrower theme.

## Step 9 — Log everything

Write `~/.kiln/runs/<run_id>.json`: a JSON list with one object for **every** idea
in the step-3 pool (all 15–25, so future runs can skip them), each
`{slug, title, pitch, status, reason, scores, prior_art, theme, run_id}`
(put `access_tier`, `key_penalty`, `raw_total` and `final` inside `scores`):
- killed in step 4/5/7 → `status: "killed"`, `reason: "<code>: <one line>"`
- presented → `status: "presented"`, with `scores` and the scout's full JSON as `prior_art`
- killed after research → include the scout JSON as `prior_art` too
Use short kebab-case slugs (≤ 40 chars) and pass them explicitly so later steps can refer to them.

Then run `kiln ledger add --from-json @<that path>` (use the absolute path) and
confirm the count it printed.

Finish by asking the user what next, offering exactly:
- `/kiln:brief <slug>` to write the build prompt
- reject one with a quick reason (you'll run `kiln ledger reject <slug> --reason "…"`; the reason feeds their taste log)
- reroll (`/kiln:idea` again, optionally with a theme)
