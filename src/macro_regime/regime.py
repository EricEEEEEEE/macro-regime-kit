from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd

from .util import clamp, fnum


SGT = timezone(timedelta(hours=8))

SERIES_META = {
    "yield_30y": {"label": "30Y Treasury yield", "unit": "pct"},
    "real_yield_30y": {"label": "30Y TIPS real yield", "unit": "pct"},
    "curve_2s10s": {"label": "10Y-2Y curve", "unit": "bps"},
    "dxy": {"label": "Trade-weighted US dollar index", "unit": "index"},
    "oil_wti": {"label": "WTI crude oil", "unit": "usd"},
    "cpi_yoy": {"label": "CPI YoY", "unit": "pct"},
}

REGIME_NAMES = {
    "act_1_1970s_stagflation": "Act 1: 1970s stagflation",
    "act_2_1994_bond_vigilantes": "Act 2: 1994 bond vigilantes",
    "act_3_financial_repression": "Act 3: financial repression",
}


@dataclass(frozen=True)
class FredSeries:
    name: str
    series_id: str


def format_value(value: float | None, unit: str) -> str:
    if value is None:
        return "N/A"
    if unit == "pct":
        return f"{value:.2f}%"
    if unit == "bps":
        return f"{value:.1f} bps"
    if unit == "usd":
        return f"${value:.2f}"
    return f"{value:.2f}"


def status_for(name: str, value: float | None, thresholds: dict[str, Any]) -> str:
    if value is None:
        return "stale"
    if name == "yield_30y":
        if value > float(thresholds["yield_30y_red_gt"]):
            return "red"
        if value >= float(thresholds["yield_30y_green_lt"]):
            return "amber"
        return "green"
    if name == "real_yield_30y":
        if value > float(thresholds["real_yield_red_gt"]):
            return "red"
        if value >= float(thresholds["real_yield_green_lt"]):
            return "amber"
        return "green"
    if name == "curve_2s10s":
        if value < float(thresholds["curve_inversion_bps_lt"]):
            return "red"
        if value > float(thresholds["curve_steep_bps_gt"]):
            return "amber"
        return "green"
    if name == "cpi_yoy":
        if value > float(thresholds["cpi_red_gt"]):
            return "red"
        if value >= float(thresholds["cpi_green_lt"]):
            return "amber"
        return "green"
    if name in {"dxy", "oil_wti"}:
        return "amber"
    return "amber"


def latest_non_null(series: pd.Series) -> tuple[str, float]:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        raise RuntimeError("FRED returned no non-null observations")
    latest_date = clean.index[-1]
    return pd.Timestamp(latest_date).date().isoformat(), float(clean.iloc[-1])


def cpi_yoy_from_series(series: pd.Series) -> tuple[str, float, dict[str, Any]]:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if len(clean) < 13:
        raise RuntimeError(f"CPI needs at least 13 monthly observations; got {len(clean)}")
    latest_ts = pd.Timestamp(clean.index[-1])
    lag_month = (latest_ts - pd.DateOffset(months=12)).to_period("M")
    lag_slice = clean[clean.index.to_period("M") == lag_month]
    if lag_slice.empty:
        raise RuntimeError(f"CPI missing 12-month lag observation for {lag_month}")
    latest_value = float(clean.iloc[-1])
    lag_value = float(lag_slice.iloc[-1])
    if lag_value == 0:
        raise RuntimeError("CPI 12-month lag value is zero")
    yoy = (latest_value / lag_value - 1) * 100
    return (
        latest_ts.date().isoformat(),
        float(yoy),
        {
            "raw_cpi_latest": round(latest_value, 4),
            "raw_cpi_12m_ago": round(lag_value, 4),
            "lag_12m_date": pd.Timestamp(lag_slice.index[-1]).date().isoformat(),
        },
    )


def build_stale_indicator(name: str, series_id: str, old_indicator: dict[str, Any], error: str) -> dict[str, Any]:
    meta = SERIES_META[name]
    old_value = fnum(old_indicator.get("value"))
    old_status = old_indicator.get("status") if isinstance(old_indicator.get("status"), str) else "stale"
    return {
        "series_id": series_id,
        "label": meta["label"],
        "value": old_value,
        "value_prev": old_value,
        "unit": meta["unit"],
        "display": f"{format_value(old_value, meta['unit'])} [stale]",
        "fred_date": old_indicator.get("fred_date"),
        "status": old_status,
        "status_prev": old_status,
        "status_changed": False,
        "stale": True,
        "fetch_error": error,
    }


def build_indicator(
    name: str,
    series_id: str,
    series: pd.Series,
    thresholds: dict[str, Any],
    old_state: dict[str, Any],
) -> dict[str, Any]:
    meta = SERIES_META[name]
    old_indicator = old_state.get("indicators", {}).get(name, {})
    if name == "cpi_yoy":
        fred_date, value, extra = cpi_yoy_from_series(series)
        raw_value = extra["raw_cpi_latest"]
    else:
        fred_date, raw_value = latest_non_null(series)
        value = raw_value * 100 if name == "curve_2s10s" else raw_value
        extra = {}

    status = status_for(name, value, thresholds)
    prev_value = fnum(old_indicator.get("value"))
    prev_status = old_indicator.get("status") if isinstance(old_indicator.get("status"), str) else None
    indicator = {
        "series_id": series_id,
        "label": meta["label"],
        "value": round(value, 4),
        "value_prev": prev_value,
        "unit": meta["unit"],
        "display": format_value(value, meta["unit"]),
        "fred_date": fred_date,
        "status": status,
        "status_prev": prev_status,
        "status_changed": bool(prev_status and prev_status != status),
        "stale": False,
    }
    if name == "curve_2s10s":
        indicator["raw_pct_points"] = round(raw_value, 4)
    indicator.update(extra)
    return indicator


