import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MissingInputTests(unittest.TestCase):
    def run_cli(self, *args):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        return subprocess.run(
            [sys.executable, "-m", "backtest_integrity_guard.cli", *args],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )

    def test_missing_ohlcv_and_ledger_are_concise_errors(self):
        missing = ROOT / "examples" / "does-not-exist.csv"
        for command in ("ohlcv", "ledger"):
            with self.subTest(command=command):
                result = self.run_cli(command, str(missing))
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(f"input file not found: {missing}", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(len(result.stderr.splitlines()), 1)

    def test_existing_ohlcv_and_ledger_still_emit_reports(self):
        cases = (
            ("ohlcv", ROOT / "examples" / "ohlcv.csv"),
            ("ledger", ROOT / "examples" / "trades.csv"),
        )
        for command, path in cases:
            with self.subTest(command=command):
                result = self.run_cli(command, str(path))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIsInstance(json.loads(result.stdout), dict)
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
