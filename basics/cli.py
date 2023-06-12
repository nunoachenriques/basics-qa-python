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

Command-line interface.
"""

import argparse
import logging
from pathlib import Path
from typing import NoReturn

# Enable logging.
logger = logging.getLogger(__name__)


class Cli:
    """
    Provide bootstrap and complete command-line integration.

    The application may run as a command-line Python script by making use of
    this class integration. See a ready-made example in ``app_cli.py``.
    """

    def __init__(self: "Cli") -> None:
        """
        Initialise the class parameters:

            * self.option1: args option1 placeholder.
            * self.argument1: args argument1 placeholder.
            * self.version: semantic version from VERSION file.
        """
        self.option1 = None
        self.argument1 = None
        with Path.open(Path("VERSION")) as f:
            self.version = f.read()

    def bootstrap(self: "Cli") -> "Cli":
        """
        Protect the start-up and help the user.

        Moreover, parse the command-line arguments to obtain options and
        argument values. Set the logging level regarding verbosity requested.

        :return: This instance with self.option1 = args.o and
            self.argument1 = args.argument1
        """
        cmd_line_parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        cmd_line_parser.description = (
            f"Basics on Quality Assurance in Python {self.version}"
            "\n\nhttps://github.com/nunoachenriques/basics-qa-python"
        )
        cmd_line_parser.add_argument(
            "-v",
            action="count",
            default=0,
            help="Output verbosity: none, info (-v), debug (-vv).",
        )
        cmd_line_parser.add_argument(
            "-o",
            metavar="OPTION1",
            type=str,
            help="The option1 help description.",
        )
        cmd_line_parser.add_argument("argument1", type=str, help="The argument1 help description.")
        cmd_line_parser.epilog = (
            "Usage examples:"
            "\n\n  Demonstration of the usage examples with verbose and argument:"
            "\n    pipenv run python app_cli.py -v argument1"
            "\n\n  Demonstration of the usage examples with option and argument:"
            "\n    pipenv run python app_cli.py -o option1 argument1"
        )
        args = cmd_line_parser.parse_args()
        if args.v == 0:
            logger.setLevel(logging.CRITICAL)
        elif args.v == 1:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.DEBUG)
        # Set logging format with more information (function name) if DEBUG mode.
        if logger.level == logging.DEBUG:
            # noinspection SpellCheckingInspection
            logger_format = "%(asctime)s | %(name)s | %(funcName)s | %(levelname)s | %(message)s"
        else:
            # noinspection SpellCheckingInspection
            logger_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        logging.basicConfig(format=logger_format, force=True)
        logger.info("Logging set to %s", logging.getLevelName(logger.level))
        self.option1 = args.o
        self.argument1 = args.argument1
        return self

    def run(self: "Cli") -> NoReturn:
        """Run the application."""
        logger.info(
            "Basics QA Python %s | option1: %s | argument1: %s | Started",
            self.version,
            self.option1,
            self.argument1,
        )
        # Add code to run your application below this line and before the SystemExit.
        raise SystemExit(0)
