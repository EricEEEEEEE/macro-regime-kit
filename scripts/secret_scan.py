#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
ALLOWLIST = {
    ".env.example:FRED_API_KEY=",
    ".env.example:OPENAI_API_KEY=",
    "README.md:FRED_API_KEY=your_key_here",
    "docs/quickstart.md:FRED_API_KEY=your_key_here",
    "src/macro_regime/cli.py:FRED_API_KEY=\\n",
    "AGENTS.md:rg -n",
    "scripts/secret_scan.py:re.compile",
}

PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}"),
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
    re.compile(r"iCloud~md~obsidian"),
    re.compile(r"FAB笔记"),
    re.compile(r"TELEGRAM|chat_id|3858718664"),
]


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if any(part.endswith(".egg-info") for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return files


def allowed(rel: str, line: str) -> bool:
    text = f"{rel}:{line.strip()}"
    return any(item in text for item in ALLOWLIST)


def main() -> int:
    findings: list[str] = []
    for path in iter_files():
        rel = str(path.relative_to(ROOT))
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, start=1):
            if allowed(rel, line):
                continue
            for pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel}:{lineno}: {line.strip()}")
                    break
    if findings:
        print("Potential secrets or private paths found:")
        for item in findings:
            print(f"  {item}")
        return 1
    print("secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
