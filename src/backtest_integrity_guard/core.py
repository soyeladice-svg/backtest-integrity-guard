from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import json
from typing import Iterable, Mapping, Any


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    row: int | None
    message: str


@dataclass
class AuditReport:
    findings: list[Finding]

    @property
    def errors(self) -> int:
        return sum(x.severity == "ERROR" for x in self.findings)

    @property
    def warnings(self) -> int:
        return sum(x.severity == "WARNING" for x in self.findings)

    @property
    def status(self) -> str:
        return "FAIL" if self.errors else "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "findings": [asdict(x) for x in self.findings],
        }


def parse_iso8601(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        raise ValueError("timestamp must include UTC offset or Z")
    return dt


def _float(row: Mapping[str, str], key: str) -> float:
    return float(row[key])


def audit_ohlcv_rows(
    rows: Iterable[Mapping[str, str]],
    timestamp_field: str = "timestamp",
    field_map: Mapping[str, str] | None = None,
    expected_interval_seconds: int | None = None,
    allowed_gaps: Iterable[tuple[datetime, datetime]] | None = None,
) -> AuditReport:
    findings: list[Finding] = []
    seen: set[datetime] = set()
    previous: datetime | None = None
    if expected_interval_seconds is not None and expected_interval_seconds <= 0:
        raise ValueError("expected_interval_seconds must be positive")
    expected = (
        timedelta(seconds=expected_interval_seconds)
        if expected_interval_seconds is not None else None
    )
    allowed = set(allowed_gaps or ())
    names = {
        "timestamp": timestamp_field,
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        **(dict(field_map) if field_map else {}),
    }

    for n, row in enumerate(rows, start=2):
        missing = [k for k in ("timestamp", "open", "high", "low", "close") if names[k] not in row]
        if missing:
            findings.append(Finding(
                "ERROR", "MISSING_REQUIRED_FIELD", n,
                ",".join(f"{k}->{names[k]}" for k in missing),
            ))
            continue
        try:
            ts = parse_iso8601(row[names["timestamp"]])
        except Exception as exc:
            findings.append(Finding("ERROR", "INVALID_TIMESTAMP", n, str(exc)))
            continue

        if ts in seen:
            findings.append(Finding("ERROR", "DUPLICATE_TIMESTAMP", n, str(ts)))
        if previous is not None and ts <= previous:
            findings.append(Finding("ERROR", "NON_MONOTONIC_TIME", n, str(ts)))
        elif previous is not None and expected is not None:
            delta = ts - previous
            if delta != expected:
                if (previous, ts) in allowed:
                    findings.append(Finding(
                        "WARNING", "ALLOWED_SESSION_GAP", n,
                        f"from={previous.isoformat()} to={ts.isoformat()} seconds={int(delta.total_seconds())}",
                    ))
                elif delta > expected and delta.total_seconds() % expected.total_seconds() == 0:
                    missing = int(delta / expected) - 1
                    findings.append(Finding(
                        "ERROR", "MISSING_BARS", n,
                        f"missing={missing} expected_interval_seconds={expected_interval_seconds} "
                        f"from={previous.isoformat()} to={ts.isoformat()}",
                    ))
                else:
                    findings.append(Finding(
                        "ERROR", "IRREGULAR_BAR_INTERVAL", n,
                        f"expected_seconds={expected_interval_seconds} "
                        f"actual_seconds={delta.total_seconds():g} "
                        f"from={previous.isoformat()} to={ts.isoformat()}",
                    ))
        seen.add(ts)
        previous = ts

        try:
            o, h, l, c = (_float(row, names[k]) for k in ("open", "high", "low", "close"))
        except Exception as exc:
            findings.append(Finding("ERROR", "INVALID_OHLC", n, str(exc)))
            continue

        if l > h:
            findings.append(Finding("ERROR", "LOW_ABOVE_HIGH", n, f"{l}>{h}"))
        if h < max(o, c):
            findings.append(Finding("ERROR", "HIGH_BELOW_BODY", n, f"h={h} o={o} c={c}"))
        if l > min(o, c):
            findings.append(Finding("ERROR", "LOW_ABOVE_BODY", n, f"l={l} o={o} c={c}"))

        volume_field = names["volume"]
        if volume_field in row and row[volume_field] not in ("", None):
            try:
                if float(row[volume_field]) < 0:
                    findings.append(Finding("ERROR", "NEGATIVE_VOLUME", n, row[volume_field]))
            except Exception as exc:
                findings.append(Finding("ERROR", "INVALID_VOLUME", n, str(exc)))

        if "complete" in row and str(row["complete"]).strip().lower() in {"false", "0", "no"}:
            findings.append(Finding("WARNING", "INCOMPLETE_BAR", n, "bar is marked incomplete"))

    return AuditReport(findings)


def audit_trade_rows(
    rows: Iterable[Mapping[str, str]],
    signal_close_field: str = "signal_bar_close",
    entry_field: str = "entry_time",
    next_open_field: str | None = "next_bar_open",
) -> AuditReport:
    findings: list[Finding] = []

    for n, row in enumerate(rows, start=2):
        try:
            signal_close = parse_iso8601(row[signal_close_field])
            entry = parse_iso8601(row[entry_field])
        except Exception as exc:
            findings.append(Finding("ERROR", "INVALID_EXECUTION_TIME", n, str(exc)))
            continue

        if entry <= signal_close:
            findings.append(Finding(
                "ERROR", "LOOKAHEAD_OR_SAME_BAR_ENTRY", n,
                f"entry={entry.isoformat()} signal_close={signal_close.isoformat()}",
            ))

        if next_open_field and row.get(next_open_field):
            try:
                next_open = parse_iso8601(row[next_open_field])
                if entry < next_open:
                    findings.append(Finding(
                        "ERROR", "ENTRY_BEFORE_NEXT_BAR", n,
                        f"entry={entry.isoformat()} next_open={next_open.isoformat()}",
                    ))
            except Exception as exc:
                findings.append(Finding("ERROR", "INVALID_NEXT_BAR_OPEN", n, str(exc)))

        stop_hit = str(row.get("stop_hit", "")).strip().lower() in {"1", "true", "yes"}
        target_hit = str(row.get("target_hit", "")).strip().lower() in {"1", "true", "yes"}
        policy = str(row.get("same_bar_policy", "")).strip().lower()
        if stop_hit and target_hit and policy not in {"stop_first", "target_first", "path_known"}:
            findings.append(Finding(
                "ERROR", "AMBIGUOUS_SAME_BAR_EXIT", n,
                "stop and target both hit but no explicit same_bar_policy is declared",
            ))

    return AuditReport(findings)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def build_manifest(paths: Iterable[Path], root: Path | None = None) -> dict[str, Any]:
    root = root.resolve() if root else None
    files = []
    for path in sorted(Path(p).resolve() for p in paths):
        name = str(path.relative_to(root)) if root and path.is_relative_to(root) else str(path)
        files.append({"path": name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    return {"algorithm": "sha256", "files": files}


def verify_manifest(manifest_path: Path, root: Path | None = None) -> AuditReport:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = root.resolve() if root else manifest_path.parent.resolve()
    findings: list[Finding] = []
    for item in data.get("files", []):
        path = Path(item["path"])
        if not path.is_absolute():
            path = base / path
        if not path.exists():
            findings.append(Finding("ERROR", "MISSING_FROZEN_INPUT", None, str(path)))
            continue
        actual = sha256_file(path)
        if actual != item["sha256"]:
            findings.append(Finding("ERROR", "FROZEN_INPUT_HASH_MISMATCH", None, str(path)))
    return AuditReport(findings)
