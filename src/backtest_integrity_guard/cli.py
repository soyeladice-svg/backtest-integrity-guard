from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .core import audit_ohlcv_rows, audit_trade_rows, build_manifest, verify_manifest


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def emit(report) -> int:
    print(json.dumps(report.to_dict(), indent=2))
    return 1 if report.errors else 0


def main() -> int:
    p = argparse.ArgumentParser(prog="btguard")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("ohlcv", help="audit OHLCV geometry and timestamps")
    a.add_argument("file", type=Path)
    a.add_argument("--timestamp", default="timestamp")
    a.add_argument("--map", type=Path, help="JSON mapping of canonical fields to input column names")

    b = sub.add_parser("ledger", help="audit signal-to-execution causality")
    b.add_argument("file", type=Path)
    b.add_argument("--signal-close", default="signal_bar_close")
    b.add_argument("--entry", default="entry_time")
    b.add_argument("--next-open", default="next_bar_open")

    c = sub.add_parser("freeze", help="create a SHA256 input manifest")
    c.add_argument("files", nargs="+", type=Path)
    c.add_argument("-o", "--output", required=True, type=Path)
    c.add_argument("--root", type=Path)

    d = sub.add_parser("verify", help="verify a frozen SHA256 manifest")
    d.add_argument("manifest", type=Path)
    d.add_argument("--root", type=Path)

    args = p.parse_args()
    if args.command == "ohlcv":
        mapping = None
        if args.map:
            mapping = json.loads(args.map.read_text(encoding="utf-8"))
            if not isinstance(mapping, dict):
                raise SystemExit("--map must contain a JSON object")
        return emit(audit_ohlcv_rows(read_csv(args.file), args.timestamp, mapping))
    if args.command == "ledger":
        return emit(audit_trade_rows(read_csv(args.file), args.signal_close, args.entry, args.next_open))
    if args.command == "freeze":
        data = build_manifest(args.files, args.root)
        args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(args.output)
        return 0
    return emit(verify_manifest(args.manifest, args.root))


if __name__ == "__main__":
    raise SystemExit(main())
