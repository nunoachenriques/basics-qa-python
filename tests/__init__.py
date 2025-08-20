"""Deliver the code required to test the application."""

import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("basics-qa-python")
except PackageNotFoundError:
    # package is not installed
    with Path.open(Path(__file__).parent.parent.joinpath("pyproject.toml"), "rb") as f:
        __version__ = tomllib.load(f)["project"]["version"]
