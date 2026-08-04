# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entries up to and including `3.0.0` are reconstructed from the Git history
(tags `1.0.0`, `2.0.0`, `2.0.1`, `3.0.0`) rather than written at release
time, so they are summaries rather than a contemporaneous record.

## [Unreleased]

### Added

- `tests/test_journey.py`: the whole path walked with real Git in a real
  clone — setup, a lint violation refused at commit, a clean change
  accepted, and a push refused by the pre-push stage. Every existing hook
  test read the configuration and checked what it said; none had ever
  installed a hook or made a commit, so nothing proved the push stage
  existed outside a line of YAML.
- Pipeline linting with `zizmor` and `check-jsonschema`, in a `pipeline`
  dependency group. The pipeline definitions were the one part of the
  repository nothing checked, and both tools found real problems on their
  first run.
- Mutation testing with `cosmic-ray`, in a `mutation` dependency group of
  its own so `uv sync --dev` never installs it and generated projects
  carry the configuration at no cost. Coverage says a line ran; this asks
  whether any assertion would have noticed it changing. It found two real
  gaps behind 100% branch coverage — every exit status compared against
  the constant it came from, so the value itself went unchecked, and
  `logging.basicConfig(force=True)` able to become `force=False`
  unnoticed. `qa.py` now scores 94% and `basics/` 83%, the remainder
  being equivalent mutants recorded in `docs/README-QA-Steps.md`.
- `tests/test_release.py`: the facts that must agree across files nobody
  edits together — the version in `pyproject.toml`, in `uv.lock`, and the
  one the package reports — plus what the built wheel actually contains
  and a size budget that catches a stray coverage database or wheel
  committed by accident. It ships into generated projects, which need the
  same checks.
- Tests for the edges that arrive from a shell rather than from a test:
  `--into` naming a file, a parent directory that does not exist yet, a
  path full of spaces and accents, a case-insensitive collision, a
  destination reached through a symlink, `-vvv`, an argument that looks
  like an option, and a gate killed by a signal.
- Property-based testing with `hypothesis`. A property states a rule that
  must hold for every input and lets the tool hunt for the input that
  breaks it, which is the class of bug an example-based suite keeps
  missing however many examples it accumulates. `tests/test_qa.py` carries
  a worked example, so the practice ships into generated projects with
  something to copy rather than as an unused dependency.
- `pytest-randomly`, shuffling the test order on every run. A test that
  passes only because another ran first leaves a suite that is green and
  lying, and running them in the same order every time is exactly what
  hides it. It guards `tests/conftest.py`, whose restoration of the global
  logging state is load-bearing and would otherwise go unchecked.

- `qa.py setup`: one command after cloning, installing the environment and
  both Git hook stages. Git does not clone `.git/hooks`, so a fresh
  checkout has no local gates until somebody remembers three separate
  commands — and forgetting is the usual reason a configured hook never
  runs. `README.md` and `CONTRIBUTING.md` now name this one instead.
- `tests/test_onboarding.py`: the template tested as somebody who has just
  cloned it would meet it — the name they pick, the command they copy out
  of the README, the step they skip. Written against the repository's own
  files, so documentation drifting from the code fails here rather than in
  somebody's afternoon. Not copied into generated projects.
- `qa.py`: the quality gates grouped under names, so they need not be
  memorised — `check` runs the whole CI sequence in CI's order, stopping at
  the first failure. Not a `Makefile`, because `make` is absent from a
  default Windows install and this project asks you to install only Git and
  `uv`; standard library only, like `new_project.py`, and it ships into
  generated projects.
- `new_project.py`: one command creates a new, fully renamed project in its
  own directory, with the environment installed and Git hooks in place.
  Standard library only, so it runs straight after `git clone` and adds
  nothing to the supply chain of the projects it creates.
- `.gitlab-ci.yml`, running the same gates as the Git hooks and GitHub
  Actions, for the move to GitLab.
- Supply-chain hardening: a seven-day dependency cooldown
  (`exclude-newer`), `UV_MALWARE_CHECK` in CI, and a CycloneDX SBOM
  published as a pipeline artefact.
- CI workflow (`.github/workflows/qa.yml`) running formatting, linting, type
  checking, tests, and a dependency vulnerability audit on every push and
  pull request, across Python 3.11-3.13.
