# deq-tune library

Car profiles and EQs for [deq-tune](https://github.com/stevendejongnl/deq-tune),
shared by the people who made them.

The deq-tune app shows this library under **Settings → Community**. Choose an
entry and tap **Add to my library**. The app adds it to your own profiles or
EQs, next to what you have. It never changes or replaces an item of yours.
Your phone or computer reads the library from the internet. The Pi does not
need internet for it.

## What is here

| Directory | Holds |
|---|---|
| `equalizers/` | one EQ per file: `equalizers/<name>.json` |
| `profiles/` | one car profile per file: `profiles/<brand>/<model>/<name>.json` |
| `schema/openapi.json` | a copy of the deq-tune backend's schema, which gives each item its shape |
| `tools/` | the check, the index build, and the tool that makes an entry from your backup file |

An entry holds its author, a description, and the item, in the same shape
as the app's backup file:

```json
{
  "author": "your-github-name",
  "description": "Less bass and softer highs, for the motorway at night.",
  "equalizer": { "name": "Night drive", "gains": [0, 0, -1, -1, 0, 0, 0, 0, 0, -1, -1, -2, -2] }
}
```

A car profile has `"profile"` in place of `"equalizer"`, with the car's
brand, model and tuning data.

## Add your own

[CONTRIBUTING.md](CONTRIBUTING.md) has the steps.

## How it is published

Each push to `main` runs `tools.check`, builds `site/index.json` with all
entries in one file, and publishes it on GitHub Pages:
<https://stevendejongnl.github.io/deq-tune-library/index.json>. The app reads
that one file.

```sh
uv sync
uv run pytest -q                    # the tools' own tests
uv run python -m tools.check        # every entry: shape and value ranges
uv run python -m tools.build_index  # writes site/index.json
uv run python -m tools.update_schema  # after deq-tune changes its backup file
```

## License

The entries are public domain, under [CC0 1.0](LICENSE). Anybody can use,
change and share them, also without your name. The author field stays in
the entry, so the app shows who made it.
