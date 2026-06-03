---
name: macro-regime-monitor
description: Use when running, verifying, or interpreting Macro Regime Kit workflows, including FRED macro-state refreshes, Obsidian sync, portfolio transmission, and thesis-feedback dry-runs.
---

# Macro Regime Monitor

Use the CLI as the source of truth. Do not recreate the model by memory.

## Workflow

1. Run `macro-regime doctor`.
2. If configuration is valid, run `macro-regime run`.
3. Verify `macro_regime_state.json` has fresh FRED values or explicitly marked stale values.
4. If a portfolio risk file exists, run `macro-regime portfolio`.
5. Run `macro-regime weekly`.
6. Run `macro-regime obsidian-sync` only when the user wants local Markdown copied into the vault.
7. For thesis notes, run `macro-regime thesis-feedback` first. Use `--apply` only after explicit user approval.

## Safety Rules

- Never invent missing macro data.
- Never treat Act 2 probability as complete without auction and cross-asset stress checks.
- Never request broker trading permission, withdrawal permission, or wallet private keys.
- Never edit credentials.
- Never rewrite a thesis note outside the bounded feedback block.

## References

- `references/output_schema.md`: state and portfolio transmission schema.
- `references/obsidian_workflow.md`: vault sync and thesis-feedback workflow.
- `references/portfolio_transmission.md`: how to interpret beta and real-yield transmission.

