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

Command-line interface.
"""

import argparse
import logging
from typing import NoReturn

from basics import __version__

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
        Initialise the class parameters.

            * self.option1: args option1 placeholder.
            * self.argument1: args argument1 placeholder.
            * self.version: the installed distribution version.
        """
        self.option1: str | None = None  # -o is optional
        self.argument1: str = ""  # positional, always set once bootstrap() runs
        self.version: str = __version__

    def bootstrap(self: "Cli") -> "Cli":
        """
        Protect the start-up and help the user.

        Moreover, parse the command-line arguments to obtain options and
        argument values. Set the logging level regarding verbosity requested.

        :return: This instance with self.option1 = args.o and
            self.argument1 = args.argument1
        """
        cmd_line_parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        # One short statement, not a string split across two lines. Renaming
        # shortens the title, and an implicit concatenation that then fits on
        # one line gets joined by the formatter - so a generated project
        # failed its own `ruff format --check` before anyone had touched it.
        # The project URL lived here too, and renaming could not fix it: every
        # generated project advertised this template's repository as its own.
        cmd_line_parser.description = f"Basics on Quality Assurance in Python {self.version}"
        cmd_line_parser.add_argument(
            "--version",
            action="version",
            version=self.version,
            help="Show the version and exit.",
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
        # %(prog)s, not a hardcoded path: argparse expands it to however the
        # program was actually started. Installed users see `basics-qa`, and
        # app_cli.py is not in the wheel for them to run.
        cmd_line_parser.epilog = (
            "Usage examples:"
            "\n\n  With verbosity and an argument:"
            "\n    %(prog)s -v argument1"
            "\n\n  With an option and an argument:"
            "\n    %(prog)s -o option1 argument1"
        )
        args = cmd_line_parser.parse_args()
        # WARNING, not CRITICAL. At CRITICAL an application built on this
        # skeleton loses its own logger.warning() and logger.error() calls
        # unless the user happens to pass -v, which is the one situation
        # where a message most needs to be seen. Nothing here logs below
        # INFO, so the default run stays silent either way.
        if args.v == 0:
            level = logging.WARNING
        elif args.v == 1:
            level = logging.INFO
        else:
            level = logging.DEBUG
        # Set the level on the PACKAGE logger, not this module's own. Every
        # other module in the package inherits from it, so their records
        # honour -v too. Setting it on `logger` alone silently mutes every
        # sibling module, which only becomes visible once the package has
        # more than one.
        logging.getLogger(__package__).setLevel(level)
        # Set logging format with more information (function name) if DEBUG mode.
        if level == logging.DEBUG:
            # noinspection SpellCheckingInspection
            logger_format = "%(asctime)s | %(name)s | %(funcName)s | %(levelname)s | %(message)s"
        else:
            # noinspection SpellCheckingInspection
            logger_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        logging.basicConfig(format=logger_format, force=True)
        logger.info("Logging set to %s", logging.getLevelName(level))
        self.option1 = args.o
        self.argument1 = args.argument1
        return self

    def run(self: "Cli") -> NoReturn:
        """Run the application."""
        logger.info(
            "Basics on Quality Assurance in Python %s | option1: %s | argument1: %s | Started",
            self.version,
            self.option1,
            self.argument1,
        )
        # Add code to run your application below this line and before the SystemExit.
        raise SystemExit(0)


def main() -> NoReturn:
    """
    Provide the console-script entry point declared in ``pyproject.toml``.

    Installing the project exposes this as the ``basics-qa`` command.
    """
    Cli().bootstrap().run()
