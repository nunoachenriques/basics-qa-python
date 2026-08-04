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

Test ``cli`` module.
This is an integration test.
"""

import logging
import subprocess
import sys

import pytest

from basics import __version__
from basics.cli import Cli, main

#: Both imports above come from the project package, so renaming the project
#: moves them together and the block stays sorted whatever the new name is.
#: Importing the version from ``tests`` instead put a second top-level name
#: in the block, and a package renamed to anything after "tests" in the
#: alphabet then left a generated project failing its own import-order gate.

#: Held in names rather than repeated inline. Spelled out in full twice, the
#: expected log line runs past the line-length limit and needs a suppression
#: comment, which a shorter project name then makes unused - itself a lint
#: error. The generated project failed one way or the other; kept short, the
#: line fits whatever the project is called.
TITLE = "Basics on Quality Assurance in Python"
STARTED = "| option1: OPTION1 | argument1: ARGUMENT1 | Started"


def _test_cli(
    args: list[str],
    code_expected: int,
    output_expected: list[str],
) -> None:
    """
    Help the ``TestCli.test_cli`` method.

    Actually, this is the testing workload called by ``TestCli.test_cli``.
    Process the ``stdout`` (``stderr`` is redirected to ``stdout``) result
    to strip off the logging prefix of timestamp and module name.
    Result output before stripping::

     2023-06-12 11:55:14,448 | basics.cli | INFO | Logging set to INFO

    After stripping::

      INFO | Logging set to INFO

    :param args: The arguments composing the command-line to run the application.
    :param code_expected: The exit code of the process.
    :param output_expected: The standard output to the console.
    """
    result = subprocess.run(  # noqa: S603
        args,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == code_expected, (
        f"The return code ({result.returncode}) is not the expected ({code_expected})!"
    )
    for result_stdout_line, output_expected_line in zip(
        result.stdout.splitlines(),
        output_expected,
        strict=True,
    ):
        result_line = result_stdout_line.split("|", maxsplit=2)[-1]
        assert result_line == output_expected_line, (
            f"The result line ({result_line}) is not the expected ({output_expected_line})!"
        )


class TestCli:
    """Test the py:mod:`cli` module."""

    def test_bootstrap_run(
        self: "TestCli",
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test the Cli.bootstrap.run sequence with one argument."""
        monkeypatch.setattr(sys, "argv", ["app_cli.py", "ARGUMENT1"])
        with pytest.raises(SystemExit) as cm:
            Cli().bootstrap().run()
        # cm.value.code, not cm.match("0"): match is a regex search over the
        # string form, so it also passes for 10, 20, and 100.
        assert cm.value.code == 0

    def test_version_flag_exits_zero(
        self: "TestCli",
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """--version prints the version and exits successfully."""
        monkeypatch.setattr(sys, "argv", ["app_cli.py", "--version"])
        with pytest.raises(SystemExit) as cm:
            Cli().bootstrap()
        assert cm.value.code == 0
        assert __version__ in capsys.readouterr().out

    def test_help_names_the_running_program_not_a_file(
        self: "TestCli",
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The usage examples used to name app_cli.py, which no wheel ships."""
        monkeypatch.setattr(sys, "argv", ["basics-qa", "--help"])
        with pytest.raises(SystemExit) as cm:
            Cli().bootstrap()
        assert cm.value.code == 0
        printed = capsys.readouterr().out
        assert "app_cli.py" not in printed
        assert "basics-qa -v argument1" in printed

    def test_version_prints_the_version_and_nothing_else(
        self: "TestCli",
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Anything else printed alongside it breaks whoever parses the output."""
        # `--version` is what a script or a package manager reads to find out
        # what is installed, so a friendly prefix would be a breaking change.
        monkeypatch.setattr(sys, "argv", ["app_cli.py", "--version"])
        with pytest.raises(SystemExit):
            Cli().bootstrap()
        assert capsys.readouterr().out == f"{__version__}\n"

    def test_a_third_v_is_still_debug(
        self: "TestCli",
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """`-vvv` is what people type when they want more; it must not fall over."""
        monkeypatch.setattr(sys, "argv", ["app_cli.py", "ARGUMENT1", "-vvv"])
        Cli().bootstrap()
        # The package logger, which is where bootstrap sets the level, derived
        # from the class rather than named, so that renaming cannot miss it.
        assert logging.getLogger(Cli.__module__.partition(".")[0]).level == logging.DEBUG

    def test_a_double_dash_allows_an_argument_that_looks_like_an_option(
        self: "TestCli",
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Without `--`, argparse reads a leading dash as a flag it does not have."""
        monkeypatch.setattr(sys, "argv", ["app_cli.py", "--", "-x"])
        assert Cli().bootstrap().argument1 == "-x"

    def test_main_entry_point(
        self: "TestCli",
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The console-script entry point runs the same sequence."""
        monkeypatch.setattr(sys, "argv", ["basics-qa", "ARGUMENT1"])
        with pytest.raises(SystemExit) as cm:
            main()
        assert cm.value.code == 0

    @pytest.mark.integration
    def test_cli(self: "TestCli") -> None:
        """Test the command-line interface with various arguments and options."""
        code_expected = 0
        output_expected: list[str] = []
        # Test ONE ARGUMENT, ZERO OPTIONS
        _test_cli(
            [sys.executable, "app_cli.py", "ARGUMENT1"],
            code_expected,
            output_expected,
        )
        # Test ONE ARGUMENT, ONE OPTION
        _test_cli(
            [sys.executable, "app_cli.py", "-o", "OPTION1", "ARGUMENT1"],
            code_expected,
            output_expected,
        )
        # Test ONE ARGUMENT, ONE OPTION, ONE VERBOSE
        output_expected = [
            " INFO | Logging set to INFO",
            f" INFO | {TITLE} {__version__} {STARTED}",
        ]
        _test_cli(
            [sys.executable, "app_cli.py", "-o", "OPTION1", "ARGUMENT1", "-v"],
            code_expected,
            output_expected,
        )
        # Test ONE ARGUMENT, ONE OPTION, TWO VERBOSE
        output_expected = [
            " bootstrap | INFO | Logging set to DEBUG",
            f" run | INFO | {TITLE} {__version__} {STARTED}",
        ]
        _test_cli(
            [sys.executable, "app_cli.py", "-o", "OPTION1", "ARGUMENT1", "-vv"],
            code_expected,
            output_expected,
        )


if __name__ == "__main__":
    pytest.main()
