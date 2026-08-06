# QA, step by step

What each check is for, and why it is configured the way it is.

The authoritative configuration lives in `pyproject.toml` and
`.pre-commit-config.yaml`. This document explains the reasoning rather than
repeating those files, because a copy goes stale the moment either changes.

```text
git commit  ->  ruff check  ->  ruff format  ->  mypy
git push    ->  pytest (with coverage)  ->  pip-audit
```

Continuous integration runs all of it again on every push and pull request.
Hooks are a local convenience and can be skipped with `--no-verify`; the
pipeline is what actually holds the standard.

Run everything yourself with one command:

```shell
uv run python qa.py check
```

## The tools

### Formatting — `ruff format`

An opinionated formatter. It rewrites code into one canonical form, so
formatting stops being a matter of opinion or review comments.

```shell
uv run python qa.py format   # apply
uv run python qa.py check    # report only, as CI does
```

### Style and correctness — `ruff check`

Linting asks a different question from formatting: not *how does it look*, but
*is it suspicious, wrong, or dangerous*. The `select` list is deliberately
broad, enabling around fifty rule families including `S` (security), `ANN`
(annotations required), and `D` (docstrings required).

```shell
uv run python qa.py lint   # report only
uv run python qa.py fix    # repair what can be repaired, then format
```

Three settings are worth understanding.

**Auto-fix is off by default.** With `fix = true`, a plain `ruff check .`
silently rewrites files, which is surprising for a command that reads like an
inspection. Auto-fix is opted into explicitly instead: in the pre-commit
hook's own `entry` line, and never in CI.

**Two ignored rules are mandatory.** `D203` and `D212` each contradict a
sibling rule (`D211`, `D213`). Ruff reports the conflict in a startup warning
and one side of each pair must be off. `COM812` conflicts with the formatter,
which already owns trailing commas.

Nothing else is ignored for convenience. `D400` and `D415` were both switched
off here for a while, described as another mutually exclusive pair. They are
not one — ruff runs them together without complaint, they are alternatives
between docstring conventions — and with both off, nothing at all required a
docstring summary to end in punctuation. Nine violations had accumulated
behind the setting.

**Tests get one exemption.** `S101` bans `assert`, which is right for
production code, where `python -O` strips assertions. In tests `assert` is
exactly what pytest is built around, so `per-file-ignores` allows it there and
nowhere else.

### Types — `mypy --strict`

Python only reports a type error when the offending line actually runs.
Annotations let mypy check the whole program without running it, moving a
class of bug from production to development.

```shell
uv run python qa.py types
```

Annotate attributes rather than relying on inference. An attribute assigned
`None` in `__init__` is inferred as exactly `None`, which makes the checker
reject correct code later and teaches people to reach for `# type: ignore`.

### Tests — `pytest`, `pytest-cov`

```shell
uv run python qa.py test   # everything, with the coverage requirement
uv run python qa.py fast   # skip the slow end-to-end tests
```

Use `qa.py fast` rather than passing `-m 'not integration'` yourself. The
slow tests are the only cover for some of the code, so deselecting them
without also turning off coverage measurement fails the 100% requirement and
reports a coverage error to somebody who only asked to skip slow tests.

**Branch coverage is on.** Without it, coverage measures only whether each
line ran: a function containing `if x:` whose tests never take the false path
still scores 100%, and the untested path passes silently.

**Coverage must reach 100%,** and it is worth being clear about what that
means. Coverage measures which lines executed, never whether the result was
correct. A test that calls everything and asserts nothing still scores 100%.
Treat it as a floor that catches untested code, not as proof of quality.

**Warnings are errors.** `filterwarnings = ["error"]` means a deprecation is
found when it is announced rather than when it is removed. Third-party
warnings you do not own should be silenced individually rather than by
removing the setting:

```toml
filterwarnings = [
    "error",
    "ignore:some message:DeprecationWarning:some_package",
]
```

