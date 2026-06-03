from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from macro_regime.portfolio import build_portfolio_transmission


class PortfolioTests(unittest.TestCase):
    def test_missing_portfolio_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = {"regime": {"dominant": "act_1_1970s_stagflation"}, "indicators": {}}
            result = build_portfolio_transmission(state, Path(tmp) / "missing.json")
            self.assertFalse(result["available"])

    def test_high_beta_assets_are_ranked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            risk_path = Path(tmp) / "portfolio_risk.json"
            risk_path.write_text(
                json.dumps(
                    {
                        "updated": "2026-06-03",
                        "total_delta": {
                            "btc_plus_1pct_usd": 100,
                            "beta_by_factor": {"ETH": 1.4, "SOL": 1.8, "CASH": 0.0},
                        },
                        "exposures_usd": {"ETH": 10000, "SOL": 5000, "CASH": 20000},
                    }
                )
            )
            state = {
                "regime": {"dominant": "act_1_1970s_stagflation"},
                "indicators": {"real_yield_30y": {"value": 2.8}},
            }
            result = build_portfolio_transmission(state, risk_path)
            self.assertTrue(result["available"])
            self.assertEqual([item["factor"] for item in result["high_beta_assets"]], ["SOL", "ETH"])
            self.assertIn("above the 2.7%", result["real_yield_break_2_7_hint"])


if __name__ == "__main__":
    unittest.main()

