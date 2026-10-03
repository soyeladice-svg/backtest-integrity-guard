# Backtest Integrity Guard

[![tests](https://github.com/suguobin2021/backtest-integrity-guard/actions/workflows/test.yml/badge.svg)](https://github.com/suguobin2021/backtest-integrity-guard/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/backtest-integrity-guard.svg)](https://pypi.org/project/backtest-integrity-guard/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/suguobin2021/backtest-integrity-guard/blob/main/examples/quickstart.ipynb)

**Project site:** https://suguobin2021.github.io/backtest-integrity-guard/

A small, dependency-free Python CLI for catching common integrity failures in quantitative backtests before performance metrics are trusted.

It focuses on **causality, data integrity, explicit ambiguity handling, and reproducibility**. It does not implement trading signals or ship market data.

## Install

### From PyPI

~~~bash
python -m pip install backtest-integrity-guard
btguard --help
~~~

### From a GitHub release

The GitHub release includes a wheel, source archive, and SHA256SUMS for users who want to verify exact artifacts.

### From source

~~~bash
git clone https://github.com/suguobin2021/backtest-integrity-guard.git
cd backtest-integrity-guard
python -m pip install -e .
~~~

## Quick start

Audit ordinary OHLCV data:

~~~bash
btguard ohlcv examples/ohlcv.csv --hash-input
~~~

Audit vendor-specific column names:

~~~bash
btguard ohlcv examples/vendor.csv --map examples/schema.json
~~~

Check a 5-minute cadence while explicitly allowing a known session break:

~~~bash
btguard ohlcv examples/session_gap.csv \
  --interval-seconds 300 \
  --allow-gaps examples/allowed_gaps.json
~~~

Audit signal-to-execution timing:

~~~bash
btguard ledger examples/trades.csv --hash-input
~~~

Freeze and verify research inputs:

~~~bash
btguard freeze examples/ohlcv.csv examples/trades.csv -o manifest.json --root .
btguard verify manifest.json --root .
~~~

Commands exit non-zero when an integrity error is found, so they can be used in CI.

## Output contract

Audit output is deterministic JSON with a stable report schema:

~~~json
{
  "errors": 0,
  "findings": [],
  "input_sha256": "<64 hex chars>",
  "report_schema_version": "1.0",
  "status": "PASS",
  "tool_version": "0.2.2",
  "warnings": 0
}
~~~

Use --hash-input when a report should be bound to the exact audited file.

## What it checks

- OHLC geometry and negative or invalid volume
- duplicate/conflicting and non-monotonic timestamps
- timezone-aware timestamps
- incomplete-bar markers
- configurable OHLCV schema aliases
- missing bars and irregular cadence
- explicitly allowlisted session gaps
- signal-close to execution ordering
- next-bar execution constraints
- same-bar stop/target ambiguity
- SHA256 frozen-input manifests
- deterministic machine-readable reports

## Scope

Backtest Integrity Guard intentionally does **not** contain:
- trading signals or alpha logic
- brokerage execution code
- proprietary or licensed market data
- account credentials or API keys

The goal is to make research assumptions machine-checkable without depending on any particular strategy.

## Guides

- [Three backtest integrity failures worth catching before you trust performance](docs/three-backtest-integrity-failures.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports should include the smallest synthetic example that reproduces the problem.

Useful project links:
- [Discussions](https://github.com/suguobin2021/backtest-integrity-guard/discussions)
- [Issues](https://github.com/suguobin2021/backtest-integrity-guard/issues)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Releases](https://github.com/suguobin2021/backtest-integrity-guard/releases)

## License

MIT.
