from __future__ import annotations

import unittest

import pandas as pd

from macro_regime.regime import cpi_yoy_from_series, normalize_probabilities, score_regimes, status_for


class RegimeTests(unittest.TestCase):
    def test_cpi_yoy_uses_12_month_lag(self) -> None:
        index = pd.date_range("2025-01-01", periods=14, freq="MS")
        values = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 115]
        series = pd.Series(values, index=index)

        latest_date, yoy, meta = cpi_yoy_from_series(series)

        self.assertEqual(latest_date, "2026-02-01")
        self.assertAlmostEqual(yoy, (115 / 101 - 1) * 100)
        self.assertEqual(meta["lag_12m_date"], "2025-02-01")

    def test_probability_sum_is_one(self) -> None:
        probs = normalize_probabilities({"a": 0.2, "b": 0.3, "c": 0.5})
        self.assertAlmostEqual(sum(probs.values()), 1.0)

    def test_status_thresholds(self) -> None:
        thresholds = {
            "yield_30y_green_lt": 5.0,
            "yield_30y_red_gt": 5.5,
            "real_yield_green_lt": 2.0,
            "real_yield_red_gt": 2.7,
            "curve_inversion_bps_lt": 0,
            "curve_steep_bps_gt": 100,
            "cpi_green_lt": 3.0,
            "cpi_red_gt": 4.5,
        }
        self.assertEqual(status_for("yield_30y", 4.9, thresholds), "green")
        self.assertEqual(status_for("yield_30y", 5.2, thresholds), "amber")
        self.assertEqual(status_for("yield_30y", 5.6, thresholds), "red")
        self.assertEqual(status_for("curve_2s10s", -1, thresholds), "red")
        self.assertEqual(status_for("curve_2s10s", 120, thresholds), "amber")

    def test_score_regimes_returns_dominant(self) -> None:
        indicators = {
            "yield_30y": {"value": 5.2},
            "real_yield_30y": {"value": 2.8, "value_prev": 2.5},
            "curve_2s10s": {"value": 20},
            "cpi_yoy": {"value": 4.2},
        }
        regime = score_regimes(indicators)
        self.assertIn(regime["dominant"], regime["probabilities"])
        self.assertAlmostEqual(sum(regime["probabilities"].values()), 1.0)


if __name__ == "__main__":
    unittest.main()