def normalize_probabilities(scores: dict[str, float]) -> dict[str, float]:
    total = sum(max(value, 0.0) for value in scores.values())
    if total <= 0:
        return {key: round(1 / len(scores), 4) for key in scores}
    keys = list(scores)
    normalized: dict[str, float] = {}
    running = 0.0
    for key in keys[:-1]:
        value = round(max(scores[key], 0.0) / total, 4)
        normalized[key] = value
        running += value
    normalized[keys[-1]] = round(max(0.0, 1.0 - running), 4)
    return normalized


def score_regimes(indicators: dict[str, dict[str, Any]]) -> dict[str, Any]:
    nominal = fnum(indicators.get("yield_30y", {}).get("value"))
    real = fnum(indicators.get("real_yield_30y", {}).get("value"))
    real_prev = fnum(indicators.get("real_yield_30y", {}).get("value_prev"))
    curve = fnum(indicators.get("curve_2s10s", {}).get("value"))
    cpi = fnum(indicators.get("cpi_yoy", {}).get("value"))

    cpi_pressure = clamp(((cpi or 0.0) - 3.0) / 1.5) if cpi is not None else 0.0
    real_pressure = clamp(((real or 0.0) - 2.0) / 0.7) if real is not None else 0.0
    if real is not None and real_prev is not None:
        real_up = clamp((real - real_prev) / 0.25)
    elif real is not None and real >= 2.0:
        real_up = 0.35
    else:
        real_up = 0.0

    curve_steep = clamp(((curve or 0.0) - 50.0) / 50.0) if curve is not None else 0.0
    nominal_pressure = clamp(((nominal or 0.0) - 4.5) / 1.0) if nominal is not None else 0.0
    real_low = clamp((2.0 - (real or 0.0)) / 2.0) if real is not None else 0.0

    scores = {
        "act_1_1970s_stagflation": 0.15 + 0.50 * cpi_pressure + 0.25 * real_pressure + 0.10 * real_up,
        "act_2_1994_bond_vigilantes": 0.15 + 0.60 * curve_steep + 0.25 * nominal_pressure,
        "act_3_financial_repression": 0.15 + 0.55 * nominal_pressure + 0.30 * real_low,
    }
    probabilities = normalize_probabilities(scores)
    dominant = max(probabilities.items(), key=lambda item: item[1])[0]
    return {
        "dominant": dominant,
        "dominant_label": REGIME_NAMES[dominant],
        "probabilities": probabilities,
        "scores": {key: round(value, 4) for key, value in scores.items()},
        "logic": [
            "Act 1: high CPI plus high/rising 30Y real yields.",
            "Act 2: steepening 2s10s curve plus nominal yield pressure; auction stress must be checked externally.",
            "Act 3: high nominal yields with suppressed or falling real yields.",
        ],
    }


def build_what_changed(indicators: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "indicator": name,
            "from": item.get("status_prev"),
            "to": item.get("status"),
            "value": item.get("display"),
            "fred_date": item.get("fred_date"),
        }
        for name, item in indicators.items()
        if item.get("status_changed")
    ]


def build_regime_reasoning(indicators: dict[str, dict[str, Any]], regime: dict[str, Any]) -> str:
    yield_30y = indicators.get("yield_30y", {})
    real_yield = indicators.get("real_yield_30y", {})
    curve = indicators.get("curve_2s10s", {})
    cpi = indicators.get("cpi_yoy", {})
    return (
        f"{regime.get('dominant_label', 'unknown')}: 30Y real yield {real_yield.get('display')} "
        f"({real_yield.get('status')}) and CPI YoY {cpi.get('display')} ({cpi.get('status')}) "
        f"drive the current score; nominal 30Y yield {yield_30y.get('display')} "
        f"({yield_30y.get('status')}) and 2s10s {curve.get('display')} ({curve.get('status')}) "
        "set the bond-vigilante versus repression balance."
    )


def build_state(indicators: dict[str, dict[str, Any]], old_state: dict[str, Any] | None = None) -> dict[str, Any]:
    old_state = old_state or {}
    regime = score_regimes(indicators)
    updated_at = datetime.now(SGT).isoformat(timespec="seconds")
    return {
        "updated": updated_at[:10],
        "updated_at": updated_at,
        "source": "FRED via fredapi",
        "current_act": regime["dominant_label"],
        "dominant_label": regime["dominant_label"],
        "regime": regime,
        "regime_reasoning": build_regime_reasoning(indicators, regime),
        "act2_note": "Auction / three-asset selloff soft signals are not included; check them in the weekly narrative.",
        "indicators": indicators,
        "portfolio_transmission": {"available": False, "reason": "not computed yet"},
        "what_changed": build_what_changed(indicators),
        "logs": [],
    }

