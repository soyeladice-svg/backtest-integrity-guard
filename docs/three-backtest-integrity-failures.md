# Three backtest integrity failures worth catching before you trust performance

A profitable backtest can be invalid even when the performance code is correct. Some failures happen earlier: in the data, in signal/execution timing, or in assumptions about what happened inside a bar.

Backtest Integrity Guard is designed to make a few of those assumptions machine-checkable before metrics such as Sharpe ratio, CAGR, or profit factor are interpreted.

All examples below use synthetic data and the public PyPI package.

## Install

~~~bash
python -m pip install backtest-integrity-guard
~~~

## 1. Same-bar entry after using the bar close

Suppose a strategy uses a completed 5-minute bar to decide whether to trade. If the signal depends on that bar's close, an execution timestamp at the same close is not a causal next-bar execution.

Run:

~~~bash
btguard ledger examples/lookahead_entry.csv
~~~

The audit fails with:

~~~text
LOOKAHEAD_OR_SAME_BAR_ENTRY
~~~

Why it matters: the execution price is being taken from the same information boundary that created the signal. A backtest can therefore consume information that was not available early enough to execute as modeled.

A causal alternative is to declare the signal bar complete first and execute no earlier than the next permitted bar.

## 2. Missing bars hidden inside an apparently valid OHLCV file

A CSV can have valid OHLC geometry and still be incomplete. In this example, a five-minute series jumps from 00:00 to 00:15, so two expected bars are missing.

Run:

~~~bash
btguard ohlcv examples/missing_bars.csv --interval-seconds 300
~~~

The audit fails with:

~~~text
MISSING_BARS
~~~

and reports the number of missing intervals.

Why it matters: missing bars can change indicator state, stop/target paths, holding periods, and the apparent timing of signals.

Not every gap is an error. Known exchange or session breaks can be declared explicitly with `--allow-gaps`; undeclared gaps fail closed.

## 3. Stop and target both touched inside the same bar

OHLC data does not reveal the intrabar path. If a bar's high and low imply that both a stop and a target were touched, the order of those events is unknown unless higher-resolution path information exists or an explicit policy is declared.

Run:

~~~bash
btguard ledger examples/ambiguous_exit.csv
~~~

The audit fails with:

~~~text
AMBIGUOUS_SAME_BAR_EXIT
~~~

Why it matters: silently choosing the favorable outcome can create optimistic backtests. Silently choosing the unfavorable outcome can also distort results. The important requirement is that the ambiguity policy be explicit and reproducible.

Supported explicit policies include:

- `stop_first`
- `target_first`
- `path_known`

## Reproducibility: bind the audit to the exact input

For an auditable research trail, add `--hash-input`:

~~~bash
btguard ohlcv examples/ohlcv.csv --hash-input
~~~

The JSON report includes a SHA256 hash of the exact input file plus a stable report schema and tool version.

## What this does not solve

Backtest Integrity Guard is not a backtesting engine. It does not model commissions, slippage, market impact, exchange calendars, order-book fills, survivorship bias, or strategy overfitting.

Its narrower goal is to make several common integrity assumptions explicit, testable, and reproducible before performance results are trusted.

## Try it without local setup

Use the repository's **Open in Colab** badge to run a passing and failing example in a browser.
