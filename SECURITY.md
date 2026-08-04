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

* `ruff` with the `S` (bandit) rules — insecure patterns in this codebase,
  including hardcoded passwords and tokens (`S105`–`S107`).
* `pip-audit` — dependencies with published advisories.
* `zizmor` — the GitHub workflows themselves, which are code that runs with
  credentials and which nothing else lints.
* `check-jsonschema` — the GitLab pipeline, against GitLab's own schema.

The scheduled run matters because a dependency advisory can be published
long after the code last changed.

The published bill of materials is checked before it is uploaded. It used to
be generated and published without anything looking at it, so an empty or
malformed document would have been found by whoever needed it during an
incident.

## Secrets

Nothing here reads a `.env` file, but the projects generated from this one
will. `.gitignore` covers `.env` and `.env.*`, a test asserts none is
committed, and ruff's `S105`–`S107` catch a password or token written into
the source.

Entropy-based scanning — a key or token that looks like nothing in
particular — is a step beyond that, and not installed. Measured on this
repository it reports nothing:

```shell
git ls-files | uvx detect-secrets scan
```

Add it as a pre-commit hook once a project actually handles credentials.
Scan the tracked files rather than the working tree: `--all-files` walks
the caches and virtual environment too, and reports hundreds of hashes.

## Publishing

This project is not on PyPI, which `pip-audit` reports on every run as a
dependency it could not audit. That leaves the name unregistered and so
available to somebody else — a real risk for any project that later installs
its own package by name from a public index. Register the name before
publishing anything, or keep installs pinned to a private index.

## Attribution in generated projects

The notice at the top of each source file names this template's author, and
a generated project keeps it: the Apache licence requires a derivative work
to retain it, and removing it is the violation. The generated `README.md`
carries the new project's own copyright instead, with the attribution the
licence does require, because that file describes the new project rather
than this one.
