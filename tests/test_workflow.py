import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from document_workflow.core import load_rules
from document_workflow.workflow import process_documents


class WorkflowTests(unittest.TestCase):
    def test_recursively_copies_with_duplicate_safe_names_and_manifests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incoming = root / "incoming"
            output = root / "organized"
            (incoming / "a").mkdir(parents=True)
            (incoming / "b").mkdir(parents=True)
            source_a = incoming / "a" / "report.txt"
            source_b = incoming / "b" / "report.txt"
            source_a.write_text("Invoice alpha", encoding="utf-8")
            source_b.write_text("Invoice beta", encoding="utf-8")
            rules_path = root / "rules.json"
            rules_path.write_text(
                json.dumps(
                    {
                        "fallback": "other",
                        "categories": [{"name": "finance", "keywords": ["invoice"]}],
                    }
                ),
                encoding="utf-8",
            )

            summary = process_documents(incoming, output, load_rules(rules_path))

            self.assertEqual(2, summary.copied)
            copied = sorted(path.name for path in (output / "finance").iterdir())
            self.assertEqual(["report-2.txt", "report.txt"], copied)
            self.assertEqual("Invoice alpha", source_a.read_text(encoding="utf-8"))
            self.assertEqual("Invoice beta", source_b.read_text(encoding="utf-8"))
            json_manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(2, len(json_manifest["records"]))
            self.assertTrue((output / "manifest.csv").is_file())

    def test_records_invalid_json_and_unsupported_files_without_stopping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "broken.json").write_text("{not valid", encoding="utf-8")
            (incoming / "photo.png").write_bytes(b"not an image")
            (incoming / "good.md").write_text("invoice", encoding="utf-8")
            rules_path = root / "rules.json"
            rules_path.write_text(
                json.dumps(
                    {
                        "fallback": "other",
                        "categories": [{"name": "finance", "keywords": ["invoice"]}],
                    }
                ),
                encoding="utf-8",
            )

            summary = process_documents(incoming, root / "output", load_rules(rules_path))

            self.assertEqual((1, 1, 1), (summary.copied, summary.skipped, summary.errors))
            statuses = {record.source: record.status for record in summary.records}
            self.assertEqual("error", statuses["broken.json"])
            self.assertEqual("copied", statuses["good.md"])
            self.assertEqual("unsupported", statuses["photo.png"])

    def test_dry_run_plans_without_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "note.txt").write_text("invoice", encoding="utf-8")
            rules_path = root / "rules.json"
            rules_path.write_text(
                json.dumps(
                    {
                        "fallback": "other",
                        "categories": [{"name": "finance", "keywords": ["invoice"]}],
                    }
                ),
                encoding="utf-8",
            )
            output = root / "output"

            summary = process_documents(
                incoming, output, load_rules(rules_path), dry_run=True
            )

            self.assertFalse(output.exists())
            self.assertEqual("planned", summary.records[0].status)
            self.assertEqual("finance/note.txt", summary.records[0].destination)

    def test_rejects_symlink_sources_without_copying_external_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incoming = root / "incoming"
            incoming.mkdir()
            external = root / "external.txt"
            external.write_text("invoice secret", encoding="utf-8")
            (incoming / "linked.txt").symlink_to(external)
            rules_path = root / "rules.json"
            rules_path.write_text(
                json.dumps(
                    {
                        "fallback": "other",
                        "categories": [{"name": "finance", "keywords": ["invoice"]}],
                    }
                ),
                encoding="utf-8",
            )
            output = root / "output"

            summary = process_documents(incoming, output, load_rules(rules_path))

            self.assertEqual(1, summary.errors)
            self.assertEqual("error", summary.records[0].status)
            self.assertFalse((output / "finance" / "linked.txt").exists())


if __name__ == "__main__":
    unittest.main()
