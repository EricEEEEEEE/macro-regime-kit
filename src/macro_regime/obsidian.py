from __future__ import annotations

import filecmp
import shutil
from pathlib import Path
from typing import Any

from .util import expand_path


def obsidian_macro_dir(cfg: dict[str, Any]) -> Path:
    obsidian = cfg.get("obsidian", {})
    vault = str(obsidian.get("vault_path") or "").strip()
    folder = str(obsidian.get("macro_folder") or "宏观追踪").strip()
    if not vault:
        raise RuntimeError("obsidian.vault_path is not configured")
    path = expand_path(vault) / folder
    if not path.exists() or not path.is_dir():
        raise RuntimeError(f"Obsidian macro folder unavailable: {path}")
    return path


def pending_reports(reports_dir: Path) -> list[Path]:
    source_dir = reports_dir / "macro_weekly_reports"
    if not source_dir.exists():
        return []
    return sorted(path for path in source_dir.glob("*.md") if path.is_file())


def move_to_synced(path: Path) -> Path:
    synced_dir = path.parent / "_synced"
    synced_dir.mkdir(parents=True, exist_ok=True)
    target = synced_dir / path.name
    if target.exists():
        target.unlink()
    return path.rename(target)


def sync_reports(cfg: dict[str, Any], reports_dir: Path, archive: bool = True) -> list[dict[str, str]]:
    vault_dir = obsidian_macro_dir(cfg)
    results: list[dict[str, str]] = []
    for src in pending_reports(reports_dir):
        dst = vault_dir / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
            archived = move_to_synced(src) if archive else src
            results.append({"status": "copied", "source": str(src), "target": str(dst), "archived": str(archived)})
        elif filecmp.cmp(src, dst, shallow=False):
            archived = move_to_synced(src) if archive else src
            results.append({"status": "already_synced", "source": str(src), "target": str(dst), "archived": str(archived)})
        elif src.stat().st_mtime > dst.stat().st_mtime:
            shutil.copy2(src, dst)
            archived = move_to_synced(src) if archive else src
            results.append({"status": "updated", "source": str(src), "target": str(dst), "archived": str(archived)})
        else:
            results.append({"status": "conflict", "source": str(src), "target": str(dst)})
    return results

