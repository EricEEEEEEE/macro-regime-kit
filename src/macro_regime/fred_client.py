from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .regime import SERIES_META, build_indicator, build_stale_indicator


def fetch_indicators(api_key: str, cfg: dict[str, Any], old_state: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    try:
        from fredapi import Fred
    except ImportError as exc:  # pragma: no cover - packaging error path
        raise RuntimeError("Missing dependency: fredapi. Install macro-regime-kit with pipx or pip.") from exc

    fred_cfg = cfg["fred"]
    thresholds = cfg["regime"]["thresholds"]
    fetch_days = int(fred_cfg.get("fetch_days", 800))
    observation_start = (date.today() - timedelta(days=fetch_days)).isoformat()
    series_ids = {
        "yield_30y": fred_cfg["series"].get("yield_30y", "DGS30"),
        "real_yield_30y": fred_cfg["series"].get("real_yield_30y", "DFII30"),
        "curve_2s10s": fred_cfg["series"].get("curve_2s10s", "T10Y2Y"),
        "dxy": fred_cfg["series"].get("dxy", "DTWEXBGS"),
        "oil_wti": fred_cfg["series"].get("oil_wti", "DCOILWTICO"),
        "cpi_yoy": fred_cfg["series"].get("cpi", "CPIAUCSL"),
    }

    fred = Fred(api_key=api_key)
    indicators: dict[str, dict[str, Any]] = {}
    logs: list[str] = []
    for name, series_id in series_ids.items():
        if name not in SERIES_META:
            continue
        try:
            series = fred.get_series(series_id, observation_start=observation_start)
            indicators[name] = build_indicator(name, series_id, series, thresholds, old_state)
            logs.append(f"FRED loaded {name}/{series_id} date={indicators[name].get('fred_date')}")
        except Exception as exc:  # noqa: BLE001
            message = f"{type(exc).__name__}: {exc}"
            old_indicator = old_state.get("indicators", {}).get(name, {})
            indicators[name] = build_stale_indicator(name, series_id, old_indicator, message)
            logs.append(f"FRED fetch failed for {name}/{series_id}: {message}")
    return indicators, logs

