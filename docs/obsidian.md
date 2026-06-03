# Obsidian Setup

Macro Regime Kit writes Markdown reports. Obsidian is optional but recommended.

## Suggested Vault Layout

```text
Investment Vault/
├── 宏观追踪/
├── 投资论点/
└── 仓位/
```

## Configuration

```yaml
obsidian:
  enabled: true
  vault_path: "/path/to/Investment Vault"
  macro_folder: "宏观追踪"
  thesis_folder: "投资论点"
  chartsview: false
```

## Sync Behavior

`macro-regime obsidian-sync` copies pending reports from:

```text
~/.macro-regime/reports/macro_weekly_reports/
```

to:

```text
<vault>/<macro_folder>/
```

Synced reports are moved into `_synced/` to avoid duplicate writes.

## Thesis Feedback

Dry-run:

```bash
macro-regime thesis-feedback
```

Apply:

```bash
macro-regime thesis-feedback --apply
```

Only the bounded block is written:

```md
<!-- MACRO-REGIME-FEEDBACK:START -->
...
<!-- MACRO-REGIME-FEEDBACK:END -->
```

