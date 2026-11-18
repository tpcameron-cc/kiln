---
name: ledger
description: Show and manage Kiln's idea ledger — past ideas, prior-art evidence, reject (with a reason), revive, or mark built.
argument-hint: "[recent | list <status> | show <slug> | reject <slug> <reason> | revive <slug> | built <slug> | similar <text>]"
allowed-tools: Bash(kiln *)
---

# Kiln: ledger

`kiln` is on the Bash PATH; if not found use `"${CLAUDE_PLUGIN_ROOT}/bin/kiln"`.

Request: **$ARGUMENTS**

Map the request to one CLI call and show the result readably:

| Request | Command |
|---------|---------|
| (empty) or `recent` | `kiln ledger recent --n 20` |
| `list [status]` | `kiln ledger list [--status presented\|killed\|rejected\|briefed\|built\|pool]` |
| `show <slug>` | `kiln ledger show <slug>` (includes prior-art matches) |
| `reject <slug> <reason…>` | `kiln ledger reject <slug> --reason "<reason>"` |
| `revive <slug>` | `kiln ledger revive <slug>` (back to presented) |
| `built <slug>` | `kiln ledger built <slug>` |
| `briefed <slug>` | `kiln ledger briefed <slug>` |
| `similar <text>` | `kiln ledger similar "<text>"` |
| `taste` | `kiln ledger taste` |

Rules:
- **Reject always needs a reason.** If none was given, ask for one short phrase —
  it feeds the taste profile, so "meh" isn't useful; ask what specifically put them off.
- If a slug doesn't exist, run `kiln ledger similar "<slug words>" --include-pool`
  and suggest the closest slugs.
- After a reject, mention that `/kiln:profile` will fold the reason into the taste log.
- After `built`, congratulate briefly and ask whether anything about the build
  should change their profile (e.g. a new tool they're now fluent in).
