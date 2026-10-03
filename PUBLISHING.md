# Publishing to PyPI

This repository is prepared for PyPI Trusted Publishing through GitHub Actions OIDC. No long-lived PyPI API token is required.

## One-time PyPI setup

Create or sign in to a PyPI account, then add a **pending GitHub publisher** with these exact values:

- PyPI project name: backtest-integrity-guard
- GitHub owner: suguobin2021
- Repository: backtest-integrity-guard
- Workflow filename: release.yml
- Environment: pypi

The GitHub environment named pypi already exists in this repository.

Important: a pending publisher does not reserve the project name until the first successful publish.

## First publication

After the pending publisher is configured on PyPI:

1. Open GitHub Actions.
2. Select the **publish** workflow.
3. Run it manually on main.
4. Confirm that PyPI created the project and uploaded the current version.

## Future releases

Publishing a GitHub Release triggers the same workflow automatically. The workflow:

- checks out the release revision
- builds wheel and source distributions
- installs the wheel for a CLI smoke test
- requests a short-lived OIDC credential
- uploads through PyPA's official publish action

Do not add PYPI_TOKEN or another long-lived publishing secret unless the Trusted Publishing design is intentionally retired.
