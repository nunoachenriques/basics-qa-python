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

from tqdm.auto import tqdm


class Cli(object):
    """
    Provides bootstrap and complete integration of application run from
    command-line a Python script, such as:

        from basics.cli import Cli

        if __name__ == "__main__":
            Cli().bootstrap().run()
    """

    def __init__(self):
        """
        Initialisation of the class parameters:

            * self.option1: args option1 placeholder.
            * self.argument1: args argument1 placeholder.
            * self.version: semantic version in VERSION file.
        """
        self.option1 = None
        self.argument1 = None
        with open("VERSION") as f:
            self.version = f.read()

    def bootstrap(self) -> "Cli":
        """
        Required to protect the start-up and help the user. Parse the
        command-line arguments to obtain options and argument values. Set the
        logging level regarding verbosity requested.

        :return: This instance with self.option1 = args.o and
            self.argument1 = args.argument1
        """
        # noinspection PyTypeChecker
        cmd_line_parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter
        )
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
            "-o", metavar="OPTION1", type=str, help="The option1 help description."
        )
        cmd_line_parser.add_argument(
            "argument1", type=str, help="The argument1 help description."
        )
        cmd_line_parser.epilog = (
            "Usage examples:"
            "\n\n  Demonstration of the usage examples with verbose and argument:"
            "\n    pipenv run python app_cli.py -v argument1"
            "\n\n  Demonstration of the usage examples with option and argument:"
            "\n    pipenv run python app_cli.py -o option1 argument1"
        )
        args = cmd_line_parser.parse_args()
        if args.v == 0:
            logging.getLogger().setLevel(logging.CRITICAL)
        elif args.v == 1:
            logging.getLogger().setLevel(logging.INFO)
        else:
            logging.getLogger().setLevel(logging.DEBUG)
        logging.debug(
            f"Logging set to {logging.getLevelName(logging.getLogger().level)}"
        )
        self.option1 = args.o
        self.argument1 = args.argument1
        return self

    def run(self, output: bool = True):
        """
        Run the application, place here the description of options and
        arguments effects and add examples (e.g., -o option1).

        :param output: True for result output.
        """
        with tqdm(
            total=1, disable=(logging.getLogger().level >= logging.CRITICAL)
        ) as bar:
            bar.set_description_str("Basics QA Python")
            bar.set_postfix_str("Getting and parsing option1...")
            dummy = self.option1
            bar.set_postfix_str(dummy)
            bar.update()
            bar.set_postfix_str("")
        if output:
            result: str = ""
            if self.argument1 is not None:
                result = self.argument1
            print(
                f"\nBasics QA Python {self.version}"
                f"\n\noption1 {self.option1} | argument1: {self.argument1}"
                "\n\nDescription: for anything required..."
                f"\n\n{result}"
            )
        raise SystemExit(0)
