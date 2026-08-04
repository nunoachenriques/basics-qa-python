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

import sys

import pytest

import qa
from qa import (
    COMMAND_NOT_FOUND_STATUS,
    TASKS,
    USAGE_ERROR_STATUS,
    build_parser,
    main,
    run,
    run_task,
)

#: An arbitrary non-zero status, distinguishable from a real tool's exit code.
FAILING_STATUS = 3


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
        status = run(("definitely-not-a-real-command",))
        assert status == COMMAND_NOT_FOUND_STATUS
        assert "not found" in capsys.readouterr().err


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
