# Backtest Integrity Guard

[![tests](https://github.com/suguobin2021/backtest-integrity-guard/actions/workflows/test.yml/badge.svg)](https://github.com/suguobin2021/backtest-integrity-guard/actions/workflows/test.yml)

A small, dependency-free Python CLI for detecting common integrity failures in quantitative backtests before performance metrics are trusted.

## What it checks

- OHLC geometry and negative/invalid volume
- duplicate or non-monotonic timestamps
- timezone-aware timestamps
- incomplete-bar markers
- signal-close -> execution ordering
- next-bar execution constraints
- same-bar stop/target ambiguity
- SHA256 manifests for frozen research inputs

It does **not** implement a trading strategy and does not contain market data.

## Install

```bash
python -m pip install -e .
```

## Examples

```bash
btguard ohlcv examples/ohlcv.csv
btguard ohlcv vendor.csv --map schema.json
btguard ohlcv bars.csv --interval-seconds 300 --allow-gaps allowed_gaps.json
btguard ohlcv bars.csv --hash-input
btguard ledger examples/trades.csv
btguard freeze examples/ohlcv.csv examples/trades.csv -o manifest.json --root .
btguard verify manifest.json --root .
```

The command exits non-zero when an integrity error is found, so it can be used in CI.

For vendor-specific schemas, pass a JSON mapping from canonical field names to input columns:

~~~json
{
  "timestamp": "ts",
  "open": "o",
  "high": "h",
  "low": "l",
  "close": "c",
  "volume": "qty"
}
~~~




For cadence checks, declare the expected bar interval. Missing bars and irregular intervals fail the audit. Known session breaks can be allowlisted explicitly without bundling an exchange calendar:

~~~json
[
  ["2026-01-02T16:00:00Z", "2026-01-05T09:30:00Z"]
]
~~~

An allowlisted break is reported as ALLOWED_SESSION_GAP with warning severity while the audit remains PASS.

Audit JSON uses a stable schema identifier, includes the tool version, and is serialized deterministically for byte-for-byte comparison. Use --hash-input when the report should also bind itself to the exact audited file via SHA256.

## Why

Backtests can look profitable while silently consuming incomplete bars, executing on the signal bar, changing frozen inputs, or resolving an intrabar stop/target collision without an explicit policy. This project makes those assumptions machine-checkable.

## Scope

Version 0.2 focuses on auditable data integrity: schema mapping, cadence/session checks, deterministic report output, and optional SHA256 input binding. Future versions will extend execution-integrity checks and adapters.

## License

MIT.
