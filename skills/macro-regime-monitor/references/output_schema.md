# Output Schema

## `macro_regime_state.json`

Required top-level fields:

- `updated`
- `updated_at`
- `source`
- `regime`
- `regime_reasoning`
- `act2_note`
- `indicators`
- `portfolio_transmission`
- `what_changed`

Each indicator includes:

- `series_id`
- `value`
- `value_prev`
- `display`
- `fred_date`
- `status`
- `status_prev`
- `status_changed`
- `stale`

Stale values must be marked with `stale: true`. Do not invent substitute values.

## `portfolio_risk.json`

Minimum consumed schema:

```json
{
  "updated": "YYYY-MM-DD",
  "total_delta": {
    "btc_plus_1pct_usd": 0,
    "beta_by_factor": {
      "ETH": 1.4
    }
  },
  "exposures_usd": {
    "ETH": 10000
  }
}
```

