from __future__ import annotations

from pathlib import Path
from typing import Any

from .util import expand_path


def thesis_dir(cfg: dict[str, Any]) -> Path:
    obsidian = cfg.get("obsidian", {})
    vault = str(obsidian.get("vault_path") or "").strip()
    folder = str(obsidian.get("thesis_folder") or "投资论点").strip()
    if not vault:
        raise RuntimeError("obsidian.vault_path is not configured")
    path = expand_path(vault) / folder
    if not path.exists() or not path.is_dir():
        raise RuntimeError(f"Obsidian thesis folder unavailable: {path}")
    return path


def macro_feedback_text(state: dict[str, Any]) -> str:
    transmission = state.get("portfolio_transmission", {})
    regime = state.get("regime", {})
    high_beta = transmission.get("high_beta_assets") or []
    top = ", ".join(item["factor"] for item in high_beta[:5]) or "none"
    return "\n".join(
        [
            f"- Current macro regime: {regime.get('dominant_label', 'unknown')}.",
            f"- Regime reasoning: {state.get('regime_reasoning', '')}",
            f"- High-beta watchlist from portfolio transmission: {top}.",
            f"- Real-yield rule: {transmission.get('real_yield_break_2_7_hint', 'Watch 30Y real yield > 2.7%.')}",
            "- This block is generated context, not an investment recommendation.",
        ]
    )


def update_block(text: str, marker: str, block: str) -> str:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    replacement = f"{start}\n{block.rstrip()}\n{end}"
    if start in text and end in text:
        prefix, rest = text.split(start, 1)
        _, suffix = rest.split(end, 1)
        return prefix.rstrip() + "\n\n" + replacement + "\n" + suffix.lstrip()
    return text.rstrip() + "\n\n" + replacement + "\n"


def thesis_feedback(cfg: dict[str, Any], state: dict[str, Any], apply: bool = False) -> list[dict[str, str]]:
    marker = str(cfg.get("thesis_feedback", {}).get("block_marker") or "MACRO-REGIME-FEEDBACK")
    root = thesis_dir(cfg)
    block = macro_feedback_text(state)
    results: list[dict[str, str]] = []
    for path in sorted(root.rglob("*.md")):
        old = path.read_text()
        new = update_block(old, marker, block)
        changed = new != old
        if apply and changed:
            path.write_text(new)
        results.append({"path": str(path), "status": "changed" if changed else "unchanged", "applied": str(bool(apply and changed))})
    return results

