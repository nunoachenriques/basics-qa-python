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
Basics on Quality Assurance in Python

Test ``cli`` module.
This is an integration test.
"""

import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import pytest

from basics.cli import Cli

with Path.open(Path("VERSION")) as f:
    VERSION = f.read()


def _test_cli(
    args: list[str],
    code_expected: int,
    output_expected: list[str],
) -> NoReturn | None:
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
    result = subprocess.run(
        args,  # noqa: S603
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != code_expected:
        msg = f"The return code ({result.returncode}) is not the expected ({code_expected})!"
        raise ValueError(msg)
    for result_stdout_line, output_expected_line in zip(
        result.stdout.splitlines(),
        output_expected,
        strict=True,
    ):
        result_line = result_stdout_line.split("|", maxsplit=2)[-1]
        if result_line != output_expected_line:
            msg = f"The result line ({result_line}) is not the expected ({output_expected_line})!"
            raise ValueError(msg)
    return None


class TestCli:
    """Test the py:mod:`cli` module."""

    def test_bootstrap_run(self: "TestCli") -> NoReturn | None:
        """Test the Cli.bootstrap.run sequence with one argument."""
        # simulate argument from command line
        sys.argv.append("ARGUMENT1")
        with pytest.raises(SystemExit) as cm:
            Cli().bootstrap().run()
        if not cm.match("0"):
            msg = "Zero (0) value expected!"
            raise ValueError(msg)
        return None

    def test_cli(self: "TestCli") -> NoReturn | None:
        """Test the command-line interface with various arguments and options."""
        code_expected = 0
        output_expected: list[str] = []
        # Test ONE ARGUMENT, ZERO OPTIONS
        _test_cli(
            ["pipenv", "run", "python", "app_cli.py", "ARGUMENT1"],
            code_expected,
            output_expected,
        )
        # Test ONE ARGUMENT, ONE OPTION
        _test_cli(
            ["pipenv", "run", "python", "app_cli.py", "-o", "OPTION1", "ARGUMENT1"],
            code_expected,
            output_expected,
        )
        # Test ONE ARGUMENT, ONE OPTION, ONE VERBOSE
        output_expected = [
            " INFO | Logging set to INFO",
            f" INFO | Basics QA Python {VERSION} | option1: OPTION1 | argument1: ARGUMENT1 | Started",  # noqa: E501
        ]
        _test_cli(
            ["pipenv", "run", "python", "app_cli.py", "-o", "OPTION1", "ARGUMENT1", "-v"],
            code_expected,
            output_expected,
        )
        # Test ONE ARGUMENT, ONE OPTION, TWO VERBOSE
        output_expected = [
            " bootstrap | INFO | Logging set to DEBUG",
            f" run | INFO | Basics QA Python {VERSION} | option1: OPTION1 | argument1: ARGUMENT1 | Started",  # noqa: E501
        ]
        _test_cli(
            ["pipenv", "run", "python", "app_cli.py", "-o", "OPTION1", "ARGUMENT1", "-vv"],
            code_expected,
            output_expected,
        )
        return None


if __name__ == "__main__":
    pytest.main()
