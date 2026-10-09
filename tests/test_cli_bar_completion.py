import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BarCompletionCLITests(unittest.TestCase):
    def run_ohlcv(self, marker, policy=None):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "bars.csv"
            csv_path.write_text(
                "timestamp,open,high,low,close,complete\n"
                "2026-01-01T00:00:00Z,10,12,9,11," + marker + "\n",
                encoding="utf-8",
            )
            args = [
                sys.executable, "-m", "backtest_integrity_guard.cli",
                "ohlcv", str(csv_path),
            ]
            if policy is not None:
                args.extend(["--bar-completion", policy])
            return subprocess.run(
                args, capture_output=True, text=True, timeout=10,
                env=dict(os.environ, PYTHONPATH=str(ROOT / "src")),
            )

    def test_default_keeps_incomplete_warning_only(self):
        result = self.run_ohlcv("false")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "PASS")
        self.assertEqual(output["findings"][0]["code"], "INCOMPLETE_BAR")
        self.assertEqual(output["findings"][0]["severity"], "WARNING")

    def test_strict_incomplete_is_an_error_with_row(self):
        result = self.run_ohlcv("false", "require-complete")
        self.assertEqual(result.returncode, 1)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "FAIL")
        self.assertEqual(output["findings"][0]["row"], 2)
        self.assertEqual(output["findings"][0]["severity"], "ERROR")

    def test_strict_missing_marker_fails_closed(self):
        result = self.run_ohlcv("", "require-complete")
        self.assertEqual(result.returncode, 1)
        output = json.loads(result.stdout)
        self.assertEqual(output["findings"][0]["code"], "BAR_COMPLETION_UNVERIFIED")
        self.assertEqual(output["status"], "FAIL")

    def test_strict_complete_and_invalid_policy(self):
        ok = self.run_ohlcv("yes", "require-complete")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        bad = self.run_ohlcv("true", "not-a-policy")
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("invalid choice", bad.stderr)
        self.assertEqual(bad.stdout, "")


if __name__ == "__main__":
    unittest.main()
