# Slop rubric

Apply literally. An idea that trips any **auto-kill** pattern dies unless it has a
twist so unusual that a skeptic would say "oh, that's actually different" — and
the twist must be stated in one sentence, not implied.

## Auto-kill patterns

| # | Pattern | Tell-tale phrasing |
|---|---------|--------------------|
| K1 | **LLM wrapper** whose core value is "chat with X" or "AI summarizes X" | "ask questions about your…", "get AI insights from…" |
| K2 | **Generic productivity app**: to-do list, habit tracker, Pomodoro timer, note app, journaling app, bookmark manager | "stay organized", "track your habits" |
| K3 | **"AI-powered assistant for <profession>"** | "copilot for lawyers/doctors/realtors" |
| K4 | **Dashboard with no specific question** it answers | "see all your X in one place", "insights at a glance" |
| K5 | **Needs other users to be valuable**: user base, network effects, marketplace, social feed, sharing, leaderboards with strangers | "connect with other…", "community" |
| K6 | **Resume / cover-letter builder, prompt library, "Uber for X", newsletter generator** | — |
| K7 | **Buzzword pitch**: only works with "seamless", "revolutionize", "leverage", "empower", "unlock", "supercharge", "streamline" | rewrite without them; if nothing is left, kill |
| K8 | **"A nicer version of <popular tool>"** with no real wedge | "like X but cleaner/faster/simpler" |

## The LLM-removal test

AI may be *part* of an idea. Delete every LLM call from the design. If nothing
interesting is left — no data join, no unusual form, no workflow inversion — kill it (K1).

## Quality bar (a keeper hits most)

- **Q1 Specific person, specific moment.** "Me, Sunday night before the IMSA
  race, deciding which class battle to watch" — not "racing fans".
- **Q2 Non-obvious insight.** One of: an underused data source, an unexpected
  form, a workflow inversion, a join nobody makes. Name it.
- **Q3 Demoable in 60 seconds** with a "huh, neat" moment you can point at.
- **Q4 Clear done state.** You can write the acceptance test in one sentence.
- **Q5 Useful even if nobody else ever uses it.**

A keeper hits **at least 4 of 5**. Hitting Q1 and Q2 is mandatory.

## Smells that aren't auto-kills but cost points

- The pitch needs the word "platform".
- The demo needs fake/mock data to look good.
- The hardest part is UI polish rather than a real data or logic problem.
- It duplicates a built-in feature of something the user already uses (Excel, iRacing UI, Gmail filters).
- The core loop is "fetch → show" with no transformation, judgment or join.
- The idea is a category ("a tool for X") rather than a thing ("prints Y when Z").

## How to write a kill reason

One line, cite the code: `K4: "all your filings in one place" — answers no question.`
or `Q2 missing: obvious data, obvious form, obvious user.`
