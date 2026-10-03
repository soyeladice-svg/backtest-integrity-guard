from pathlib import Path
import json
import tempfile
import unittest

from backtest_integrity_guard.core import (
    audit_ohlcv_rows, audit_trade_rows, build_manifest, verify_manifest,
)


class IntegrityTests(unittest.TestCase):
    def test_clean_ohlcv_passes(self):
        rows = [
            {"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"12","low":"9","close":"11","volume":"100"},
            {"timestamp":"2026-01-01T00:05:00Z","open":"11","high":"13","low":"10","close":"12","volume":"110"},
        ]
        self.assertEqual(audit_ohlcv_rows(rows).status, "PASS")

    def test_bad_ohlcv_fails(self):
        rows = [{"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"9","low":"11","close":"10","volume":"-1"}]
        report = audit_ohlcv_rows(rows)
        self.assertEqual(report.status, "FAIL")
        self.assertGreaterEqual(report.errors, 3)

    def test_same_bar_entry_fails(self):
        rows = [{
            "signal_bar_close":"2026-01-01T00:05:00Z",
            "entry_time":"2026-01-01T00:05:00Z",
            "next_bar_open":"2026-01-01T00:05:00Z",
        }]
        codes = {x.code for x in audit_trade_rows(rows).findings}
        self.assertIn("LOOKAHEAD_OR_SAME_BAR_ENTRY", codes)

    def test_ambiguous_exit_fails(self):
        rows = [{
            "signal_bar_close":"2026-01-01T00:05:00Z",
            "entry_time":"2026-01-01T00:10:00Z",
            "next_bar_open":"2026-01-01T00:10:00Z",
            "stop_hit":"true", "target_hit":"true",
        }]
        codes = {x.code for x in audit_trade_rows(rows).findings}
        self.assertIn("AMBIGUOUS_SAME_BAR_EXIT", codes)

    def test_manifest_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            f = root / "input.txt"
            f.write_text("frozen\n")
            m = root / "manifest.json"
            m.write_text(json.dumps(build_manifest([f], root)))
            self.assertEqual(verify_manifest(m, root).status, "PASS")
            f.write_text("changed\n")
            self.assertEqual(verify_manifest(m, root).status, "FAIL")


if __name__ == "__main__":
    unittest.main()
