from __future__ import annotations

from pathlib import Path
from typing import Any

from .util import fnum, load_json


def build_portfolio_transmission(
    state: dict[str, Any],
    risk_path: Path,
    high_beta_threshold: float = 1.0,
) -> dict[str, Any]:
    if not risk_path.exists():
        return {
            "available": False,
            "source": str(risk_path),
            "reason": "portfolio risk state not found; skipped",
        }

    payload = load_json(risk_path)
    total_delta = payload.get("total_delta", {})
    beta_by_factor = total_delta.get("beta_by_factor", {})
    exposures = payload.get("exposures_usd", {})
    if not isinstance(beta_by_factor, dict):
        return {
            "available": False,
            "source": str(risk_path),
            "reason": "total_delta.beta_by_factor missing or not an object",
        }

    high_beta = []
    for factor, beta_raw in beta_by_factor.items():
        beta = fnum(beta_raw, 0.0) or 0.0
        if beta <= high_beta_threshold:
            continue
        exposure = fnum(exposures.get(factor), 0.0) or 0.0
        high_beta.append(
            {
                "factor": factor,
                "beta_to_btc": round(beta, 4),
                "exposure_usd": round(exposure, 2),
                "btc_plus_1pct_contribution_usd": round(exposure * beta * 0.01, 2),
            }
        )
    high_beta.sort(
        key=lambda item: (item["beta_to_btc"], abs(item["btc_plus_1pct_contribution_usd"])),
        reverse=True,
    )

    dominant = state.get("regime", {}).get("dominant")
    if dominant == "act_3_financial_repression":
        regime_hint = "Financial repression dominant: real yields are contained; watch dollar/liquidity pressure."
    elif dominant == "act_2_1994_bond_vigilantes":
        regime_hint = "Bond-vigilante dominant: steepening curve can pressure high-beta and long-duration assets first."
    else:
        regime_hint = "Stagflation/tightening dominant: high CPI plus real-yield pressure can compress growth and crypto multiples."

    indicators = state.get("indicators", {})
    real_yield = fnum(indicators.get("real_yield_30y", {}).get("value"))
    watched = ", ".join(item["factor"] for item in high_beta[:5]) or "none"
    if real_yield is not None and real_yield > 2.7:
        real_yield_hint = (
            f"30Y real yield is {real_yield:.2f}% and above the 2.7% hard-tightening line; "
            f"review beta>1 exposure: {watched}."
        )
    else:
        real_yield_hint = (
            "If 30Y real yield breaks above 2.7%, treat it as a hard-tightening line and "
            f"review beta>1 exposure: {watched}."
        )

    return {
        "available": True,
        "source": str(risk_path),
        "portfolio_updated": payload.get("updated"),
        "btc_plus_1pct_usd": total_delta.get("btc_plus_1pct_usd"),
        "beta_by_factor": beta_by_factor,
        "high_beta_assets": high_beta,
        "dominant_regime_hint": regime_hint,
        "real_yield_break_2_7_hint": real_yield_hint,
    }