- Dependency vulnerability scanning with `pip-audit`, run both locally and
  in CI.
- `[build-system]` (hatchling), making the project actually installable —
  previously `uv` treated it as a non-installable "virtual" project.
- `.python-version`, pinning the interpreter `uv` selects by default.
- This file, `CONTRIBUTING.md`, and `SECURITY.md`.
- `py.typed`, so consumers actually receive the type information the package
  already satisfies. CI builds the wheel and asserts the marker ships.
- `[project.scripts]` console entry point, plus a `--version` flag.
- `[project] classifiers` and `[project.urls]` metadata.
- `.gitattributes`, normalising line endings. Without it Git stores LF while
  Windows checks out CRLF, so every commit from a Windows machine reports
  changes to files nobody touched.
- `.editorconfig`, and a Dependabot configuration covering both Python
  dependencies and the workflow's own actions.
- Branch coverage (`branch = true`). Line coverage alone reports 100% for an
  `if` whose false path is never tested.
- `filterwarnings = ["error"]` and `xfail_strict = true`.
- `strict = true` for mypy: the code already satisfied it, so this stops the
  standard regressing rather than raising it.
- Seven further ruff rule families: ASYNC, FA, FURB, INT, LOG, PERF, SLOT.
- CI now tests macOS and Windows as well as Linux, matching the three
  platforms the setup documentation covers; a weekly scheduled run catches
  advisories published between pushes; and a separate job builds and installs
  the wheel.

### Changed

- Replaced `black` with `ruff format` (one tool instead of two, same
  formatting rules already configured for `ruff`).
- Type-annotated the `Cli` placeholder attributes, so `mypy` distinguishes
  the always-set `argument1` from the genuinely optional `option1`.
- Capped `pytest-cov` and `ruff` to known-safe ranges after finding that an
  unconstrained `pytest-cov` upgrade silently drops measured coverage on
  this project's subprocess-based tests.
- `tests/__init__.py` now imports `__version__` from `basics` instead of
  duplicating the same version-lookup logic.
- `ruff` no longer auto-fixes by default: `fix = true` made a plain
  `ruff check .` rewrite files. Auto-fix is now opted into explicitly, in
  the pre-commit hook only.
- All `pre-commit` hooks now set `pass_filenames: false` consistently.
- Rewrote `docs/README-QA-Steps.md` to explain the reasoning behind each
  tool rather than duplicating `pyproject.toml` verbatim — the duplication
  was the reason the document drifted out of date.
- Filled in the README's `Use` section (previously a bare `TODO`).
- Rewrote `README.md`, `CONTRIBUTING.md`, and all four documents under
  `docs/` to be shorter and easier to follow, with every command checked
  against what the code actually does. The README now lists every `qa.py`
  task; five of them were documented nowhere.
- `qa.py check` installs from the lock file first, as CI does. Without it a
  green `check` could not promise a green pipeline: a lock file that had
  drifted from `pyproject.toml` failed CI at its first step.
- Python 3.14 is tested in CI and declared in the classifiers.
  `requires-python` has no upper bound, so it already promised support for
  an interpreter nothing had ever run.
- `pip-audit` runs as a `pre-push` hook, so the dependency audit is not
  something only CI performs.
- The GitLab pipeline's packaging stage now checks the same things the
  GitHub one does: the full path of `py.typed`, that the package module
  ships, and that the console script runs from an installed wheel.

### Fixed

- The GitLab coverage regex no longer escapes its `%`. GitLab parses that
  pattern with RE2, where `\%` is not a valid escape at all, so the
  coverage figure risked never being reported — and a number quietly
  missing from merge requests is not something anybody notices.
- `actions/checkout` no longer leaves the job's credentials behind in
  `.git/config`, where anything later archiving the workspace could pick
  them up. Nothing in either pipeline pushes.
- `--into` naming a file is refused with the reason. It used to reach
  `copytree`, fail with "the system cannot find the path specified" naming
  a path that plainly exists, and be reported as the Windows
  260-character limit — sending somebody off to shorten a name that was
  never the problem. A directory that cannot be written to now says that
  too, instead of borrowing the same wrong explanation.
