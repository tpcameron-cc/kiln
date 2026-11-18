# Working on the Kiln repo

This repo is the Kiln plugin's **code only**. It is pushed to GitHub (private).

## Never commit personal Kiln data

The user's own data lives in `~/.kiln/` and must never be copied into this repo:
- `kiln.db` (the idea ledger), `runs/*.json`, `briefs/*.md`
- `profile.md`, including the taste log and anything specific to the user's tastes

Don't hardcode the user's background, interests, keys or accounts into skills,
agents, reference docs or `cli/kiln/profile.py`. Templates stay generic, and
personal tuning belongs in `~/.kiln/profile.md`.

## Examples

`kiln/examples/` holds a **fixed, curated** set of example outputs that the user
approved for the repo. Don't add new runs or briefs there unless the user asks
for a specific one to be added. `.gitignore` blocks `briefs/`, `runs/` and `*.brief.md`.

## Before pushing an update

- `cd kiln/cli && uv run --group dev python -m pytest -q`
- `claude plugin validate ./kiln`
- `git status`: make sure nothing from `~/.kiln` or any new generated idea is staged.
