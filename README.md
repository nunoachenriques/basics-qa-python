[![Apache 2.0 License](https://img.shields.io/badge/license-Apache%202.0-blue.svg "Apache 2.0 License")](http://www.apache.org/licenses/LICENSE-2.0.html)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)

# Basics on Quality Assurance in Python

A small Python project, set up the way a project should be set up: formatted,
linted, type-checked, tested with full coverage, and audited for known
vulnerabilities. Every one of those runs with a single command, and the same
command runs in continuous integration.

Use it as the starting point for a new project, or read it as a worked example.

You need two tools installed: `git` and `uv`. Everything else is installed for
you.

## Contents

* [Get started](#get-started)
* [Run the application](#run-the-application)
<!-- template-only:start -->
* [Start a new project](#start-a-new-project)
<!-- template-only:end -->
* [Everyday commands](#everyday-commands)
* [How the checks fit together](#how-the-checks-fit-together)
* [Install the prerequisites](#install-the-prerequisites)
* [Contributing](CONTRIBUTING.md)
* [Changelog](CHANGELOG.md)
* [History](#history)
* [License](#license)

## Get started

Clone the repository, then run one command:

```shell
uv run python qa.py setup
```

That installs the environment and both Git hooks. Run it after every fresh
clone. Git does not copy hooks, so until you do, nothing checks your commits
and the first sign of trouble is a red pipeline.

Then check that everything passes:

```shell
uv run python qa.py check
```

## Run the application

As shipped, the application parses its arguments, logs what it parsed, and
exits. `ARGUMENT1` is required.

```shell
uv run python app_cli.py ARGUMENT1
```

| Option | Meaning |
| --- | --- |
| `ARGUMENT1` | A placeholder positional argument. Required. |
| `-o OPTION1` | A placeholder option. |
| `-v` | Log at `INFO` level. Repeat as `-vv` for `DEBUG`. |
| `--version` | Print the version and exit. |
| `--help` | Print usage and exit. |

Without `-v` the run is silent:

```shell
uv run python app_cli.py hello
```

With an option and logging:

```shell
uv run python app_cli.py -o world hello -v
```

To build your own application, replace the body of `Cli.run()` in
`basics/cli.py`. Everything else is already in place.

<!-- template-only:start -->
## Start a new project

One command creates a new project from this one:

```shell
uv run python new_project.py my-new-project
```

That creates `../my-new-project`, renamed throughout, with its environment
installed and its Git hooks in place. Start writing code in `my_new_project/`.

```shell
cd ../my-new-project
uv run python app_cli.py --help
uv run python qa.py check
```

Useful variations:

```shell
# Put it somewhere other than alongside this project.
uv run python new_project.py my-new-project --into ~/work

# Copy and rename only. Skips git init, the environment, and the hooks.
uv run python new_project.py my-new-project --no-install

# Show what it is doing.
uv run python new_project.py my-new-project -v
```

The new project keeps every check described here and none of this project's
history. It starts at version `0.1.0` with an empty changelog, and it does not
carry `new_project.py` forward, so it is a project rather than another
template.

Prefer this over copying and renaming by hand. The name appears in four
different forms, and it renames all of them.
<!-- template-only:end -->

## Everyday commands

Every check is a plain `uv run` command, and running them by hand is always an
option. `qa.py` groups them under names so you need not remember them:

| Command | What it does |
| --- | --- |
| `uv run python qa.py setup` | Install the environment and the Git hooks. Run this first. |
| `uv run python qa.py check` | Run every check, exactly as continuous integration does. |
| `uv run python qa.py test` | Run the tests, with the coverage requirement. |
| `uv run python qa.py fast` | Run only the quick tests, skipping the slow ones. |
| `uv run python qa.py fix` | Repair what can be repaired, then format. |
| `uv run python qa.py lint` | Report problems without changing any file. |
| `uv run python qa.py format` | Format the code. |
| `uv run python qa.py types` | Check the type annotations. |
| `uv run python qa.py audit` | Report known vulnerabilities in dependencies. |
| `uv run python qa.py sync` | Install exactly what the lock file pins. |
| `uv run python qa.py --help` | List all of the above. |

`check` runs everything in the same order as continuous integration, cheapest
first, and stops at the first failure so the message that matters stays on
screen. Ctrl-C stops it with one line and the exit status a shell uses for an
interruption, rather than a traceback that reads like a crash.

Use `qa.py fast` rather than deselecting the slow tests by hand. They are the
only cover for some of the code, so skipping them without also turning off the
coverage requirement reports a coverage failure instead of the quick result you
asked for.

This is a script rather than a `Makefile` because `make` is not installed on
Windows by default, and this project asks you to install only `git` and `uv`.

## How the checks fit together

| Check | Tool | When |
| --- | --- | --- |
| Formatting | `ruff format` | On commit, and in CI |
| Style and correctness | `ruff check` | On commit, and in CI |
| Type annotations | `mypy --strict` | On commit, and in CI |
| Tests and coverage | `pytest` | On push, and in CI |
| Properties, over generated input | `hypothesis` | With the tests |
| Test-order independence | `pytest-randomly` | With the tests |
| Known vulnerabilities | `pip-audit` | On push, and in CI |
| Packaging | `uv build` | In CI |

The hooks run the fast checks when you commit and the slow ones when you push.
Continuous integration runs all of them again, on three operating systems and
four Python versions, because hooks can be skipped and a pipeline cannot.

The test run does two things beyond running the tests. It shuffles their order
every time, so a test that only passes because another ran first fails instead
of hiding; when one does fail, the printed seed replays that exact order. And
where a rule holds for every possible input rather than for a case somebody
thought of, `hypothesis` generates input looking for the one that breaks it —
`tests/test_qa.py` has a worked example to copy.

For the reasoning behind each choice, see
[Quality assurance, step by step](docs/README-QA-Steps.md).

To test the hooks themselves:

```shell
uv run pre-commit run --all-files --hook-stage pre-commit
uv run pre-commit run --all-files --hook-stage pre-push
```

## Install the prerequisites

**[Linux](docs/README-Linux.md)** &middot;
**[macOS](docs/README-macOS.md)** &middot;
**[Windows](docs/README-Windows.md)**

Confirm both tools are installed before going further:

```shell
git --version
uv --version
```

If `uv --version` reports that the command is not found, the installer
finished but your shell has not picked it up yet. Open a new terminal and try
again.

## History

It started in 2022 with an urge to compile some basics of quality assurance
for application development in Python. The motivation was and is to simplify,
automate, and guarantee a proper normalised and more secure code.

By me [Nuno A. C. Henriques](https://github.com/nunoachenriques) and by
[Alexandre Almeida](https://github.com/alexandre1-almeida)'s precious
contributions in code and vivid discussions!

## License

Copyright 2022 Nuno A. C. Henriques https://nunoachenriques.net

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
