# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entries up to and including `3.0.0` are reconstructed from the Git history
(tags `1.0.0`, `2.0.0`, `2.0.1`, `3.0.0`) rather than written at release
time, so they are summaries rather than a contemporaneous record.

## [Unreleased]

### Fixed

- The README's Contents list rendered as five separate lists with gaps
  between them: the template-only markers at column zero are HTML blocks,
  which end a list in CommonMark. The markers inside the list are now
  indented as list-item continuation lines, and the scaffolder's pattern
  accepts the indentation.

### Added

- Pedro Nascimento joins the authors, and the History tells how: Nuno's
  challenge to contribute, taken up and reviewed together as a team.

### Changed

- "Quality assurance" shortened to "QA" in prose, headings, and the GitHub
  workflow name. The project title keeps the full phrase.
- Ruff bumped from `>=0.12.9,<0.13` to `>=0.16.0,<0.17`. No newly-enabled
  rule fires and the formatter output is unchanged, so the bump is the
  specifier, the lock, and the guide's example of it.

## [4.0.0] - 2026-08-04

The release that turns this from a worked example into a template: one
command creates a new project, one command prepares a fresh clone, and the
gates are tested rather than merely configured.

Entries are kept to a line or two. The reasoning behind each one is in the
commit that made it, and the reasoning behind the tooling as a whole is in
[the quality guide](docs/README-QA-Steps.md).

### Added

- `new_project.py` — one command creates a fully renamed project in its own
  directory, environment installed and Git hooks in place. Standard library
  only, so it runs straight after `git clone`.
- `qa.py` — every gate behind a name, so none has to be memorised.
  `qa.py setup` after a clone, `qa.py check` for the whole CI sequence.
  Standard library only, because `make` is absent from a default Windows
  install and this project asks you to install only Git and `uv`.
- `[build-system]` (hatchling), a console script, `py.typed`, classifiers,
  and URLs. The project is installable rather than a "virtual" one.
- Continuous integration on every push and pull request, across three
  operating systems and four interpreters, plus a weekly run to catch
  advisories published since the last push.
- `.gitlab-ci.yml`, running the same gates, for the move to GitLab.
- Supply-chain hardening: a seven-day dependency cooldown,
  `UV_MALWARE_CHECK` in CI, Dependabot for both dependencies and actions,
  and a CycloneDX SBOM that is now validated before it is published.
- `tests/test_onboarding.py` — the template as somebody who has just cloned
  it meets it, asserted against the repository's own files, so
  documentation drifting from the code fails here rather than in somebody's
  afternoon.
- `tests/test_journey.py` — the same path walked with real Git: a lint
  violation refused at commit, a push refused by the pre-push stage.
- `tests/test_release.py` — the version in `pyproject.toml`, in `uv.lock`,
  and the one the package reports must agree, and the built wheel must
  contain the package but not the tests.
- `hypothesis` for rules that must hold over every input, with a worked
  example in `tests/test_qa.py`, and `pytest-randomly` so that a suite
  depending on test order fails instead of hiding.
- Mutation testing (`cosmic-ray`, in a `mutation` group that
  `uv sync --dev` does not install). `qa.py` scores 94%, `basics/` 83%.
- Pipeline linting (`zizmor` and `check-jsonschema`, in a `pipeline`
  group). The pipeline definitions were the one part of the repository
  that nothing checked.
- Stricter gates: branch coverage, `mypy --strict`, `--strict-markers`,
  `filterwarnings = ["error"]`, `xfail_strict`, and seven further ruff rule
  families.
- `CONTRIBUTING.md`, `SECURITY.md`, this file, `.editorconfig`,
  `.gitattributes`, `.python-version`, and a fifteen-minute manual
  acceptance script in the quality guide.

### Changed

- `ruff format` replaces `black`: one tool instead of two, same rules.
- `ruff` no longer auto-fixes by default. `fix = true` made a plain
  `ruff check .` rewrite files on disk; auto-fix is now opted into in the
  pre-commit hook alone, and CI always runs `--no-fix`.
- The linter runs before the formatter everywhere — the hooks, `qa.py`, and
  `new_project.py`. The three used to disagree with each other.
- `qa.py check` installs from the lock file first, as CI does, so a green
  `check` cannot promise a pipeline that a drifted lock would fail.
- `pip-audit` runs as a `pre-push` hook, not only in CI.
- Python 3.14 is tested and declared. `requires-python` has no upper bound,
  so it already promised an interpreter nothing had ever run.
- `pytest-cov` and `ruff` are capped: an unconstrained `pytest-cov` upgrade
  silently dropped measured coverage on this project's subprocess tests.