**A passing `xfail` is a failure.** `xfail_strict = true` means a fixed bug
does not sit unnoticed behind a stale marker.

**Markers must be registered** in `[tool.pytest.ini_options]`, and
`--strict-markers` makes a mistyped one a collection error rather than a
silent no-op that quietly deselects nothing.

**`if TYPE_CHECKING:` blocks are excluded from coverage.** They have to be:
ruff's `TC` rules actively move type-only imports into such a block, which by
design never runs, so the linter would otherwise push you into code the
coverage gate then fails you for.

Two habits matter more than the number. Use plain `assert`, because pytest
rewrites assertions to show the actual values on failure. And never let a test
depend on the real `sys.argv` — use `monkeypatch`, which also restores state
afterwards, or the test breaks the moment anyone runs `pytest -k` or uses an
IDE test runner.

### Consistency — `tests/test_release.py`

Some facts have to agree across files nobody ever edits together: the version
in `pyproject.toml`, the version in `uv.lock`, and the one the package
reports. Each drifts silently, and each is discovered at the worst possible
moment. That file checks them, along with what the built wheel actually
contains — that `py.typed` ships, that the tests do not, and that no
oversized file has been committed where it will slow every clone for ever.

The wheel checks are marked `integration`, so `qa.py fast` skips them and the
inner loop stays quick.

### Properties — `hypothesis`

An ordinary test checks a case you thought of. That is its weakness: the bugs
that survive a suite are the ones nobody imagined, so a suite made entirely of
examples keeps missing the same class of thing however many examples you add.

A property states a rule that must hold for *every* input, and Hypothesis goes
looking for the input that breaks it — hundreds of shapes per run, including
the empty string, the trailing newline, and pathological unicode nobody would
sit down and type. When it finds a failure it *shrinks* it to the smallest
example that still fails, so the report names something readable, and saves it
so that case is replayed for ever afterwards.

`tests/test_qa.py` carries a worked example to copy: whatever command `qa.py`
echoes, reading that line back the way a shell would has to yield the same
arguments it was handed. The rule holds for every command; no list of examples
could say as much.

This is not free. Properties take longer to think of than examples, because
you have to find the rule rather than the case. Reach for them where the rule
is clear — round trips, operations that must change nothing the second time
they run, outputs that must satisfy an invariant whatever went in — and use
plain examples everywhere else.

It earns its place. The first run of that property found a project name with a
trailing newline passing validation, because `$` in a Python regex also
matches immediately before a final newline. `\Z` is the anchor that means what
`$` looks like it means.

Hypothesis's record of past failures lives in `.hypothesis/`, a local cache
Git never sees. A case worth keeping goes into a parametrised example beside
the property, where it is shared and stays fast.

### Test order — `pytest-randomly`

The order tests run in is an accident, and a suite that depends on that
accident is green and lying. It happens through global state: one test leaves
a logger at `DEBUG`, or a module imported, or an environment variable set, and
another passes only because of it.

`pytest-randomly` shuffles the order on every run, so that dependency surfaces
as a failure instead of hiding. There is nothing to learn and no API to call —
installing it is the whole change.

The cost is that a failure may not reproduce next run. Every run prints the
seed it used, so pin it to get the same order back:

```shell
uv run pytest --randomly-seed=12345
```

Here it guards something specific. `tests/conftest.py` restores the global
logging state after every test, because command-line entry points call
`logging.basicConfig(force=True)`, which rebinds the root handlers to whatever
`sys.stderr` was at that moment — under pytest, the current test's capture
buffer. That fixture is load-bearing, and in a fixed order a broken one would
leave the suite green.

<!-- template-only:start -->
### The whole path, with real Git — `tests/test_journey.py`

Every other test about the hooks reads the task table or
`.pre-commit-config.yaml` and checks what they *say*. None of them ever
installed a hook, made a commit, or pushed — so nothing proved that a badly
formatted commit is actually refused, or that the pre-push stage exists
anywhere but in a line of YAML. Those are the gates this project is for.

