# Kiln

This repository holds the **Kiln** Claude Code plugin, which finds one-day project ideas worth
building and checks them against prior art. The plugin lives in [`kiln/`](kiln/). See
[kiln/README.md](kiln/README.md) for install, the workflow and an example session.

- `kiln/`: the plugin (skills, agents, reference docs, seeds and the `kiln` Python CLI)
- `.claude-plugin/marketplace.json`: a local marketplace, so you can run `/plugin install kiln@kiln-local`
- `kiln-build-prompt.md`: the original spec this was built from
