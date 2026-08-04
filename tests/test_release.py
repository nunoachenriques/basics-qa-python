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

Check the repository is consistent with itself.

Nothing here tests behaviour. These are the facts that have to agree
across files nobody edits together: the version, the changelog, what the
wheel contains. Each of them drifts silently, and each is found at the
worst possible moment - during a release.
"""

import os
import re
import subprocess
import sys
import tomllib
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from basics import __version__

#: The repository root, two levels up from this file.
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

#: Directories holding generated state rather than source. Listed here
#: rather than imported from ``new_project.py``, which a generated project
#: deliberately does not ship.
GENERATED_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        ".hypothesis",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".uv-cache",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
    },
)

#: No source file has any business being this large. A stray coverage
#: database, a built wheel, or a captured log is how one arrives, and each
#: is invisible in review while making every clone slower for ever.
LARGEST_SENSIBLE_FILE = 1_000_000


def read_pyproject() -> dict[str, object]:
    """
    Parse ``pyproject.toml``.

    :return: The parsed document.
    """
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as file:
        return tomllib.load(file)


def project_table() -> dict[str, object]:
    """
    Return the ``[project]`` table.

    :return: The table, which every packaged project has.
    """
    project = read_pyproject()["project"]
    assert isinstance(project, dict)
    return project


def source_files() -> Iterator[Path]:
    """
    Walk every file that is part of the source, skipping generated state.

    :yield: Each source file.
    """
    # os.walk, pruning as it descends, rather than rglob filtered afterwards.
    # rglob visits every directory before anything can reject it, so it walks
    # the whole of .venv - which is slow, and on Windows fails outright the
    # moment a vendored dependency in there sits past the 260-character path
    # limit. That is not hypothetical: it happens in any checkout more than a
    # few directories deep.
    for directory, subdirectories, names in os.walk(REPOSITORY_ROOT):
        subdirectories[:] = [name for name in subdirectories if name not in GENERATED_DIRECTORIES]
        for name in names:
            yield Path(directory) / name


class TestTheVersionAgreesWithItself:
    """One version, recorded in three files that are never edited together."""

    def test_the_package_reports_what_pyproject_declares(self) -> None:
        """``--version`` reads the installed metadata, which is built from this."""
        assert __version__ == project_table()["version"]

    def test_the_lock_file_records_the_same_version(self) -> None:
        """A lock that disagrees makes ``uv sync --locked`` refuse to install."""
        # This is not hypothetical: generated projects shipped a lock still
        # claiming the template's version, and the first documented command
        # failed on its first line.
        name = project_table()["name"]
        assert isinstance(name, str)
        lock = (REPOSITORY_ROOT / "uv.lock").read_text(encoding="utf-8")
        entry = re.search(rf'name = "{re.escape(name)}"\r?\nversion = "([^"]+)"', lock)
        assert entry is not None, f"the lock file has no entry for {name}"
        assert entry.group(1) == __version__

    def test_the_changelog_is_ready_to_receive_a_change(self) -> None:
        """Without a section to write into, notable changes go unrecorded."""
        changelog = (REPOSITORY_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "## [Unreleased]" in changelog


class TestNothingUnwantedIsCommitted:
    """The repository is cloned far more often than it is written to."""

    def test_no_source_file_is_unexpectedly_large(self) -> None:
        """A committed coverage database or wheel slows every clone for ever."""
        oversized = {
            str(path.relative_to(REPOSITORY_ROOT)): path.stat().st_size
            for path in source_files()
            if path.stat().st_size > LARGEST_SENSIBLE_FILE
        }
        assert not oversized, f"unexpectedly large files: {oversized}"

    def test_no_environment_file_is_committed(self) -> None:
        """`.env` holds secrets, and `.gitignore` only helps before the first add."""
        assert not list(REPOSITORY_ROOT.glob(".env")), ".env must never be committed"


class TestTheWheelContainsTheRightThings:
    """An editable install resolves from the source tree and hides every fault."""

    @staticmethod
    @pytest.fixture(scope="class")
    def manifest(tmp_path_factory: pytest.TempPathFactory) -> list[str]:
        """
        Build a wheel and list what is inside it.

        :param tmp_path_factory: The fixture the wheel is built into.
        :return: Every path the wheel contains.
        """
        output = tmp_path_factory.mktemp("wheel")
        result = subprocess.run(  # noqa: S603
            ["uv", "build", "--wheel", "--out-dir", str(output)],  # noqa: S607
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        built = list(output.glob("*.whl"))
        assert len(built) == 1, f"expected one wheel, got {built}"
        with zipfile.ZipFile(built[0]) as wheel:
            return wheel.namelist()

    @pytest.mark.integration
    def test_it_ships_the_typing_marker(self, manifest: list[str]) -> None:
        """Without py.typed, type checkers ignore the annotations entirely."""
        assert any(name.endswith("/py.typed") for name in manifest), manifest

    @pytest.mark.integration
    def test_it_ships_the_command_line_module(self, manifest: list[str]) -> None:
        """A module left out of the wheel is invisible until somebody installs it."""
        assert any(name.endswith("/cli.py") for name in manifest), manifest

    @pytest.mark.integration
    def test_it_does_not_ship_the_tests(self, manifest: list[str]) -> None:
        """Tests in a wheel are dead weight installed into everybody's environment."""
        # A top-level `tests` in a wheel is worse than dead weight: it claims
        # the import name `tests` in the installing environment, where it then
        # shadows anybody else's.
        assert not [name for name in manifest if name.startswith("tests/")], manifest

    @pytest.mark.integration
    def test_it_does_not_ship_the_developer_scripts(self, manifest: list[str]) -> None:
        """`qa.py` and `app_cli.py` are for the repository, not for consumers."""
        unwanted = {"qa.py", "app_cli.py", "new_project.py"}
        assert not unwanted.intersection(manifest), manifest


class TestTheDeclaredInterpretersAreReal:
    """`requires-python` is a promise made on PyPI to people who never test it."""

    def test_every_classifier_version_is_allowed_by_requires_python(self) -> None:
        """A classifier for a version the project refuses to install on is a lie."""
        project = project_table()
        requires = project["requires-python"]
        assert isinstance(requires, str)
        classifiers = project["classifiers"]
        assert isinstance(classifiers, list)
        minimum = tuple(int(part) for part in requires.removeprefix(">=").split("."))
        declared = [
            tuple(int(part) for part in line.rsplit(" :: ", maxsplit=1)[-1].split("."))
            for line in classifiers
            if line.startswith("Programming Language :: Python :: 3.")
        ]
        assert declared, "no interpreter version is declared in the classifiers"
        assert all(version >= minimum for version in declared), declared

    def test_the_pinned_interpreter_is_one_of_the_declared_ones(self) -> None:
        """`.python-version` decides what everybody gets by default."""
        pinned = (REPOSITORY_ROOT / ".python-version").read_text(encoding="utf-8").strip()
        classifiers = project_table()["classifiers"]
        assert isinstance(classifiers, list)
        assert any(line.endswith(f":: {pinned}") for line in classifiers), pinned

    def test_the_running_interpreter_satisfies_the_declared_minimum(self) -> None:
        """The suite must never pass on an interpreter the project rules out."""
        requires = project_table()["requires-python"]
        assert isinstance(requires, str)
        minimum = tuple(int(part) for part in requires.removeprefix(">=").split("."))
        assert sys.version_info[: len(minimum)] >= minimum
