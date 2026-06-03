from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from importlib import resources
from pathlib import Path
from typing import Any

from . import __version__
from .config import APP_HOME, config_path, ensure_runtime_dirs, load_config, load_env, reports_dir, state_path, write_default_config
from .fred_client import fetch_indicators
from .obsidian import sync_reports
from .portfolio import build_portfolio_transmission
from .regime import build_state
from .thesis_feedback import thesis_feedback
from .util import append_jsonl, expand_path, load_json, write_json
from .weekly import write_weekly_report


def cmd_init(args: argparse.Namespace) -> int:
    target = config_path(args.config)
    write_default_config(target)
    APP_HOME.mkdir(parents=True, exist_ok=True)
    env_path = APP_HOME / ".env"
    if not env_path.exists():
        env_path.write_text("FRED_API_KEY=\n")
    cfg = load_config(str(target))
    ensure_runtime_dirs(cfg)
    print(f"created config: {target}")
    print(f"created env: {env_path}")
    print("edit FRED_API_KEY before running macro-regime run")
    return 0


def load_state(cfg: dict[str, Any]) -> dict[str, Any]:
    return load_json(state_path(cfg, "macro_regime_state.json"))


def save_state(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    write_json(state_path(cfg, "macro_regime_state.json"), state)
    append_jsonl(state_path(cfg, "macro_regime_history.jsonl"), state)


def cmd_doctor(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    env = load_env()
    ensure_runtime_dirs(cfg)
    checks: list[tuple[str, bool, str]] = [
        ("config", True, str(config_path(args.config))),
        ("FRED_API_KEY", bool(env.get("FRED_API_KEY")), "set" if env.get("FRED_API_KEY") else "missing"),
        ("state_dir", expand_path(cfg["state_dir"]).exists(), str(expand_path(cfg["state_dir"]))),
        ("reports_dir", expand_path(cfg["reports_dir"]).exists(), str(expand_path(cfg["reports_dir"]))),
    ]
    obsidian = cfg.get("obsidian", {})
    if obsidian.get("enabled"):
        vault = expand_path(obsidian.get("vault_path", ""))
        checks.append(("obsidian_vault", vault.exists(), str(vault)))
    risk_path = expand_path(cfg["portfolio"]["risk_state_path"])
    checks.append(("portfolio_risk", risk_path.exists(), str(risk_path) if risk_path.exists() else "optional; skipped if missing"))

    failed = False
    for name, ok, detail in checks:
        print(f"[{'OK' if ok else 'WARN'}] {name}: {detail}")
        if name in {"FRED_API_KEY"} and not ok:
            failed = True
    return 1 if failed else 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    env = load_env()
    api_key = env.get("FRED_API_KEY", "")
    if not api_key:
        print("[FATAL] FRED_API_KEY missing. Put it in ~/.macro-regime/.env or environment.")
        return 1
    ensure_runtime_dirs(cfg)
    old_state = load_state(cfg)
    indicators, logs = fetch_indicators(api_key, cfg, old_state)
    state = build_state(indicators, old_state)
    state["logs"] = logs
    if cfg.get("portfolio", {}).get("enabled", True):
        risk_path = expand_path(cfg["portfolio"]["risk_state_path"])
        threshold = float(cfg["portfolio"].get("high_beta_threshold", 1.0))
        state["portfolio_transmission"] = build_portfolio_transmission(state, risk_path, threshold)
    save_state(cfg, state)
    print_summary(cfg, state)
    stale = [name for name, item in indicators.items() if item.get("stale")]
    if len(stale) == len(indicators):
        print("[FATAL] all FRED series stale; previous values preserved where available")
        return 1
    if stale:
        print(f"[WARN] stale series: {', '.join(stale)}")
    return 0


def cmd_portfolio(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    state = load_state(cfg)
    if not state:
        print("[FATAL] macro state missing; run macro-regime run first")
        return 1
    risk_path = expand_path(cfg["portfolio"]["risk_state_path"])
    threshold = float(cfg["portfolio"].get("high_beta_threshold", 1.0))
    state["portfolio_transmission"] = build_portfolio_transmission(state, risk_path, threshold)
    save_state(cfg, state)
    print(f"portfolio_transmission: {state['portfolio_transmission'].get('reason') or 'updated'}")
    return 0


def cmd_weekly(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    state = load_state(cfg)
    if not state:
        print("[FATAL] macro state missing; run macro-regime run first")
        return 1
    target = write_weekly_report(state, reports_dir(cfg), date.fromisoformat(args.date) if args.date else None)
    print(f"wrote {target}")
    return 0


def cmd_obsidian_sync(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    try:
        results = sync_reports(cfg, reports_dir(cfg), archive=not args.no_archive)
    except Exception as exc:  # noqa: BLE001
        print(f"[FATAL] {type(exc).__name__}: {exc}")
        return 1
    if not results:
        print("pending=0")
        return 0
    conflicts = 0
    for item in results:
        print(f"[{item['status']}] {item['source']} -> {item.get('target', '')}")
        conflicts += int(item["status"] == "conflict")
    return 2 if conflicts else 0


def cmd_thesis_feedback(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    state = load_state(cfg)
    if not state:
        print("[FATAL] macro state missing; run macro-regime run first")
        return 1
    try:
        results = thesis_feedback(cfg, state, apply=args.apply)
    except Exception as exc:  # noqa: BLE001
        print(f"[FATAL] {type(exc).__name__}: {exc}")
        return 1
    for item in results[:50]:
        print(f"[{item['status']}] applied={item['applied']} {item['path']}")
    if len(results) > 50:
        print(f"... {len(results) - 50} more files")
    return 0


def cmd_skill_install(args: argparse.Namespace) -> int:
    source = resources.files("macro_regime").joinpath("resources/skills/macro-regime-monitor")
    target_root = expand_path(args.target)
    target = target_root / "macro-regime-monitor"
    target_root.mkdir(parents=True, exist_ok=True)
    if target.exists() and not args.force:
        print(f"[FATAL] skill already exists: {target}")
        print("rerun with --force to overwrite")
        return 1
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    print(f"installed skill: {target}")
    return 0


def print_summary(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    print("Macro Regime Kit")
    print(f"  updated={state['updated_at']}")
    for name, item in state.get("indicators", {}).items():
        stale = " [stale]" if item.get("stale") else ""
        changed = " changed" if item.get("status_changed") else ""
        print(f"  {name} ({item['series_id']}): {item['display']} [{item['status']}]{stale}{changed}")
    probs = state["regime"]["probabilities"]
    print(
        "  regime="
        f"{state['regime']['dominant_label']} "
        f"act1={probs['act_1_1970s_stagflation']:.2%} "
        f"act2={probs['act_2_1994_bond_vigilantes']:.2%} "
        f"act3={probs['act_3_financial_repression']:.2%}"
    )
    print(f"  wrote {state_path(cfg, 'macro_regime_state.json')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="macro-regime")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", help="Path to config.yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="Create default ~/.macro-regime config and env files")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("doctor", help="Check local configuration")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("run", help="Fetch FRED data, score regimes, and write state")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("portfolio", help="Recompute portfolio transmission from portfolio_risk.json")
    p.set_defaults(func=cmd_portfolio)

    p = sub.add_parser("weekly", help="Render a macro weekly markdown report")
    p.add_argument("--date", help="Report date YYYY-MM-DD")
    p.set_defaults(func=cmd_weekly)

    p = sub.add_parser("obsidian-sync", help="Copy pending weekly reports into Obsidian")
    p.add_argument("--no-archive", action="store_true", help="Do not move synced reports into _synced")
    p.set_defaults(func=cmd_obsidian_sync)

    p = sub.add_parser("thesis-feedback", help="Dry-run or apply macro feedback blocks to thesis markdown files")
    p.add_argument("--apply", action="store_true", help="Write changes. Default is dry-run only.")
    p.set_defaults(func=cmd_thesis_feedback)

    p = sub.add_parser("skill-install", help="Install the bundled AI skill into a local skill directory")
    p.add_argument("--target", default="~/.codex/skills", help="Skill root directory, e.g. ~/.codex/skills or ~/.claude/skills")
    p.add_argument("--force", action="store_true", help="Overwrite an existing macro-regime-monitor skill")
    p.set_defaults(func=cmd_skill_install)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
