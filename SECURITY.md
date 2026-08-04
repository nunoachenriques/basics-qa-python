# Security Policy

## Supported versions

The latest release on `main` receives security fixes.

## Reporting a vulnerability

Please report vulnerabilities **privately** rather than opening a public
issue: use GitHub's *Report a vulnerability* button under the Security tab,
or contact the maintainers directly.

Include the affected version, reproduction steps, and impact if known. We
aim to acknowledge within a few working days.

## What is checked automatically

Every push and pull request runs, and a weekly scheduled job re-runs:

* `ruff` with the `S` (bandit) rules — insecure patterns in this codebase.
* `pip-audit` — dependencies with published advisories.

The scheduled run matters because a dependency advisory can be published
long after the code last changed.
