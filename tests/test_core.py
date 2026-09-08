import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from document_workflow.core import classify_text, extract_text, load_rules


class CoreTests(unittest.TestCase):
    def test_extracts_supported_formats_as_normalized_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = {
                "note.txt": "  Quarterly   invoice\n\n ready ",
                "note.md": "# Quarterly\n\ninvoice ready",
                "note.csv": "name,status\nInvoice,ready\n",
                "note.json": json.dumps({"name": "Invoice", "status": "ready"}),
            }
            for name, content in cases.items():
                path = root / name
                path.write_text(content, encoding="utf-8")
                with self.subTest(name=name):
                    text = extract_text(path)
                    self.assertNotRegex(text, r"\s{2,}")
                    self.assertIn("Invoice".lower(), text.lower())
                    self.assertIn("ready", text.lower())

    def test_loads_rules_and_classifies_by_priority_then_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            rules_path = Path(directory) / "rules.json"
            rules_path.write_text(
                json.dumps(
                    {
                        "fallback": "other",
                        "categories": [
                            {"name": "finance", "keywords": ["invoice", "payment"]},
                            {"name": "legal", "keywords": ["contract"]},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            rules = load_rules(rules_path)
            self.assertEqual("finance", classify_text("Contract invoice", rules))
            self.assertEqual("other", classify_text("Team lunch", rules))

    def test_trims_keyword_whitespace_from_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            rules_path = Path(directory) / "rules.json"
            rules_path.write_text(
                json.dumps(
                    {
                        "fallback": "other",
                        "categories": [{"name": "finance", "keywords": [" invoice "]}],
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual("finance", classify_text("Invoice ready", load_rules(rules_path)))

    def test_rejects_category_names_that_can_escape_output(self):
        with tempfile.TemporaryDirectory() as directory:
            rules_path = Path(directory) / "rules.json"
            rules_path.write_text(
                json.dumps(
                    {
                        "fallback": "../outside",
                        "categories": [{"name": "finance", "keywords": ["invoice"]}],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Invalid rules file"):
                load_rules(rules_path)


if __name__ == "__main__":
    unittest.main()
