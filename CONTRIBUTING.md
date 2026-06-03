# Contributing

Thanks for improving Macro Regime Kit.

## Local Setup

```bash
git clone https://github.com/EricEEEEEEE/macro-regime-kit.git
cd macro-regime-kit
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m unittest discover tests
```

## Rules

- Keep examples synthetic.
- Do not commit `.env`, real portfolio state, real broker output, account numbers, vault paths, or API keys.
- Do not add trading, withdrawal, transfer, or wallet-signing actions.
- Prefer dry-run for Obsidian writes and thesis feedback.
- Treat stale macro data as stale; do not fabricate replacement values.

## Pull Request Checklist

- Tests pass: `python -m unittest discover tests`
- Secret scan passes: `python scripts/secret_scan.py`
- CLI still works: `macro-regime --version`
- New public behavior is documented in `README.md` or `docs/`

## Adapter Contributions

Broker and exchange adapters are welcome, but they must be read-only:

- No order placement.
- No withdrawal or transfer permissions.
- No private keys.
- No credential logging.
- Include fixture-based tests with synthetic data.

