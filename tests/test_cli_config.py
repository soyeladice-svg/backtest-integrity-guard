import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def run_config(self, option, text):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_text(text, encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
            return subprocess.run(
                [sys.executable, "-m", "backtest_integrity_guard.cli", "ohlcv",
                 str(ROOT / "examples" / "ohlcv.csv"), option, str(config)],
                capture_output=True, text=True, env=env, timeout=10,
            )

    def test_malformed_json_is_a_concise_error(self):
        for option in ("--map", "--allow-gaps"):
            with self.subTest(option=option):
                result = self.run_config(option, "{\n")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(f"invalid {option} JSON:", result.stderr)
                self.assertIn("line 2 column 1", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(len(result.stderr.splitlines()), 1)

    def test_valid_json_still_emits_a_report(self):
        for option, text in (("--map", "{}"), ("--allow-gaps", "[]")):
            with self.subTest(option=option):
                result = self.run_config(option, text)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIsInstance(json.loads(result.stdout), dict)
                self.assertEqual(result.stderr, "")

    def test_semantic_validation_is_preserved(self):
        cases = (
            ("--map", "[]", "--map must contain a JSON object"),
            ("--allow-gaps", "{}", "--allow-gaps must contain a JSON list"),
            ("--allow-gaps", "[[]]", "each --allow-gaps entry must be"),
            ("--allow-gaps", '[["bad", "bad"]]', "invalid --allow-gaps entry:"),
        )
        for option, text, message in cases:
            with self.subTest(option=option, text=text):
                result = self.run_config(option, text)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
