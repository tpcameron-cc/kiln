---
name: brief
description: Write a self-contained Claude Code build prompt for a Kiln idea (by slug), after re-verifying its riskiest assumption against the real data source. Use after /kiln:idea when the user picks an idea to build.
argument-hint: "<slug>"
allowed-tools: Bash(kiln *) Bash(curl *) Read Write WebFetch
---

# Kiln: write the build brief for `$0`

`kiln` is on the Bash PATH; if not found use `"${CLAUDE_PLUGIN_ROOT}/bin/kiln"`.

If no slug was given, run `kiln ledger list --status presented` and ask which one.

## Inputs

Idea record (title, pitch, scores, full prior-art JSON):
!`"${CLAUDE_PLUGIN_ROOT}/bin/kiln" ledger show "$0" --json 2>&1 || true`

Profile (for stack choices — prefer what the user already knows):
!`"${CLAUDE_PLUGIN_ROOT}/bin/kiln" profile show 2>&1 || true`

Template: read `${CLAUDE_PLUGIN_ROOT}/reference/brief-template.md` and follow it exactly.
Day-scope rules: `${CLAUDE_PLUGIN_ROOT}/reference/day-scope.md`.

If the idea record says "no idea with slug", stop and show `kiln ledger recent`.
If the conversation already contains the presented idea (riskiest assumption,
day-one bullets), use that detail too — the ledger only keeps the pitch.

## Step 1 — Verify the riskiest assumption (required)

Before writing anything, actually hit the data source once:
- Use `curl -s -i` (with a descriptive User-Agent where the source asks for one)
  or WebFetch for each data source the build depends on, starting with the riskiest.
- Record: the exact URL, HTTP status, date, the fields that matter, a **trimmed**
  sample (≤ 25 lines), observed or documented rate limits, and any key required.
- If the assumption is **false** (endpoint gone, data missing, behind a login or
  bot wall), stop. Tell the user what you found, propose the smallest change that
  rescues the idea (another source, narrower scope), and only continue if they agree.

Never invent a response. Only paste what actually came back.

## Step 2 — Write the brief

Fill in every section of the template. The brief must stand alone in a fresh
Claude Code session in an empty folder: no mention of Kiln, the ledger, or this
conversation. Specifics:
- **Demo**: concrete commands/clicks with expected output on real data.
- **Scope out**: be generous — list every tempting extra.
- **Stack**: boring and minimal, matched to the profile's fluent languages; give a reason per choice.
- **Verified data sources**: from Step 1, including the date verified.
- **Build order**: M0 spike → M4 polish, each runnable.
- **Prior art**: the scout's closest matches with links and the one-sentence wedge.

Write it to `~/.kiln/briefs/<slug>.md` (absolute path; create the folder if needed).

## Step 3 — Record and hand off

1. `kiln ledger briefed <slug>`
2. Print the whole brief in a single fenced markdown block so it's easy to copy.
3. Tell the user the file path and: "Open a new, empty folder, start `claude`, and paste this."
   Remind them to run `kiln ledger built <slug>` (or `/kiln:ledger built <slug>`) once it works.
