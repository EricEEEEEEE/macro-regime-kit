# Macro Regime Kit Agent Rules

This is an open-source project. Do not add private user data, personal vault paths, broker account numbers, Telegram topics, API keys, portfolio snapshots, or machine-specific state.

## Safe Defaults

- Keep all examples synthetic.
- Do not write into a real Obsidian vault during tests.
- Do not add broker trading APIs or order placement.
- Do not request wallet private keys.
- Prefer dry-run before any Markdown write.

## Verification

Run:

```bash
python3 -m unittest discover tests
```

Before publishing, scan for obvious secrets:

```bash
rg -n "FRED_API_KEY=.+|OPENAI_API_KEY=.+|TELEGRAM|/Users/|iCloud~md~obsidian|account|secret|token" .
```

