import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "document_workflow.cli", *arguments],
            cwd=PROJECT_ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_dry_run_prints_json_plan_and_returns_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "note.txt").write_text("invoice", encoding="utf-8")
            rules = root / "rules.json"
            rules.write_text(
                json.dumps(
                    {
                        "fallback": "other",
                        "categories": [{"name": "finance", "keywords": ["invoice"]}],
                    }
                ),
                encoding="utf-8",
            )
            output = root / "output"

            result = self.run_cli(
                str(incoming), "--output", str(output), "--rules", str(rules), "--dry-run"
            )

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual("planned", payload["records"][0]["status"])
            self.assertFalse(output.exists())

    def test_returns_one_when_a_document_cannot_be_processed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "broken.json").write_text("{broken", encoding="utf-8")
            rules = root / "rules.json"
            rules.write_text(
                json.dumps({"fallback": "other", "categories": []}), encoding="utf-8"
            )

            result = self.run_cli(
                str(incoming), "--output", str(root / "output"), "--rules", str(rules)
            )

            self.assertEqual(1, result.returncode, result.stderr)
            self.assertEqual(1, json.loads(result.stdout)["summary"]["errors"])


if __name__ == "__main__":
    unittest.main()
