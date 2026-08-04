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

Test the ``qa`` task runner.
"""

import shlex
import string
import subprocess
import sys

import pytest
from hypothesis import given
from hypothesis import strategies as st

import qa
from qa import (
    COMMAND_NOT_FOUND_STATUS,
    INTERRUPTED_STATUS,
    TASKS,
    USAGE_ERROR_STATUS,
    build_parser,
    main,
    printable,
    run,
    run_task,
)

#: An arbitrary non-zero status, distinguishable from a real tool's exit code.
FAILING_STATUS = 3

#: The characters a command argument realistically contains. Quotes and
#: backslashes are deliberately absent: :py:func:`qa.printable` quotes for
#: reading, not for surviving every shell ever written, and no task passes
#: an argument containing either.
ARGUMENT_CHARACTERS = string.ascii_letters + string.digits + "-_.=/"

#: One command argument: a few ordinary words, sometimes separated by the
#: spaces that are the whole reason quoting is needed at all.
ARGUMENTS = st.lists(
    st.text(alphabet=ARGUMENT_CHARACTERS, min_size=1, max_size=8),
    min_size=1,
    max_size=3,
).map(" ".join)


class TestTasks:
    """Test the task table itself."""

    def test_every_task_is_described(self) -> None:
        """``--help`` is the only documentation this script has."""
        assert all(task.description for task in TASKS.values())

    def test_every_task_runs_a_command(self) -> None:
        """A task with no commands would report success without doing anything."""
        assert all(task.commands for task in TASKS.values())

    def test_check_covers_the_continuous_integration_gates(self) -> None:
        """`check` green locally must mean the pipeline is green too."""
        commands = TASKS["check"].commands
        assert ("uv", "run", "ruff", "check", ".", "--no-fix") in commands
        assert ("uv", "run", "mypy", ".") in commands
        assert ("uv", "run", "pytest") in commands
        assert ("uv", "run", "pip-audit") in commands

    def test_read_only_tasks_do_not_write(self) -> None:
        """`lint` reports; only `fix` and `format` are allowed to edit files."""
        assert ("uv", "run", "ruff", "check", ".", "--fix") not in TASKS["lint"].commands
        assert ("uv", "run", "ruff", "check", ".", "--fix") in TASKS["fix"].commands

    def test_no_task_name_could_be_mistaken_for_an_option(self) -> None:
        """A task named `-x` would be unreachable: argparse would read it as a flag."""
        assert all(not name.startswith("-") for name in TASKS)

    def test_fix_repairs_before_it_formats(self) -> None:
        """Ruff recommends the linter first, so its rewrites reach the formatter."""
        commands = list(TASKS["fix"].commands)
        assert commands.index(("uv", "run", "ruff", "check", ".", "--fix")) < commands.index(
            ("uv", "run", "ruff", "format", "."),
        )


class TestRun:
    """Test :py:func:`run`."""

    def test_echoes_the_command_and_returns_its_status(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The command is echoed before it runs, and its status handed back."""
        # Run the interpreter already under test rather than a real tool: no
        # dependency on what happens to be installed, and it exits instantly.
        status = run((sys.executable, "-c", f"raise SystemExit({FAILING_STATUS})"))
        assert status == FAILING_STATUS
        # The whole command, not just the "$ " prefix: checking the prefix
        # alone still passed with the command text dropped entirely, which is
        # the part that makes the output explain itself.
        assert f"$ {sys.executable} -c" in capsys.readouterr().out

    def test_reports_success_as_zero(self) -> None:
        """A command that works reports zero."""
        assert run((sys.executable, "-c", "pass")) == 0

    def test_echoes_an_argument_with_spaces_as_one_argument(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """`fast` passes `-m 'not integration'`, which must echo as one thing."""
        run((sys.executable, "-c", "pass", "not integration"))
        assert '"not integration"' in capsys.readouterr().out

    def test_reports_a_missing_command_without_a_traceback(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """`uv` missing from PATH is the likeliest way the first command fails."""
        # subprocess raises rather than returning a status when the executable
        # does not exist, so this used to end in a traceback naming subprocess
        # internals - telling somebody who has not installed uv nothing about
        # what to install.
        #
        # More than one argument, deliberately. With a single-element command
        # the executable is also the last element, so naming command[-1] read
        # exactly the same and mutation testing found the test could not tell
        # them apart. Every real task here looks like ("uv", "run", "pytest"),
        # where the difference is "uv not found" against "pytest not found" -
        # the wrong one of which sends somebody to install the wrong thing.
        status = run(("definitely-not-a-real-command", "an-argument"))
        assert status == COMMAND_NOT_FOUND_STATUS
        assert "definitely-not-a-real-command not found" in capsys.readouterr().err


class TestTheExitStatusesAreTheConventionalOnes:
    """
    Comparing a constant with itself proves nothing about its value.

    Found by mutation testing. Every other test checks a status by
    comparing it with the same constant it came from, so changing 127 to
    128 changed both sides at once and the suite stayed green - a hundred
    per cent covered and completely indifferent to the number. The numbers
    are the whole point: each is what a shell already means by that
    condition, and a script reading our exit status expects exactly it.
    """

    def test_a_usage_error_exits_the_way_argparse_does(self) -> None:
        """A usage error exits 2, which is what argparse itself returns."""
        assert USAGE_ERROR_STATUS == 2

    def test_a_missing_command_exits_the_way_a_shell_reports_one(self) -> None:
        """127 is "command not found" wherever a shell reports it."""
        assert COMMAND_NOT_FOUND_STATUS == 127

    def test_an_interrupt_exits_the_way_a_shell_reports_sigint(self) -> None:
        """128 plus the signal number, and SIGINT is signal 2."""
        assert INTERRUPTED_STATUS == 130


class TestStoppingAndBeingStopped:
    """
    A run that was interrupted, or a tool that was killed, is not a pass.

    Both arrive by a different route from an ordinary non-zero exit, and
    both used to take that route straight past the reporting.
    """

    def test_an_interrupt_stops_without_a_traceback(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Ctrl-C is a deliberate act; a traceback makes it look like a crash."""

        def interrupt(*_args: object, **_kwargs: object) -> None:
            raise KeyboardInterrupt

        monkeypatch.setattr(subprocess, "run", interrupt)
        assert run((sys.executable, "-c", "pass")) == INTERRUPTED_STATUS
        # 130 is what a shell reports for Ctrl-C, so a script wrapping this
        # one can tell an interruption from a gate that genuinely failed.
        assert "interrupted" in capsys.readouterr().err

    def test_an_interrupt_abandons_the_remaining_gates(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Working through the rest of `check` ignores what was just asked."""
        attempted: list[tuple[str, ...]] = []

        def interrupt(command: tuple[str, ...]) -> int:
            attempted.append(command)
            return INTERRUPTED_STATUS

        monkeypatch.setattr(qa, "run", interrupt)
        assert run_task("check") == INTERRUPTED_STATUS
        assert len(attempted) == 1

    def test_a_tool_killed_by_a_signal_is_not_reported_as_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """POSIX reports a killed process as a negative status, not a positive one."""
        # A gate that was killed - by the OOM killer, or a CI timeout - has
        # not passed. Anything comparing against a positive failure, or
        # testing `status > 0`, would call this a green run.
        monkeypatch.setattr(qa, "run", lambda _command: -15)
        assert run_task("check") != 0


class TestEveryArgumentSurvivesBeingEchoed:
    """
    A worked example of a property-based test, kept here to be copied.

    Every test above checks a case somebody thought of: an argument with a
    space in it, a command that is not installed. That is the weakness of
    example-based testing - it only ever covers what was imagined, and the
    bugs that survive are the ones nobody imagined.

    A property states a rule that must hold for EVERY input, and Hypothesis
    goes looking for the input that breaks it, trying a fresh set of shapes
    on every run. When it finds one it shrinks it to the smallest example
    that still fails - so the report names ``["a b"]`` rather than some
    forty-character string - and saves it, so that once found, a failure is
    checked for ever afterwards.

    Write these for rules, not for cases: round trips, things that must not
    change when applied twice, and outputs that must always satisfy some
    invariant whatever went in.
    """

    @given(command=st.lists(ARGUMENTS, min_size=1, max_size=5))
    def test_the_echoed_line_splits_back_into_the_same_arguments(
        self,
        command: list[str],
    ) -> None:
        """What is echoed has to be the command that ran, not a lookalike."""
        # shlex.split is how a shell reads a line back into arguments, so
        # this asks the question that matters: if somebody pasted what we
        # printed, would they run the command we actually ran?
        assert shlex.split(printable(tuple(command))) == command


class TestRunTask:
    """Test :py:func:`run_task`."""

    def test_runs_every_command_when_all_succeed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A passing task works through its whole list, in order."""
        calls: list[tuple[str, ...]] = []

        def succeed(command: tuple[str, ...]) -> int:
            calls.append(command)
            return 0

        monkeypatch.setattr(qa, "run", succeed)
        assert run_task("check") == 0
        assert calls == list(TASKS["check"].commands)

    def test_stops_at_the_first_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Later gates are skipped, so the message that matters stays visible."""
        calls: list[tuple[str, ...]] = []

        def fail(command: tuple[str, ...]) -> int:
            calls.append(command)
            return FAILING_STATUS

        monkeypatch.setattr(qa, "run", fail)
        assert run_task("check") == FAILING_STATUS
        assert calls == [TASKS["check"].commands[0]]


class TestBuildParser:
    """Test the command-line parser."""

    def test_help_lists_every_task(self) -> None:
        """A task nobody can discover may as well not exist."""
        text = build_parser().format_help()
        assert all(name in text for name in TASKS)

    def test_rejects_an_unknown_task(self, capsys: pytest.CaptureFixture[str]) -> None:
        """A mistyped task is an error, not a silent no-op."""
        with pytest.raises(SystemExit):
            build_parser().parse_args(["not-a-task"])
        assert "not-a-task" in capsys.readouterr().err


class TestMain:
    """Test the :py:func:`main` entry point."""

    def test_exits_with_the_task_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The process status is the task's status, so CI and hooks can react."""
        monkeypatch.setattr(sys, "argv", ["qa.py", "lint"])
        monkeypatch.setattr(qa, "run", lambda _command: FAILING_STATUS)
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == FAILING_STATUS

    def test_names_the_tasks_when_none_is_given(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A bare invocation answers with the task list, not a bare usage line."""
        monkeypatch.setattr(sys, "argv", ["qa.py"])
        with pytest.raises(SystemExit) as exc_info:
            main()
        # Read the captured output once: readouterr() drains the buffer, so
        # calling it per name would compare every name after the first
        # against an empty string.
        error_output = capsys.readouterr().err
        assert all(name in error_output for name in TASKS)
        # Non-zero: a hook or CI line that lost its argument must not pass by
        # having run no gate at all.
        assert exc_info.value.code == USAGE_ERROR_STATUS

    def test_naming_no_task_runs_no_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Listing the tasks must not also execute one."""
        calls: list[tuple[str, ...]] = []

        def record(command: tuple[str, ...]) -> int:
            calls.append(command)
            return 0

        monkeypatch.setattr(sys, "argv", ["qa.py"])
        monkeypatch.setattr(qa, "run", record)
        with pytest.raises(SystemExit):
            main()
        assert not calls
