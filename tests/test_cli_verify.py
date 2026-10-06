import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VerifyManifestTests(unittest.TestCase):
    def run_verify(self, tmp, manifest_text):
        manifest = Path(tmp) / "manifest.json"
        manifest.write_text(manifest_text, encoding="utf-8")
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        return subprocess.run(
            [sys.executable, "-m", "backtest_integrity_guard.cli", "verify", str(manifest)],
            capture_output=True, text=True, env=env, timeout=10,
        )

    def test_malformed_manifest_is_a_concise_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_verify(tmp, "{\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("invalid manifest JSON:", result.stderr)
        self.assertIn("line 2 column 1", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(len(result.stderr.splitlines()), 1)

    def test_valid_manifest_still_reports_missing_and_mismatched_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            changed = Path(tmp) / "changed.csv"
            changed.write_text("a\n", encoding="utf-8")
            manifest = {
                "algorithm": "sha256",
                "files": [
                    {"path": "missing.csv", "sha256": "0" * 64, "bytes": 0},
                    {"path": "changed.csv", "sha256": "0" * 64, "bytes": 2},
                ],
            }
            result = self.run_verify(tmp, json.dumps(manifest))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stderr, "")
        codes = {f["code"] for f in json.loads(result.stdout)["findings"]}
        self.assertEqual(codes, {"MISSING_FROZEN_INPUT", "FROZEN_INPUT_HASH_MISMATCH"})


if __name__ == "__main__":
    unittest.main()