- Every document rewritten around what the commands actually do. The README
  lists all ten `qa.py` tasks; five of them were documented nowhere.

### Fixed

Generated projects:

- Shipped a lock file disagreeing with their own `pyproject.toml`, so
  `qa.py setup` failed on its very first command.
- Started out failing their own `ruff check` and `ruff format`.
- Claimed the template's authors, URLs, and — in the README — its
  copyright, while `pyproject.toml` beside it said `Your Name`. The notices
  in the source files stay, as the Apache licence requires.
- Inherited the template's `History` section, which also held the one place
  `basics` was an ordinary English word: renaming produced "compile some
  `my_new_project` of quality assurance".
- Were written CRLF on Windows, so the first commit drowned in warnings
  from the project's own `.gitattributes`.
- Carried stray `.coverage.*` files, and the template's `VIRTUAL_ENV` into
  every setup command.
- Told their reader to run `new_project.py`, which they deliberately do not
  ship.

Names and destinations, now refused before anything is written:

- Python keywords, standard library module names, Windows device names,
  names the template already ships, and a name ending in a newline — the
  last found by the first run of a property test.
- A destination inside the template, which made pytest abort every test
  module with an error naming nothing near the cause.
- `--into` pointing at a file, which used to be blamed on the Windows
  260-character path limit, and `--into ~/work`, which PowerShell does not
  expand.

Commands that misled the person running them:

- `qa.py fast` failed every single time. It deselects the only cover for
  `app_cli.py`, so the coverage gate was unreachable.
- A missing `uv` raised `FileNotFoundError` through `subprocess` internals
  rather than naming what to install.
- Ctrl-C printed a traceback instead of exiting 130.
- A failed setup step was suppressed at the default verbosity, so a failed
  `uv sync` printed nothing and `Created ...` followed it as though all was
  well, with a zero exit status.
- The QA guide, the README, and all three platform guides documented
  commands that could not work.

The application skeleton:

- The default log level was `CRITICAL`, so an application built on this one
  lost its own warnings and errors unless `-v` was passed.
- `-v` applied to the CLI module alone rather than the package, which is
  invisible until the package has a second module.
- `--help` named `app_cli.py`, which no wheel ships.

Continuous integration:

- Every matrix job tested the same interpreter, because `.python-version`
  takes precedence until `UV_PYTHON` is set per job.
- `UV_MALWARE_CHECK` ran last, after the tests had already installed and
  executed every dependency.
- `actions/checkout` left the job's credentials in `.git/config`.
- The GitLab coverage regex escaped its `%`, which RE2 rejects outright, so
  the coverage figure risked never being reported at all.

The test suite itself:

- Global logging state leaked between tests, losing log records while the
  suite still reported green.
- Tests mutated the real `sys.argv`, and required `uv` on `PATH`.
- `D400` and `D415` were disabled as a conflicting pair they are not,
  leaving nine violations behind the setting.

## [3.0.0] - 2025-08-20

### Changed

- **Breaking:** replaced `pipenv` with `uv` for environment and dependency
  management, across Linux, macOS, and Windows.

## [2.0.1] - 2024-07-04

### Fixed

- Windows `pyenv` installation documentation, corrected against a fresh
  test run.

## [2.0.0] - 2023-06-12

### Changed

- **Breaking:** replaced `flake8`, `isort`, and related tools with `ruff`.
- Improved logging; removed all `print()` calls and the `tqdm` dependency.
- Revised documentation and improved testing to match the new tooling.

## [1.0.0] - 2023-06-09

### Added

- Initial quality-assurance baseline: `pyproject.toml` replacing
  `setup.cfg`, `pre-commit` with separate commit/push stages, pytest with
  100% coverage required.
- Per-OS (Linux, macOS, Windows) setup documentation.

### Changed

- Formatting line length set to 100 (previously 120).

[Unreleased]: https://github.com/nunoachenriques/basics-qa-python/compare/4.0.0...HEAD
[4.0.0]: https://github.com/nunoachenriques/basics-qa-python/compare/3.0.0...4.0.0
[3.0.0]: https://github.com/nunoachenriques/basics-qa-python/compare/2.0.1...3.0.0
[2.0.1]: https://github.com/nunoachenriques/basics-qa-python/compare/2.0.0...2.0.1
[2.0.0]: https://github.com/nunoachenriques/basics-qa-python/compare/1.0.0...2.0.0
[1.0.0]: https://github.com/nunoachenriques/basics-qa-python/releases/tag/1.0.0