This clones the repository with real `git clone`, runs the one documented
setup command, and then lets Git run the hooks: a lint violation is refused
at commit, a clean change is accepted, and a push whose coverage has dropped
is refused at the push stage. It also generates a project with
`--no-install` and finishes it by hand, which is the path somebody who
skipped a step has to be able to take.

It takes about a minute, and is marked `integration` so `qa.py fast` skips
it. The hooks it triggers run this suite again, so the tests skip themselves
when they find `QA_JOURNEY_RUNNING` in the environment — without that
guard, each journey starts another one inside itself.
<!-- template-only:end -->

### The pipelines themselves — `zizmor` and `check-jsonschema`

The pipeline definitions are the one part of the repository nothing else
checks. ruff does not read YAML, so a mistake in either is found by a
pipeline failing rather than by a gate — and a workflow is code that runs
with credentials, which is worth auditing rather than merely parsing.

```shell
uv run --group pipeline zizmor --config zizmor.yml .github/workflows/
uv run --group pipeline check-jsonschema --builtin-schema vendor.gitlab-ci .gitlab-ci.yml
```

Both found real problems on their first run:

* `actions/checkout` leaves the job's credentials in `.git/config` unless
  told not to, where anything later archiving the workspace can pick them
  up. Nothing here pushes, so `persist-credentials: false` costs nothing.
* The GitLab coverage regex escaped its `%`. GitLab parses that pattern with
  RE2, where `\%` is not a valid escape at all, so the coverage figure risked
  never being reported and nobody would have noticed a number quietly
  missing from merge requests.

`zizmor.yml` records one deliberate exception: actions are pinned to tags
rather than commit hashes. Hashes are stronger — a tag can be moved — but
they are unreadable in review and go stale unless somebody keeps Dependabot
moving, and this pipeline holds no secrets and has read-only permissions.
The policy still refuses an action tracking a *branch*, which is the case
that actually bites. The reasoning is in the file, next to the setting, so
the trade-off can be revisited rather than rediscovered.

### Whether the tests would notice — `cosmic-ray`

Coverage says a line *ran*. It cannot say whether any assertion would have
*noticed* that line changing, and those are different questions: a test that
calls everything and asserts nothing scores 100%.

Mutation testing answers the second one. It alters the source one small change
at a time — `==` to `<`, `127` to `128`, `True` to `False` — and runs the tests
against each. A mutant the suite still passes is a line nothing is checking.

```shell
uv run --group mutation cosmic-ray init mutation.toml mutation.sqlite
uv run --group mutation cosmic-ray exec mutation.toml mutation.sqlite
uv run --group mutation cr-report --show-diff mutation.sqlite
```

It is not a gate and not in the `dev` group, so `uv sync --dev` never installs
it. One test run per mutant is far too slow to sit in front of a commit.

**Verify the harness before believing the score.** Point `test-command` at
tests that cannot possibly cover the module and run it again: almost every
mutant must *survive*. If everything is reported killed, the command is failing
for its own reasons and every "kill" is a lie. That is not a hypothetical — a
bare `python -m pytest` here resolved to an interpreter outside the project
with no pytest installed, exited non-zero on every mutant, and produced a
flawless score that measured nothing whatsoever. The control run is what
caught it.

It found two real gaps in a suite at 100% branch coverage:

* Every exit status was checked by comparing it with the same constant it came
  from, so `COMMAND_NOT_FOUND_STATUS = 127` could become `128` and both sides
  moved together. The numbers are the point — they are what a shell already
  means — so the tests now assert them literally.
* `logging.basicConfig(force=True)` could become `force=False` unnoticed, and
  that argument is load-bearing: without it the format is silently ignored
  whenever anything else has already configured the root logger.

Scores afterwards: `qa.py` 94%, `basics/` 83%. The survivors are equivalent
mutants that cannot be killed without contorting the code — the
`if __name__ == "__main__":` guard, which never runs under pytest, and
comparisons like `args.v == 0` against `<= 0` where the value is a count and
can never be negative. A perfect score is not the goal; reading the survivors
and deciding which are real is.

