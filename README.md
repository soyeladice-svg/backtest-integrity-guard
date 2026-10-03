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


## Why

Backtests can look profitable while silently consuming incomplete bars, executing on the signal bar, changing frozen inputs, or resolving an intrabar stop/target collision without an explicit policy. This project makes those assumptions machine-checkable.

## Scope

Version 0.1 intentionally stays small and auditable. Planned additions include schema mapping, gap/session checks, deterministic report output, and adapters for common backtest ledgers.

## License

MIT.
