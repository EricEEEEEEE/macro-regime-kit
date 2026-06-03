from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from macro_regime.obsidian import sync_reports


class ObsidianTests(unittest.TestCase):
    def test_sync_reports_copies_and_archives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports" / "macro_weekly_reports"
            vault_macro = root / "vault" / "宏观追踪"
            reports.mkdir(parents=True)
            vault_macro.mkdir(parents=True)
            (reports / "2026-06-03.md").write_text("# report\n")
            cfg = {"obsidian": {"vault_path": str(root / "vault"), "macro_folder": "宏观追踪"}}

            results = sync_reports(cfg, root / "reports")

            self.assertEqual(results[0]["status"], "copied")
            self.assertTrue((vault_macro / "2026-06-03.md").exists())
            self.assertTrue((reports / "_synced" / "2026-06-03.md").exists())


if __name__ == "__main__":
    unittest.main()