- Ctrl-C during a gate exits 130 with one line, rather than unwinding
  through `subprocess` internals as a traceback. An interruption is a
  deliberate act, and printing a crash for one teaches people to ignore
  the output.
- A project name ending in a newline is rejected rather than accepted.
  `$` in a Python regular expression also matches immediately before a
  trailing newline, so `my-app\n` — what a name pasted out of a file
  arrives as — validated and went on to create a directory with a newline
  in its name. The pattern is anchored with `\Z` now. Found by the first
  run of the new property test, and kept as an example beside it.
- `--into ~/work` now expands the tilde itself. PowerShell does not expand
  `~` in arguments to native commands, so on Windows the documented example
  created a directory literally named `~` instead of using the home
  directory.
- Generated projects are written with LF line endings on every platform.
  On Windows, `write_text`'s platform default turned every rewritten file
  CRLF, and the new project's first commit then drowned in
  "CRLF will be replaced by LF" warnings from its own `.gitattributes`.
- Generated projects no longer ship a lock file that disagrees with their own
  `pyproject.toml`. `uv.lock` records the project as one of its packages, and
  renaming left that entry at the template's version, so `qa.py setup` failed
  on its first command with `uv sync --locked` refusing to install anything.
- Generated projects pass their own gates without needing the install step to
  repair them. Renaming perturbed import order and line length, so a
  `--no-install` project started out failing `ruff check` and `ruff format`.
  The template's own sources are now written so the rename cannot disturb
  them, and a test runs the gates against a generated project.
- The generated `README.md` no longer tells its reader to run
  `new_project.py`, which generated projects deliberately do not ship.
- Generated projects no longer inherit the template's authors, maintainers,
  and repository URLs, which described somebody else's project.
- `qa.py` reports a missing `uv` instead of raising `FileNotFoundError`
  through a traceback naming `subprocess` internals.
- Coverage data files written by a parallel run (`.coverage.<host>.<pid>`)
  are no longer copied into generated projects, and are ignored by Git.
- `--help` no longer points at `app_cli.py`, which is not in the installed
  wheel. It now shows however the program was actually started.
- The default log level is `WARNING` rather than `CRITICAL`, so an
  application built on this skeleton keeps its own warnings and errors.
- `UV_MALWARE_CHECK` is set for every job in both pipelines rather than on
  the audit step alone. uv performs the check whenever it resolves, so the
  old placement did run it, but it ran last: the test job had already
  installed and executed every dependency by then. On GitLab it covered one
  job of seven, and not the ones that run what was installed.
- `D400` and `D415` are enforced rather than ignored. They were described as
  a mutually exclusive pair, which they are not, and disabling both left
  nothing requiring a docstring summary to end in punctuation.
- Test runs no longer leave global logging state behind. A command-line entry
  point calling `logging.basicConfig(force=True)` bound the root handler to
  one test's capture buffer, and five later log records were lost to
  "--- Logging error ---" on every run while the suite still reported green.
- `new_project.py` refuses Windows device names (`con`, `nul`, `com1`, and
  the rest), and explains a filesystem failure such as the Windows 260
  character path limit rather than printing a traceback.
- Documented commands that could not work: `pytest -m 'not integration'` in
  the QA guide (fails the coverage gate; `qa.py fast` is the one that
  works), `app_cli.py` with no argument in the README, and
  `mkdir project_name && uv sync` in all three platform guides.
- `new_project.py` no longer reports success after a setup step failed.
  `run()` logged the failure at WARNING, but `main()` puts the logger at
  CRITICAL unless `-v` is passed, so the one message meant to surface it
  was suppressed at the default verbosity: a failed `uv sync` printed
  nothing from the script, `Created ...` followed as though all was well,
  and the exit status was zero. Failures now go to stderr regardless of
  verbosity, every remaining step is still attempted, and the exit status
  is non-zero with the failed commands listed to run by hand.
- `qa.py fast` no longer fails every time it runs. It deselects the
  integration tests, which are the only cover for `app_cli.py`, so the
  100% gate was unreachable and the task reported a coverage shortfall to
  anyone who only asked to skip the slow tests. It now passes `--no-cov`.
  The `integration` marker's own help text in `pyproject.toml` described
  the same failing invocation and now points at `qa.py fast`.
