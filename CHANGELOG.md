# Changelog

All notable changes to Backtest Integrity Guard are documented here.

## [0.2.2] - 2026-10-03

### Added
- Distinguish exact duplicate bar rows from same-timestamp OHLC(V) conflicts.
- New finding codes: `DUPLICATE_BAR_ROW` and `TIMESTAMP_CONFLICT`.
- Zero-setup Google Colab quickstart.

### Changed
- Duplicate diagnostics preserve the existing `DUPLICATE_TIMESTAMP` finding for compatibility.
- Duplicate comparisons respect configured OHLCV field mappings.
- Test suite expanded from 12 to 16 tests.

### Contributors
- Thanks to [@vansh-nagar](https://github.com/vansh-nagar) for implementing the duplicate/conflict diagnostics in PR #16.

## [0.2.1] - 2026-10-03

### Added
- Installable wheel and source archive release assets with SHA256SUMS.
- Public quick-start examples for schema mapping and session gaps.
- Bug-report and feature-request issue templates.
- Repository, issues, releases, and changelog links in package metadata.

### Changed
- Contributor workflow documentation expanded.
- README reorganized for first-time users.

## [0.2.0] - 2026-10-03

### Added
- Configurable OHLCV schema aliases.
- Fail-closed validation for missing mapped fields.
- Expected-cadence checks for missing and irregular bars.
- Explicit allowlisting of known session gaps.
- Stable report schema version 1.0.
- Deterministic JSON serialization.
- Optional SHA256 binding to the audited input file.

### Changed
- Package version advanced to 0.2.0.
- Test suite expanded to 12 tests across Python 3.10, 3.11, and 3.12.

## [0.1.0] - 2026-10-03

### Added
- OHLC geometry and volume validation.
- Duplicate and non-monotonic timestamp detection.
- Timezone-aware timestamp validation.
- Incomplete-bar warnings.
- Signal-close to execution ordering checks.
- Next-bar execution checks.
- Same-bar stop/target ambiguity detection.
- SHA256 frozen-input manifests.
- Dependency-free CLI and synthetic examples.
