# Roadmap

Backtest Integrity Guard is intentionally small. The roadmap focuses on integrity checks that can be audited independently of any trading strategy.

## v0.2 — Data integrity
- Configurable column aliases and schema mapping
- Missing-bar and session-gap detection
- Deterministic JSON report metadata
- Optional SHA256 binding of audit reports to input files

## v0.3 — Execution integrity
- Duplicate-row diagnostics beyond timestamps
- Explicit bar-completion policies
- Configurable next-bar execution contracts
- Intrabar ambiguity policies with machine-readable evidence
- Cross-ledger consistency checks

## v0.4 — Integration
- CI usage examples
- Optional adapters for common research dataframes
- Reusable report schemas for downstream tooling

## Non-goals
- Trading signals or alpha logic
- Performance optimization
- Brokerage execution
- Bundling proprietary or licensed market data

Roadmap items may change based on reproducible bug reports and real user needs.