### Running tests in parallel — measured, and not adopted

`pytest-xdist` was evaluated rather than assumed. On this suite, `-n 4` takes
about 9 seconds against 17 sequentially, coverage still reports 100%, and three
consecutive runs were stable. It works.

It is still not installed. The full suite is already 17 seconds and `qa.py
fast` is about 4, so the saving lands on the run people make least often, in
exchange for interleaved output that is harder to read when something fails.
Add it if the suite grows to where that trade changes:

```shell
uv add --dev pytest-xdist && uv run pytest -n 4
```

Install it properly rather than reaching for `uv run --with pytest-xdist`. That
builds an ephemeral environment and points `sys.executable` at it, so the tests
that launch subprocesses fail confusingly and coverage collapses to nonsense —
an artefact of the shortcut, not a finding about xdist.

### Security — `ruff` and `pip-audit`

Two different concerns needing two different tools:

* **Insecure patterns in our own code** — ruff's `S` rules (bandit), already
  in the `select` list.
* **Known vulnerabilities in what we depend on** — `pip-audit`, which checks
  installed packages against the Python Packaging Advisory Database. Ruff
  cannot do this; it reads source code and knows nothing about advisories.

```shell
uv run python qa.py audit
```

A `pip-audit` failure with no code change means a new advisory was published
against an existing dependency. That is the tool working, not a false
positive.

## Supply chain

Three defences, in order of what they cost you.

**A committed, hash-pinned `uv.lock`.** CI installs with `--locked`, which
fails if the lock file and `pyproject.toml` have drifted apart.

**A dependency cooldown**, `exclude-newer = "7 days"`. Releases published in
the last week are ignored. Most malicious uploads are caught and withdrawn
within a day or two, so the cooldown removes the window in which one would be
installed. Overriding it is a deliberate act:

```shell
uv lock --exclude-newer "0 days"
```

**Auditing**, on every pipeline run and weekly on a schedule, because an
advisory can be published long after the code stopped changing.

CI also sets `UV_MALWARE_CHECK=1` to check for known-malicious packages rather
than merely vulnerable ones. It is set for every job, not for the audit step
alone. uv performs the check whenever it resolves, so the narrower placement
did run it — but it ran last, after the test job had already installed and
executed every dependency. Catching a malicious package after running it is
not catching it, so the install itself is what needs gating.

The check is experimental and hard-fails when OSV cannot be reached, which is
the other reason it belongs in CI rather than in `pyproject.toml`.

Malware checking is deliberately **not** enabled in `pyproject.toml`. Setting
`[tool.uv.audit] malware-check = true` makes every `uv sync` contact OSV and
fail when it cannot, breaking offline work and any network that intercepts
TLS, as many corporate proxies do. CI is the right place for it.

CI publishes a CycloneDX SBOM too, so "are we affected?" is a lookup rather
than an investigation.

### Keep the upper bounds

Tools that decide pass or fail carry an upper version bound, not just a lower
one. This is not hypothetical: an unconstrained `pytest-cov` upgrade changed
how coverage is measured inside subprocesses and dropped measured coverage
from 100% to 88% with no code change, failing the gate on every push at once.

If you add a dependency, use `uv add`, then put the cap back by hand:

```shell
uv add some-package --dev
```

`uv add` rewrites `pyproject.toml` and will replace a pinned specifier such as
`ruff>=0.16.0,<0.17` with an unbounded one. Check the diff before committing.

## Packaging

The `[build-system]` table makes the project installable rather than a
"virtual" project that only runs from its source directory. That is what lets
`importlib.metadata.version()` resolve the version from real installed
metadata instead of parsing `pyproject.toml` at import time.

The distribution name (`basics-qa-python`) differs from the import package
name (`basics`), so the mapping is stated explicitly under
`[tool.hatch.build.targets.wheel]`.

