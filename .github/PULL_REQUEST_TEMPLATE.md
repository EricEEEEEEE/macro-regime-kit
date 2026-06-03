## Summary

-

## Safety

- [ ] No secrets, private paths, real portfolio data, account IDs, or API keys
- [ ] No trading, withdrawal, transfer, or wallet-signing behavior
- [ ] Obsidian writes remain bounded or dry-run by default

## Verification

- [ ] `python -m unittest discover tests`
- [ ] `python scripts/secret_scan.py`
- [ ] CLI smoke tested if behavior changed

