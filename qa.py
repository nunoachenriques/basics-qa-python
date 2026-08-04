#  Copyright 2022 Nuno A. C. Henriques https://nunoachenriques.net
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
Basics on Quality Assurance in Python.

Run the quality gates by name, so nobody has to remember them.

A ``Makefile`` would serve the same purpose, but ``make`` is absent from a
default Windows install, and this project promises that Git and ``uv`` are
the only tools you must install. This script therefore uses the standard
library alone and runs wherever ``uv`` does.
"""

import argparse
import subprocess
import sys
from typing import NamedTuple, NoReturn

#: Exit status for a usage error, matching what argparse itself returns.
USAGE_ERROR_STATUS = 2

#: Exit status for a command that is not installed, as a shell reports it.
COMMAND_NOT_FOUND_STATUS = 127


class Task(NamedTuple):
    """A named group of commands, run in order until one fails."""

    description: str
    commands: tuple[tuple[str, ...], ...]


#: Every task, spelled out as the exact commands it runs. ``check`` mirrors
#: the continuous integration workflow in CI's own order - cheapest gate
#: first - so a failure is reported in seconds rather than after the full
#: test suite, and a green `check` locally means a green pipeline.
TASKS: dict[str, Task] = {
    "setup": Task(
        "First command after cloning: install the environment and Git hooks.",
        # Git does not clone .git/hooks, so a fresh checkout has no gates at
        # all until somebody runs `pre-commit install` - and forgetting to
        # is the single most common way a configured hook never runs. One
        # named command is easier to remember, and to put in a README, than
        # three.
        (
            ("uv", "sync", "--dev", "--locked"),
            ("uv", "run", "pre-commit", "install", "-t", "pre-commit"),
            ("uv", "run", "pre-commit", "install", "-t", "pre-push"),
        ),
    ),
    "sync": Task(
        "Install the environment exactly as the lock file pins it.",
        (("uv", "sync", "--dev", "--locked"),),
    ),
    "format": Task(
        "Format the code.",
        (("uv", "run", "ruff", "format", "."),),
    ),
    "fix": Task(
        "Repair every lint violation that can be repaired safely, then format.",
        # --fix first, the order ruff recommends and the one new_project.py
        # and the hooks use: sorting imports is a linter fix, so formatting
        # first leaves the linter's own rewrites as the final state, never
        # having been through the formatter.
        (("uv", "run", "ruff", "check", ".", "--fix"), ("uv", "run", "ruff", "format", ".")),
    ),
    "lint": Task(
        "Report lint violations without changing any file.",
        (("uv", "run", "ruff", "check", ".", "--no-fix"),),
    ),
    "types": Task(
        "Check the type annotations.",
        (("uv", "run", "mypy", "."),),
    ),
    "test": Task(
        "Run every test, with the coverage gate.",
        (("uv", "run", "pytest"),),
    ),
    "fast": Task(
        "Run only the quick tests, skipping the integration ones.",
        # --no-cov is not optional here. The integration tests are the only
        # cover for app_cli.py, so a deselected run cannot reach the 100%
        # gate and would fail every single time - reporting a coverage
        # shortfall to somebody who only asked to skip the slow tests.
        (("uv", "run", "pytest", "-m", "not integration", "--no-cov"),),
    ),
    "audit": Task(
        "Report known vulnerabilities in the installed dependencies.",
        (("uv", "run", "pip-audit"),),
    ),
    "check": Task(
        "Run every gate, exactly as continuous integration does.",
        (
            # The lock check comes first because CI's first step is the same
            # install, and a lock file that has drifted from pyproject.toml
            # fails the pipeline before any gate runs. Leaving it out made a
            # green `check` promise a green pipeline it could not deliver.
            ("uv", "sync", "--dev", "--locked"),
            ("uv", "run", "ruff", "format", "--check", "."),
            ("uv", "run", "ruff", "check", ".", "--no-fix"),
            ("uv", "run", "mypy", "."),
            ("uv", "run", "pytest"),
            ("uv", "run", "pip-audit"),
        ),
    ),
}


def printable(command: tuple[str, ...]) -> str:
    """
    Render a command as one line that can be pasted back into a shell.

    Arguments containing spaces are quoted. Joined on spaces alone, the
    ``fast`` task echoed ``-m not integration``, which reads as two
    arguments where the command has one - a different command from the one
    actually being run, and a broken one if anybody pasted it.

    :param command: The command and its arguments.
    :return: The command as a single line.
    """
    return " ".join(f'"{part}"' if " " in part else part for part in command)


def run(command: tuple[str, ...]) -> int:
    """
    Run one command, echoing it first so the output explains itself.

    :param command: The command and its arguments.
    :return: The command's exit status.
    """
    sys.stdout.write(f"$ {printable(command)}\n")
    sys.stdout.flush()
    try:
        return subprocess.run(command, check=False).returncode  # noqa: S603
    except FileNotFoundError:
        # This is the first command a new contributor runs, and `uv` missing
        # from PATH is the most likely reason it fails. A traceback naming
        # subprocess internals says nothing about what to install.
        sys.stderr.write(
            f"error: {command[0]} not found. Install it and make sure it is on "
            "your PATH - see the README prerequisites for your platform.\n",
        )
        return COMMAND_NOT_FOUND_STATUS


def run_task(name: str) -> int:
    """
    Run a task's commands in order, stopping at the first failure.

    Stopping matters: running the remaining gates after one has failed
    buries the message that actually needs reading.

    :param name: The task name, a key of :py:data:`TASKS`.
    :return: Zero if every command succeeded, else the failing status.
    """
    for command in TASKS[name].commands:
        status = run(command)
        if status != 0:
            return status
    return 0


def build_parser() -> argparse.ArgumentParser:
    """
    Build the command-line parser.

    :return: The configured parser.
    """
    listing = "\n".join(f"  {name:<8}{task.description}" for name, task in TASKS.items())
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Run a quality gate by name.",
        epilog=f"Tasks:\n\n{listing}\n\nExample:\n\n  uv run python qa.py check",
    )
    parser.add_argument(
        "task",
        choices=tuple(TASKS),
        metavar="TASK",
        nargs="?",
        help="The task to run.",
    )
    return parser


def main() -> NoReturn:
    """
    Provide the command-line entry point.

    :raises SystemExit: Always; the status of the task that ran, or
        :py:data:`USAGE_ERROR_STATUS` when no task was named.
    """
    parser = build_parser()
    task = parser.parse_args().task
    if task is None:
        # Naming the tasks is the useful answer to a bare `qa.py` - the whole
        # point of this script is that they need not be memorised. The status
        # stays non-zero even so: a hook or CI line that lost its argument
        # must fail loudly, not report success having run no gate at all.
        parser.print_help(sys.stderr)
        raise SystemExit(USAGE_ERROR_STATUS)
    raise SystemExit(run_task(task))


if __name__ == "__main__":
    main()
