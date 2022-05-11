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

import subprocess  # nosec B404
import sys

import pytest

from basics.cli import Cli


class TestCli:
    def test_bootstrap_run(self):
        with pytest.raises(SystemExit) as cm:
            # simulate argument from command line
            sys.argv.append("ARGUMENT1")
            Cli().bootstrap().run(output=False)
        assert cm.match("0")

    def test_cli(self):
        # Test ONE ARGUMENT, ZERO OPTIONS
        result = subprocess.run(  # nosec B603, B607
            ["pipenv", "run", "python", "app_cli.py", "ARGUMENT1"],
            capture_output=True,
        )
        assert result.returncode == 0
        output_expected = (
            b"\nBasics QA Python 0.0.0"
            b"\n\noption1 None | argument1: ARGUMENT1"
            b"\n\nDescription: for anything required..."
            b"\n\nARGUMENT1\n"
        )
        assert result.stdout == output_expected
        # Test ONE ARGUMENT, ONE OPTION
        result = subprocess.run(  # nosec B603, B607
            ["pipenv", "run", "python", "app_cli.py", "-o", "OPTION1", "ARGUMENT1"],
            capture_output=True,
        )
        assert result.returncode == 0
        output_expected = (
            b"\nBasics QA Python 0.0.0"
            b"\n\noption1 OPTION1 | argument1: ARGUMENT1"
            b"\n\nDescription: for anything required..."
            b"\n\nARGUMENT1\n"
        )
        assert result.stdout == output_expected
        # Test ONE ARGUMENT, ONE OPTION, ONE VERBOSE
        result = subprocess.run(  # nosec B603, B607
            [
                "pipenv",
                "run",
                "python",
                "app_cli.py",
                "-o",
                "OPTION1",
                "ARGUMENT1",
                "-v",
            ],
            capture_output=True,
        )
        assert result.returncode == 0
        output_expected = (
            b"\nBasics QA Python 0.0.0"
            b"\n\noption1 OPTION1 | argument1: ARGUMENT1"
            b"\n\nDescription: for anything required..."
            b"\n\nARGUMENT1\n"
        )
        assert result.stdout == output_expected
        # Test ONE ARGUMENT, ONE OPTION, TWO VERBOSE
        result = subprocess.run(  # nosec B603, B607
            [
                "pipenv",
                "run",
                "python",
                "app_cli.py",
                "-o",
                "OPTION1",
                "ARGUMENT1",
                "-vv",
            ],
            capture_output=True,
        )
        assert result.returncode == 0
        output_expected = (
            b"\nBasics QA Python 0.0.0"
            b"\n\noption1 OPTION1 | argument1: ARGUMENT1"
            b"\n\nDescription: for anything required..."
            b"\n\nARGUMENT1\n"
        )
        assert result.stdout == output_expected


if __name__ == "__main__":
    pytest.main()
