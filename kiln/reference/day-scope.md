# Day scope: what "buildable in one day" means

Target: a solo developer working with Claude Code, **6–8 hours**, ends the day
with a working demo on real data.

## Hard requirements (fail any → kill, code `D#`)

| # | Rule |
|---|------|
| D1 | **At most one external API that needs a key**, and its data is reachable *right now* (the scout or brief verifies the endpoint). Keyless sources don't count toward the limit. An idea that passes D1 with one keyed API still takes the **key penalty** at scoring (−3 for a free key, −5 for a gated one; see the idea skill), so it has to be clearly better than the open ideas to be presented. |
| D2 | **No user accounts or auth system** of its own. Using the user's own token for a single API is fine. |
| D3 | **No payments**, no app-store submission, no extension-store review as a requirement for the demo (sideloading is fine). |
| D4 | **No model training** or fine-tuning. Calling an existing model is fine (subject to the slop rubric). |
| D5 | **No scraping that must beat bot protection** (Cloudflare challenges, logins, CAPTCHAs, aggressive rate limits). Plain HTML pages are fine. |
| D6 | **Core loop buildable in ~3 hours**, leaving time for polish, edge cases and a README. |
| D7 | **Runnable demo by end of day.** Local is fine; deployed is a bonus. |
| D8 | **No hardware the user doesn't already own.** |

## Estimation heuristic

Count the moving parts in the core loop:

- Each distinct data source to fetch and parse: **45–90 min** (90 if HTML or an undocumented feed)
- Each non-trivial transformation (join, diff, scoring, parsing a binary format): **45–90 min**
- The output form: CLI/file **15 min**, single HTML file **45 min**, browser extension **90 min**, tray/menu-bar app **2 h**, physical device **3 h+**
- Scheduling/notifications (cron, ntfy, email): **30 min**

If the core loop sums to **more than ~3.5 h**, the idea is over scope. Either cut it
to a smaller core (say what you cut) or kill it with `D6`.

## Signs of hidden scope

- "…and it learns over time" (needs data you don't have yet)
- "…for any <thing>" (generality multiplies edge cases — pick one)
- "…syncs across devices"
- "…real-time" where the source only updates daily (or vice versa)
- A binary or proprietary file format with no existing parser
- Any OCR of messy documents as the core step
- Legal/financial data where correctness errors would mislead (OK, but scope must include a visible "verify against source" link)

## A good day plan looks like

| Time | Milestone |
|------|-----------|
| 0:00–0:15 | Spike the riskiest assumption (hit the API, parse one file) |
| 0:15–3:00 | Core loop end to end, ugly |
| 3:00–4:30 | Real data path, all inputs |
| 4:30–6:00 | Edge cases, error states, tests on core logic |
| 6:00–7:30 | Polish, README with screenshot/GIF |
