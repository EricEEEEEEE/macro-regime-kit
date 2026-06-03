from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from .util import expand_path


APP_HOME = Path(os.environ.get("MACRO_REGIME_HOME", "~/.macro-regime")).expanduser()

DEFAULT_CONFIG: dict[str, Any] = {
    "state_dir": str(APP_HOME / "state"),
    "reports_dir": str(APP_HOME / "reports"),
    "logs_dir": str(APP_HOME / "logs"),
    "timezone": "Asia/Singapore",
    "fred": {
        "fetch_days": 800,
        "series": {
            "yield_30y": "DGS30",
            "real_yield_30y": "DFII30",
            "curve_2s10s": "T10Y2Y",
            "dxy": "DTWEXBGS",
            "oil_wti": "DCOILWTICO",
            "cpi": "CPIAUCSL",
        },
    },
    "regime": {
        "thresholds": {
            "yield_30y_green_lt": 5.0,
            "yield_30y_red_gt": 5.5,
            "real_yield_green_lt": 2.0,
            "real_yield_red_gt": 2.7,
            "curve_inversion_bps_lt": 0,
            "curve_steep_bps_gt": 100,
            "cpi_green_lt": 3.0,
            "cpi_red_gt": 4.5,
        }
    },
    "portfolio": {
        "enabled": True,
        "risk_state_path": str(APP_HOME / "state" / "portfolio_risk.json"),
        "high_beta_threshold": 1.0,
        "btc_factor_name": "BTC",
    },
    "obsidian": {
        "enabled": False,
        "vault_path": "",
        "macro_folder": "宏观追踪",
        "thesis_folder": "投资论点",
        "chartsview": False,
    },
    "thesis_feedback": {
        "enabled": False,
        "dry_run_default": True,
        "block_marker": "MACRO-REGIME-FEEDBACK",
    },
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def config_path(path: str | None = None) -> Path:
    if path:
        return expand_path(path)
    env_path = os.environ.get("MACRO_REGIME_CONFIG")
    if env_path:
        return expand_path(env_path)
    return APP_HOME / "config.yaml"


def load_config(path: str | None = None) -> dict[str, Any]:
    cfg_path = config_path(path)
    if not cfg_path.exists():
        return deepcopy(DEFAULT_CONFIG)
    payload = yaml.safe_load(cfg_path.read_text()) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"config must be a mapping: {cfg_path}")
    return deep_merge(DEFAULT_CONFIG, payload)


def write_default_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False, allow_unicode=True))


def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def load_env() -> dict[str, str]:
    env = load_env_file(APP_HOME / ".env")
    for key in ("FRED_API_KEY", "OPENAI_API_KEY"):
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


def state_path(cfg: dict[str, Any], filename: str) -> Path:
    return expand_path(cfg["state_dir"]) / filename


def reports_dir(cfg: dict[str, Any]) -> Path:
    return expand_path(cfg["reports_dir"])


def ensure_runtime_dirs(cfg: dict[str, Any]) -> None:
    for key in ("state_dir", "reports_dir", "logs_dir"):
        expand_path(cfg[key]).mkdir(parents=True, exist_ok=True)