`py.typed` ships inside the package. Without that marker, type checkers ignore
the annotations entirely and consumers of a fully typed package get nothing.
CI builds the wheel and asserts the marker is there, because an editable
install hides its absence.

`[project.scripts]` declares a console entry point, so installing the project
gives a real command. CI installs the built wheel and runs that command,
because a broken entry point is invisible until something does.

## Logging

Verbosity is set on the **package** logger, not the CLI module's own:

```python
logging.getLogger(__package__).setLevel(level)
```

This matters as soon as the package has more than one module. Setting it on
the module's own logger silently mutes every sibling regardless of `-v`, and
the symptom is invisible while the package is a single file.

The default level is `WARNING`, not `CRITICAL`. At `CRITICAL` an application
built on this skeleton loses its own `logger.warning()` and `logger.error()`
calls unless the user happens to pass `-v` — which is the one situation where
a message most needs to be seen.

## Python version

`.python-version` pins the interpreter uv selects, so everyone gets the same
one by default. It must stay consistent with `requires-python`.

**Careful in CI.** `.python-version` takes precedence over whatever is merely
installed, for *every* uv command including `uv run`. A test matrix therefore
has to override it explicitly, which this project does with the `UV_PYTHON`
environment variable per job. Without that, every job silently tests the same
interpreter while appearing to test several.

`requires-python` has no upper bound, so it claims support for interpreters
that do not exist yet. Every version it allows is in the CI matrix; a version
left out is one the project promises and has never run.

## Git hooks

```shell
uv run python qa.py setup
```

That installs the environment and both hook stages. Both are needed:
`pre-commit install` on its own installs only the commit stage, silently
leaving the tests and the audit un-run on push.

Fast checks run on commit and slow ones on push. Commits are frequent and must
stay fast, or the hooks get switched off and catch nothing.

Every hook sets `pass_filenames: false`, because each tool already targets the
whole project. Without it, pre-commit appends changed filenames to a command
that also says `.`, checking those files twice.

Run the hooks by hand, without making a commit:

```shell
uv run pre-commit run --all-files --hook-stage pre-commit
uv run pre-commit run --all-files --hook-stage pre-push
```

## Housekeeping

`.gitignore` keeps generated and private files out of the repository:
bytecode, the virtual environment, IDE folders, build artefacts, tool caches,
coverage reports, and `.env` files. Coverage writes one file per process when
measuring subprocesses, named `.coverage.<host>.<pid>.<random>`, so the
pattern `.coverage.*` is listed alongside the plain name. Hypothesis's
`.hypothesis/` is there too, and `new_project.py` excludes every one of these
from a generated project, so a new project never starts life holding another
project's cached state.

<!-- template-only:start -->
## Acceptance, by hand, once per release

Everything above is automated, and automation cannot tell you that a correct
instruction is a confusing one. This takes about fifteen minutes and is worth
doing before tagging a release.

Use a machine that has never seen this project — Windows Sandbox, a fresh
container, a borrowed laptop. The point is to have no cache, no `uv` already
on `PATH`, and no memory of what the commands do.

1. Follow the platform guide for that operating system, **copy-paste only**.
   Do not fix anything silently. If you reach for knowledge that is not on
   the page, that is the finding.
2. `git clone`, then `uv run python qa.py setup`, then
   `uv run python qa.py check`. Note the wall-clock time to the first green
   run.
3. `uv run python new_project.py my-new-project`, then `cd ../my-new-project`
   and `uv run python qa.py check`. It must be green without touching
   anything.
4. In the new project, make a deliberately unformatted change and commit it.
   The commit must be refused, and the message must say why.
5. Read the generated `README.md` as though you had never seen the template.
   Does it describe *your* project, or somebody else's?

Write down every moment of hesitation, not just the failures. "I did not know
which terminal to use" is a defect in the documentation exactly as much as a
command that errors, and it is the only kind no test will ever report.
<!-- template-only:end -->

## Next

Back to [Get started](../README.md#get-started).
