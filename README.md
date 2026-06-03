# Macro Regime Kit

FRED macro-regime monitoring for investors who keep research notes in Obsidian and want an AI agent such as Claude Code or Codex to help run, verify, and interpret the workflow.

The kit does three things:

1. Fetches macro data from FRED.
2. Scores a three-act macro regime model.
3. Writes machine-readable state and Obsidian-ready weekly reports, with optional portfolio transmission and thesis feedback.

It does **not** trade, rebalance, move assets, or require wallet private keys.

## What It Monitors

Default FRED series:

| Field | FRED series | Meaning |
|---|---:|---|
| `yield_30y` | `DGS30` | 30Y Treasury yield |
| `real_yield_30y` | `DFII30` | 30Y TIPS real yield |
| `curve_2s10s` | `T10Y2Y` | 10Y minus 2Y curve, converted to bps |
| `dxy` | `DTWEXBGS` | Trade-weighted US dollar index |
| `oil_wti` | `DCOILWTICO` | WTI crude oil |
| `cpi_yoy` | `CPIAUCSL` | CPI YoY, calculated from latest CPI versus 12 months prior |

Default regime model:

| Act | Label | Core signal |
|---|---|---|
| Act 1 | 1970s stagflation | High CPI plus high/rising real yields |
| Act 2 | 1994 bond vigilantes | Steepening curve plus nominal yield pressure |
| Act 3 | Financial repression | High nominal yields while real yields are suppressed |

Act 2 deliberately does not include Treasury auction stress or cross-asset "three-way selloff" signals. The weekly report marks that blind spot so a human or AI agent can check it separately.

## Install

### Option A: From GitHub

```bash
pipx install git+https://github.com/EricEEEEEEE/macro-regime-kit.git
```

### Option B: Local development

```bash
git clone https://github.com/EricEEEEEEE/macro-regime-kit.git
cd macro-regime-kit
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Verify:

```bash
macro-regime --version
macro-regime init
macro-regime doctor
```

## Setup SOP

### 1. Install Obsidian

Download Obsidian from the official site:

```text
https://obsidian.md/download
```

Create a vault with folders like:

```text
Investment Vault/
├── 宏观追踪/
├── 投资论点/
└── 仓位/
```

Avoid using multiple sync engines on the same vault at the same time. If you use iCloud, do not also use another sync service for the same files.

### 2. Get a FRED API Key

Create a FRED API key:

```text
https://fred.stlouisfed.org/docs/api/api_key.html
```

Put it in:

```bash
~/.macro-regime/.env
```

```bash
FRED_API_KEY=your_key_here
```

### 3. Configure the Kit

Initialize:

```bash
macro-regime init
```

Edit:

```bash
~/.macro-regime/config.yaml
```

Minimal Obsidian configuration:

```yaml
obsidian:
  enabled: true
  vault_path: "/path/to/Investment Vault"
  macro_folder: "宏观追踪"
  thesis_folder: "投资论点"
```

### 4. Run the First Macro State

```bash
macro-regime doctor
macro-regime run
macro-regime weekly
macro-regime obsidian-sync
```

Expected files:

```text
~/.macro-regime/state/macro_regime_state.json
~/.macro-regime/state/macro_regime_history.jsonl
~/.macro-regime/reports/macro_weekly_reports/YYYY-MM-DD.md
<vault>/宏观追踪/YYYY-MM-DD.md
```

### 5. Optional Portfolio Transmission

Macro Regime Kit expects a read-only portfolio risk state. It does not need broker trading credentials.

Create:

```text
~/.macro-regime/state/portfolio_risk.json
```

Minimum schema:

```json
{
  "updated": "2026-06-03",
  "total_delta": {
    "btc_plus_1pct_usd": 1234.56,
    "beta_by_factor": {
      "BTC": 1.0,
      "ETH": 1.4,
      "SOL": 1.8,
      "NVDA": 1.2
    }
  },
  "exposures_usd": {
    "BTC": 50000,
    "ETH": 20000,
    "SOL": 10000,
    "NVDA": 15000
  }
}
```

Then run:

```bash
macro-regime portfolio
macro-regime weekly
macro-regime obsidian-sync
```

### 6. Optional Thesis Feedback

Dry-run first:

```bash
macro-regime thesis-feedback
```

Apply only after reviewing the output:

```bash
macro-regime thesis-feedback --apply
```

The command writes a bounded Markdown block:

```md
<!-- MACRO-REGIME-FEEDBACK:START -->
...
<!-- MACRO-REGIME-FEEDBACK:END -->
```

It does not rewrite the rest of the note.

## AI Agent Setup

### Codex

Install and sign in to Codex using OpenAI's official instructions:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex
```

Then tell Codex:

```text
Use the macro-regime-monitor skill.
Run macro-regime doctor.
Do not edit my Obsidian vault or credentials.
Explain what is missing and give exact next steps.
```

### Claude Code

Install Claude Code using Anthropic's current instructions, then point it at this repository or at your local macro-regime configuration. The included skill can be copied into your Claude/Codex skill directory and used as an operating playbook.

## Skill

The AI skill lives here:

```text
skills/macro-regime-monitor/
```

If you installed the CLI with `pipx`, export the bundled skill:

```bash
macro-regime skill-install --target ~/.codex/skills
```

For Claude Code:

```bash
macro-regime skill-install --target ~/.claude/skills
```

It is intentionally small. The deterministic logic lives in the CLI; the skill tells an AI agent how to run, verify, explain, and safely apply the workflow.

## Broker and Exchange Data

This project does not ship trading adapters. That is intentional.

Recommended source pattern:

| Source | Recommended read-only input | What to export |
|---|---|---|
| Interactive Brokers | Flex Web Service | cash, open positions, option legs, net liquidation |
| Tiger Brokers | OpenAPI read-only account endpoints | cash, positions, net liquidation |
| Binance | read-only API key | spot balances, Earn balances, stablecoins |
| On-chain wallets | public wallet address + RPC/API | token balances and DeFi collateral/debt |
| Manual fallback | CSV or JSON | positions, exposures, beta factors |

Feed those into `portfolio_risk.json`. The macro kit consumes only the risk state, not live trading credentials.

## Automation

macOS launchd or Linux cron can run:

```bash
macro-regime run
macro-regime portfolio
macro-regime weekly
macro-regime obsidian-sync
```

Keep `thesis-feedback --apply` manual unless you have reviewed the dry-run behavior.

## Security Rules

- Never commit `.env`.
- Use read-only exchange or broker credentials.
- Do not grant trading, withdrawal, transfer, or wallet-signing permissions.
- Treat stale data as stale. Do not invent missing values.
- Obsidian writes are local Markdown writes only.
- Thesis feedback defaults to dry-run.

## Development

```bash
python3 -m unittest discover tests
python3 -m macro_regime.cli --version
```

## Disclaimer

Macro Regime Kit is research infrastructure. It is not financial advice and does not execute trades.
