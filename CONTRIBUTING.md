# Contributing to Kiln

Thanks for taking a look! Bug reports, ideas and pull requests are all welcome.

## Reporting a bug or suggesting an idea

Open an [issue](../../issues/new/choose) and pick a template. Screenshots, steps to
reproduce and your setup help a lot.

## Making a change

1. Fork the repo and create a branch.
2. Run the tests: `cd kiln/cli && uv run --group dev python -m pytest -q`, and validate the plugin with `claude plugin validate ./kiln`.
   Never commit personal Kiln data (anything from `~/.kiln/`).
3. Keep pull requests focused on one change and describe what you checked.

If you're planning something large, open an issue first so we can talk it through.

## License

By contributing you agree that your contributions are licensed under the [MIT License](LICENSE).
