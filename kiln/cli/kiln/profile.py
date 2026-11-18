"""The taste profile at ~/.kiln/profile.md."""

from __future__ import annotations

from datetime import date

from kiln.paths import profile_path

TEMPLATE = """# Kiln taste profile

_Last updated: {today}. Edit freely, or run /kiln:profile._

## Fluent in
- Python, SQL, R
- Adobe Analytics, Salesforce / CRM data

## Platforms I use
- Windows 11 desktop; iRacing on PC
- (add: phone OS, editor, browser, note app…)

## Keys and accounts I already have
_Ideas that use these aren't penalized for needing a key._
- GitHub (gh CLI logged in)
- iRacing account

## Background
- Economics major, computer science minor.
- Day job: paralegal handling creditor negotiations and settlements (debt relief).
- Applying to law school.

## Interests
- Antitrust, white-collar crime, AML, securities fraud
- Motorsports: NASCAR, IMSA
- iRacing and sim-racing hardware
- Music and audio gear
- Cars

## Recurring annoyances
- (add the 5-minute chores you keep doing by hand)

## Ideas I'm tired of
- Anything that is mostly "chat with X" or "AI summarizes X"
- Generic productivity apps

## Ambition
- One-day builds: a working demo in 6–8 hours with Claude Code.
- Grounded in real data and practical use. No hype.

## Taste log
_Built from reject reasons in the ledger. Newest first._
"""


def init(force: bool = False) -> tuple[bool, str]:
    p = profile_path()
    if p.exists() and not force:
        return False, str(p)
    p.write_text(TEMPLATE.format(today=date.today().isoformat()), encoding="utf-8")
    return True, str(p)
