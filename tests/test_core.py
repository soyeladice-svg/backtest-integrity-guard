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

    def test_alternate_schema_mapping_passes(self):
        rows = [
            {"ts":"2026-01-01T00:00:00Z","o":"10","h":"12","l":"9","c":"11","qty":"100"},
        ]
        report = audit_ohlcv_rows(rows, field_map={
            "timestamp":"ts", "open":"o", "high":"h", "low":"l", "close":"c", "volume":"qty"
        })
        self.assertEqual(report.status, "PASS")

    def test_missing_mapped_required_field_fails_closed(self):
        rows = [
            {"ts":"2026-01-01T00:00:00Z","o":"10","h":"12","c":"11"},
        ]
        report = audit_ohlcv_rows(rows, field_map={
            "timestamp":"ts", "open":"o", "high":"h", "low":"l", "close":"c"
        })
        codes = {x.code for x in report.findings}
        self.assertIn("MISSING_REQUIRED_FIELD", codes)

    def test_missing_bars_are_counted(self):
        rows = [
            {"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"12","low":"9","close":"11"},
            {"timestamp":"2026-01-01T00:15:00Z","open":"11","high":"13","low":"10","close":"12"},
        ]
        report = audit_ohlcv_rows(rows, expected_interval_seconds=300)
        hits = [x for x in report.findings if x.code == "MISSING_BARS"]
        self.assertEqual(len(hits), 1)
        self.assertIn("missing=2", hits[0].message)
        self.assertEqual(report.status, "FAIL")

    def test_explicit_session_gap_is_allowed(self):
        from backtest_integrity_guard.core import parse_iso8601
        start = parse_iso8601("2026-01-02T16:00:00Z")
        end = parse_iso8601("2026-01-05T09:30:00Z")
        rows = [
            {"timestamp":"2026-01-02T16:00:00Z","open":"10","high":"12","low":"9","close":"11"},
            {"timestamp":"2026-01-05T09:30:00Z","open":"11","high":"13","low":"10","close":"12"},
        ]
        report = audit_ohlcv_rows(
            rows,
            expected_interval_seconds=300,
            allowed_gaps={(start, end)},
        )
        self.assertEqual(report.status, "PASS")
        self.assertEqual([x.code for x in report.findings], ["ALLOWED_SESSION_GAP"])

    def test_irregular_interval_is_distinct(self):
        rows = [
            {"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"12","low":"9","close":"11"},
            {"timestamp":"2026-01-01T00:07:00Z","open":"11","high":"13","low":"10","close":"12"},
        ]
        codes = {
            x.code for x in audit_ohlcv_rows(
                rows, expected_interval_seconds=300
            ).findings
        }
        self.assertIn("IRREGULAR_BAR_INTERVAL", codes)

    def test_bad_ohlcv_fails(self):
        rows = [{"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"9","low":"11","close":"10","volume":"-1"}]
        report = audit_ohlcv_rows(rows)
        self.assertEqual(report.status, "FAIL")
        self.assertGreaterEqual(report.errors, 3)

    def test_exact_duplicate_bar_is_distinguished(self):
        row = {"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"12","low":"9","close":"11","volume":"100"}
        codes = {x.code for x in audit_ohlcv_rows([row, dict(row)]).findings}
        self.assertIn("DUPLICATE_TIMESTAMP", codes)
        self.assertIn("DUPLICATE_BAR_ROW", codes)
        self.assertNotIn("TIMESTAMP_CONFLICT", codes)

    def test_same_timestamp_with_different_values_is_a_conflict(self):
        rows = [
            {"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"12","low":"9","close":"11","volume":"100"},
            {"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"12","low":"9","close":"11.5","volume":"100"},
        ]
        codes = {x.code for x in audit_ohlcv_rows(rows).findings}
        self.assertIn("DUPLICATE_TIMESTAMP", codes)
        self.assertIn("TIMESTAMP_CONFLICT", codes)
        self.assertNotIn("DUPLICATE_BAR_ROW", codes)

    def test_duplicate_bar_comparison_respects_field_mapping(self):
        row = {"ts":"2026-01-01T00:00:00Z","o":"10","h":"12","l":"9","c":"11","qty":"100"}
        report = audit_ohlcv_rows([row, dict(row)], field_map={
            "timestamp":"ts", "open":"o", "high":"h", "low":"l", "close":"c", "volume":"qty"
        })
        self.assertIn("DUPLICATE_BAR_ROW", {x.code for x in report.findings})

    def test_equal_prices_at_different_timestamps_are_not_duplicates(self):
        rows = [
            {"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"12","low":"9","close":"11"},
            {"timestamp":"2026-01-01T00:05:00Z","open":"10","high":"12","low":"9","close":"11"},
        ]
        codes = {x.code for x in audit_ohlcv_rows(rows).findings}
        self.assertNotIn("DUPLICATE_BAR_ROW", codes)
        self.assertNotIn("TIMESTAMP_CONFLICT", codes)

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

    def test_report_json_is_byte_stable(self):
        rows = [
            {"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"12","low":"9","close":"11"},
        ]
        a = audit_ohlcv_rows(rows)
        b = audit_ohlcv_rows(rows)
        self.assertEqual(a.to_json(), b.to_json())
        self.assertIn('"report_schema_version":"1.0"', a.to_json())
        self.assertIn('"tool_version":"0.2.2"', a.to_json())

    def test_optional_input_sha256_is_emitted(self):
        report = audit_ohlcv_rows([
            {"timestamp":"2026-01-01T00:00:00Z","open":"10","high":"12","low":"9","close":"11"},
        ])
        report.input_sha256 = "a" * 64
        rendered = report.to_json()
        self.assertIn('"input_sha256":"' + ("a" * 64) + '"', rendered)

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
