# Contributing

Contributions that improve research integrity are welcome. Strategy logic, alpha ideas, brokerage credentials, and proprietary datasets are intentionally out of scope.

## Development setup

~~~bash
git clone https://github.com/suguobin2021/backtest-integrity-guard.git
cd backtest-integrity-guard
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
~~~

Supported Python versions: 3.10, 3.11, and 3.12.

## Pull requests
- Start with an issue for behavioral changes.
- Keep each pull request focused on one integrity problem.
- Add a failing test that demonstrates the problem, then a passing test for the fix.
- Preserve fail-closed behavior for ambiguous or missing inputs.
- Run the full unittest suite locally before opening a pull request.
- CI must pass on Python 3.10, 3.11, and 3.12 before merge.

## Reporting bugs

Use the bug-report template and include the smallest synthetic input that reproduces the problem. Do not upload private market data, API keys, account identifiers, or proprietary strategy code.

## Design principle

A check should be understandable and auditable without knowing a specific trading strategy.
