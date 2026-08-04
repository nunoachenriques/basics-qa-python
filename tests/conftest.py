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

Shared test fixtures.
"""

import logging
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _restore_logging_state() -> Iterator[None]:
    """
    Undo the global logging changes a command-line entry point makes.

    ``logging.basicConfig(..., force=True)`` closes the root handlers and
    installs a new one bound to whatever ``sys.stderr`` is at that moment -
    under pytest, the current test's capture buffer. Any later test that
    logs then writes to a stream pytest has since closed, and
    ``logging.Handler.handleError`` prints "--- Logging error ---" and
    swallows the exception. The suite stays green while genuinely failing
    to log, and ``filterwarnings = ["error"]`` cannot catch it because it
    is not a warning.

    Entry points also leave their logger at INFO or DEBUG, so a verbosity
    chosen by one test silently applied to every test that ran after it.

    :yield: Control to the test, with logging restored afterwards.
    """
    root = logging.getLogger()
    handlers = root.handlers[:]
    root_level = root.level
    levels = {
        name: logger.level
        for name, logger in logging.root.manager.loggerDict.items()
        if isinstance(logger, logging.Logger)
    }
    yield
    root.handlers[:] = handlers
    root.setLevel(root_level)
    # Walk what exists now rather than only what existed before. A logger
    # created during the test - `getLogger(__package__)` promoting a
    # placeholder into a real logger, for one - is absent from the snapshot,
    # so restoring the snapshot alone would leave its level set for every
    # test that follows. Anything unrecognised goes back to NOTSET, which is
    # what a freshly created logger has.
    for name, logger in list(logging.root.manager.loggerDict.items()):
        if isinstance(logger, logging.Logger):
            logger.setLevel(levels.get(name, logging.NOTSET))
