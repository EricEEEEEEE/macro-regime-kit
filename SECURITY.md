# Security Policy

## Supported Versions

The `main` branch and the latest tagged release receive security fixes.

## Reporting a Vulnerability

Open a private security advisory on GitHub if available. If not, open an issue with minimal reproduction details and no secrets.

Do not post:

- API keys
- Broker account IDs
- Wallet private keys
- Real portfolio snapshots
- Obsidian vault paths containing private names

## Project Safety Boundary

Macro Regime Kit is research infrastructure. It must not:

- Place trades
- Transfer funds
- Withdraw assets
- Sign wallet transactions
- Request wallet private keys
- Require broker trading permissions

All broker, exchange, and wallet integrations must be read-only.

