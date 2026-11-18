---
name: profile
description: Create or update the user's Kiln taste profile (~/.kiln/profile.md) through a short interview, and refresh its taste log from ledger reject reasons.
argument-hint: "[what to change, or empty for the interview]"
allowed-tools: Bash(kiln *) Read Write Edit
---

# Kiln: taste profile

`kiln` is on the Bash PATH; if not found use `"${CLAUDE_PLUGIN_ROOT}/bin/kiln"`.

Request: **$ARGUMENTS**

Current profile:
!`"${CLAUDE_PLUGIN_ROOT}/bin/kiln" profile show 2>&1 || true`

Reject reasons from the ledger (newest first):
!`"${CLAUDE_PLUGIN_ROOT}/bin/kiln" ledger taste 2>&1 || true`

## If there is no profile yet

Run `kiln profile init` — it writes a starter profile seeded with the user's
background (economics + CS minor; Python, SQL, R, Adobe Analytics, Salesforce;
paralegal in debt relief; antitrust/white-collar/AML/securities-fraud interests;
law-school applicant; NASCAR, IMSA, iRacing and sim-racing hardware; music and
audio gear; cars; wants practical, data-grounded ideas, no hype). Then do the
interview below to fill the gaps.

## If the user asked for a specific change

Make just that change with Edit, update the `_Last updated` date, show the diff
in one or two lines, and stop.

## Otherwise: the interview

Ask in **one message**, numbered, all optional ("skip" is fine):
1. Languages and tools you're fluent in (anything missing from the profile?)
2. Platforms you use daily (OS, phone, editor, browser, note app, sim rig…)
3. Interests to add or drop
4. Two or three recurring annoyances — chores that eat 5+ minutes every week
5. Kinds of ideas you're tired of seeing
6. Ambition: strict one-day builds, or allow stretch ideas?
7. API keys or accounts you already have (e.g. FRED, CourtListener, Spotify, OpenAI).
   Ideas that use these skip the key penalty.

Merge the answers into the matching headings. Keep it terse: bullets, no prose.

## Taste log

Rebuild the `## Taste log` section from the reject reasons above: group similar
reasons into short rules phrased as preferences, newest first, e.g.
`- Avoid ideas that need PACER fees (rejected: docket-bell)`. Keep the raw slugs
in parentheses so the rule can be traced. Don't invent entries.

Finish by printing the updated profile.
