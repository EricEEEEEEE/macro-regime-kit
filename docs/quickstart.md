# Quickstart

## 1. Install

```bash
pipx install git+https://github.com/EricEEEEEEE/macro-regime-kit.git
```

## 2. Initialize

```bash
macro-regime init
```

Edit:

```text
~/.macro-regime/.env
~/.macro-regime/config.yaml
```

## 3. Add FRED API Key

```bash
FRED_API_KEY=your_key_here
```

## 4. Run

```bash
macro-regime doctor
macro-regime run
macro-regime weekly
```

## 5. Optional Obsidian Sync

Set:

```yaml
obsidian:
  enabled: true
  vault_path: "/path/to/Investment Vault"
  macro_folder: "宏观追踪"
```

Then:

```bash
macro-regime obsidian-sync
```

