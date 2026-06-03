# Portfolio Risk Schema

Macro Regime Kit consumes a portfolio risk file. It does not need broker trading credentials.

Default path:

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

## Interpretation

- `btc_plus_1pct_usd`: portfolio PnL if BTC rises 1%, under your risk model.
- `beta_by_factor`: factor beta used for ranking high-beta assets.
- `exposures_usd`: optional exposure values used for contribution estimates.

## Read-Only Adapter Pattern

Adapters should produce the schema above. They must not trade or transfer funds.

Recommended data sources:

| Source | Read-only input | Output |
|---|---|---|
| Interactive Brokers | Flex report | positions, cash, option legs |
| Binance | read-only API | spot/Earn balances |
| Public wallets | addresses only | token balances |
| Manual | CSV/JSON | exposures and beta factors |

