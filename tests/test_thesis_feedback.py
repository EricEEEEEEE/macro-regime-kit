from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from macro_regime.thesis_feedback import thesis_feedback, update_block


class ThesisFeedbackTests(unittest.TestCase):
    def test_update_block_is_bounded(self) -> None:
        text = "# Note\n\nBody\n"
        updated = update_block(text, "TEST", "- macro")
        self.assertIn("<!-- TEST:START -->", updated)
        self.assertIn("<!-- TEST:END -->", updated)
        updated_again = update_block(updated, "TEST", "- new")
        self.assertIn("- new", updated_again)
        self.assertNotIn("- macro", updated_again)

    def test_thesis_feedback_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note_dir = root / "vault" / "投资论点" / "NVDA"
            note_dir.mkdir(parents=True)
            note = note_dir / "note.md"
            note.write_text("# NVDA\n")
            cfg = {
                "obsidian": {"vault_path": str(root / "vault"), "thesis_folder": "投资论点"},
                "thesis_feedback": {"block_marker": "MACRO"},
            }
            state = {"regime": {"dominant_label": "Act 1"}, "portfolio_transmission": {}}

            results = thesis_feedback(cfg, state, apply=False)

            self.assertEqual(results[0]["status"], "changed")
            self.assertEqual(note.read_text(), "# NVDA\n")


if __name__ == "__main__":
    unittest.main()