- `new_project.py` refuses to generate a project inside the template.
  Nested, both copies of `tests/test_cli.py` are collected and pytest
  aborts *every* test module with "import file mismatch" — the whole
  suite, not just the copy — while ruff lints the duplicate too. The
  template looks broken and nothing in the output names the cause.
- `new_project.py` no longer accepts three kinds of name that produced a
  broken project or a crash:
  - Python keywords (`class`, `import`, `del`). The package took the
    keyword's name, so `from class.cli import ...` was a `SyntaxError` and
    the generated project could not be imported, tested, or run at all.
  - Standard library module names (`json`, `email`, `types`), which the new
    package silently shadowed — a hard bug to read, and far from its cause.
  - Names the template already ships (`tests`, `docs`, `qa`). `tests`
    aborted halfway through with a `FileExistsError` traceback and left a
    half-built directory behind.

  All three are now refused before anything is written, with a message
  saying what to use instead.
- `ruff check --fix` now runs before `ruff format` everywhere — the
  pre-commit hooks, `new_project.py`, and `qa.py` — which is the order
  ruff recommends. Sorting imports is itself a linter fix, so formatting
  first left the linter's own rewrites as the final state, never having
  been through the formatter. The three disagreed with each other before.
- Generated projects no longer start out failing their own `ruff check`.
  Renaming the package changes where it sorts among the imports (`basics`
  precedes `tests`, `web-api` does not), so `new_project.py` now runs
  `ruff check --fix` before `ruff format`. Only names sorting after `tests`
  were affected, which is why it went unnoticed.
- `new_project.py` no longer leaks the template's `VIRTUAL_ENV` into the
  setup commands it runs in the new project. Started via `uv run`, it
  inherited a variable pointing at the template's own environment, so every
  `uv` call in the generated project warned that it did not match and was
  being ignored -- four times per run, suggesting `--active`, which would
  have installed the new project into the template's environment.
- Test suite no longer breaks under `pytest -k` or IDE test runners: a test
  was mutating the real `sys.argv` instead of using `monkeypatch`.
- Integration tests no longer require `uv` to be on `PATH`; they launch the
  application via `sys.executable`.
- Tests use plain `assert` instead of manually raising `ValueError`,
  restoring pytest's readable failure diffs.
- `--help` no longer tells users to run `pipenv`, which was removed from
  this project in `3.0.0`.
- Corrected the `SECURITY` notes in both `pyproject.toml` and
  `docs/README-QA-Steps.md`, which claimed coverage from `pipenv check` —
  a tool removed in `3.0.0` — and implied `ruff` audits dependencies, which
  it does not.
- CI sets `UV_PYTHON` per matrix job. Without it, `.python-version` takes
  precedence for every `uv` command, so all three matrix jobs would test
  the same interpreter while appearing to test three.
- Deprecated `TCH` rule selector renamed to `TC`; `COM812` ignored, as it
  conflicts with the formatter.
- Verbosity now applies to the whole package, not only the CLI module.
  `-v` previously had no effect on any other module's log records, which
  is invisible while the package has a single file and wrong in every
  project built from it.
- `if TYPE_CHECKING:` excluded from coverage. `ruff`'s `TC` rules move
  type-only imports into that block, which never executes at runtime, so
  the linter pushed code into a shape the coverage gate then rejected.
- Registered the `integration` marker and enabled `--strict-markers`, so
  the documented fast/slow split works and a mistyped marker is an error
  rather than a silent no-op.
- README rename instructions now cover the distribution name, the import
  package name, and capitalised prose separately, with a verification
  command -- a missed reference otherwise ships the template's name in
  your application's `--help`.

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

[Unreleased]: https://github.com/nunoachenriques/basics-qa-python/compare/3.0.0...HEAD
[3.0.0]: https://github.com/nunoachenriques/basics-qa-python/compare/2.0.1...3.0.0
[2.0.1]: https://github.com/nunoachenriques/basics-qa-python/compare/2.0.0...2.0.1
[2.0.0]: https://github.com/nunoachenriques/basics-qa-python/compare/1.0.0...2.0.0
[1.0.0]: https://github.com/nunoachenriques/basics-qa-python/releases/tag/1.0.0
