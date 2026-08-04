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

Walk the whole path, with real Git, in a real clone.

Every other test about the hooks reads the task table or the configuration
file and checks what they SAY. None of them ever installed a hook, made a
commit, or pushed - so nothing here proved that a badly formatted commit is
actually refused, or that the pre-push stage exists at all outside of a
line in a YAML file. Those are the gates this project is for.

Slow, and unavoidably so: it clones the repository, builds an environment,
and lets Git run the hooks for real. Marked ``integration`` accordingly, so
``qa.py fast`` leaves it out.

Not copied into generated projects: it clones the template and drives the
template's own onboarding.
"""

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

#: Set in the environment handed to Git. The pre-push hook runs this very
#: suite, which would otherwise start another journey inside this one, and
#: another inside that. The tests below skip when they find it.
NESTED_RUN = "QA_JOURNEY_RUNNING"

#: A module ruff will reject: no docstring, no spaces around the operator.
BADLY_FORMATTED = "x=1\n"

#: A module ruff and mypy both accept, and which no test covers - so it
#: passes the commit stage and fails the coverage gate on push. Built from
#: pieces rather than written as one block, because a docstring inside a
#: docstring is not something Python will parse.
WELL_FORMATTED_BUT_UNTESTED = (
    '"""A module nothing tests."""\n'
    "\n"
    "\n"
    "def unused() -> int:\n"
    '    """\n'
    "    Return a number.\n"
    "\n"
    "    :return: The number.\n"
    '    """\n'
    "    return 1\n"
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get(NESTED_RUN) == "1",
        reason="already inside a journey; the hooks are running this suite",
    ),
]


def child_environment() -> dict[str, str]:
    """
    Build the environment for a Git command that will run the hooks.

    :return: The environment, marked as nested and free of coverage hooks.
    """
    environment = {
        name: value for name, value in os.environ.items() if not name.startswith("COV_CORE")
    }
    # COV_CORE_* is stripped for the same reason the generated-project gates
    # strip it: pytest-cov hooks every subprocess it can reach, and the
    # nested run would report this project's files and drag the total down.
    environment[NESTED_RUN] = "1"
    return environment


def git(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """
    Run one Git command, letting any hook it triggers run for real.

    :param arguments: The Git subcommand and its arguments.
    :param cwd: The repository to run it in.
    :return: The finished process, never raising on a non-zero status.
    """
    return subprocess.run(  # noqa: S603
        ["git", *arguments],  # noqa: S607
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        env=child_environment(),
    )


class TestTheJourneyFromCloneToPush:
    """What somebody actually does, in the order they actually do it."""

    @staticmethod
    @pytest.fixture(scope="class")
    def clone(tmp_path_factory: pytest.TempPathFactory) -> Path:
        """
        Clone the repository and run the one documented setup command.

        A clone rather than a copy, deliberately: it carries the committed
        state and nothing else, which is what a new contributor receives,
        and it applies ``.gitattributes`` on the way out.

        :param tmp_path_factory: The fixture the clone is made under.
        :return: The prepared clone.
        """
        destination = tmp_path_factory.mktemp("journey") / "clone"
        cloned = subprocess.run(  # noqa: S603
            ["git", "clone", "--quiet", str(TEMPLATE_ROOT), str(destination)],  # noqa: S607
            check=False,
            capture_output=True,
            text=True,
        )
        assert cloned.returncode == 0, cloned.stderr
        # An identity, because a continuous integration runner has none and
        # every commit below would fail for a reason that is not the point.
        git("config", "user.email", "journey@example.com", cwd=destination)
        git("config", "user.name", "Journey", cwd=destination)
        setup = subprocess.run(
            ["uv", "run", "python", "qa.py", "setup"],  # noqa: S607
            cwd=destination,
            check=False,
            capture_output=True,
            text=True,
            env=child_environment(),
        )
        assert setup.returncode == 0, setup.stdout + setup.stderr
        return destination

    @staticmethod
    @pytest.fixture(autouse=True)
    def _restore(clone: Path) -> Iterator[None]:
        """
        Put the clone back as it was, so these tests may run in any order.

        :param clone: The shared clone.
        :yield: Control to the test.
        """
        starting_point = git("rev-parse", "HEAD", cwd=clone).stdout.strip()
        yield
        git("reset", "--hard", "--quiet", starting_point, cwd=clone)
        git("clean", "-qfd", cwd=clone)

    def test_setup_installs_both_hook_stages_as_real_files(self, clone: Path) -> None:
        """Git does not clone .git/hooks, so a fresh checkout starts with none."""
        for stage in ("pre-commit", "pre-push"):
            hook = clone / ".git" / "hooks" / stage
            assert hook.is_file(), f"{stage} was never installed"
            # Not merely present: pre-commit's own hook script, rather than
            # a leftover sample Git ships with every repository.
            assert "pre-commit" in hook.read_text(encoding="utf-8")

    def test_a_badly_formatted_commit_is_refused(self, clone: Path) -> None:
        """The commit stage is what stops unformatted code reaching the branch."""
        (clone / "bad_style.py").write_text(BADLY_FORMATTED, encoding="utf-8")
        git("add", "bad_style.py", cwd=clone)
        committed = git("commit", "-m", "this must not land", cwd=clone)
        assert committed.returncode != 0, "the hook let a lint violation through"
        assert "ruff" in committed.stdout + committed.stderr

    def test_a_clean_commit_is_accepted(self, clone: Path) -> None:
        """A gate that refuses everything teaches people to pass --no-verify."""
        (clone / "clean_module.py").write_text(WELL_FORMATTED_BUT_UNTESTED, encoding="utf-8")
        git("add", "clean_module.py", cwd=clone)
        committed = git("commit", "-m", "this should land", cwd=clone)
        assert committed.returncode == 0, committed.stdout + committed.stderr

    def test_a_push_failing_the_gates_is_refused(self, clone: Path, tmp_path: Path) -> None:
        """Nothing had ever exercised the push stage, only the line declaring it."""
        # The module committed here is formatted and typed, so it passes the
        # commit stage, and untested, so it drops coverage below the gate.
        # That is the shape of the mistake this stage exists to catch: work
        # that looks fine file by file and breaks the build once pushed.
        (clone / "clean_module.py").write_text(WELL_FORMATTED_BUT_UNTESTED, encoding="utf-8")
        git("add", "clean_module.py", cwd=clone)
        assert git("commit", "-m", "untested module", cwd=clone).returncode == 0
        bare = tmp_path / "remote.git"
        subprocess.run(  # noqa: S603
            ["git", "init", "--quiet", "--bare", str(bare)],  # noqa: S607
            check=True,
            capture_output=True,
        )
        pushed = git("push", str(bare), "HEAD:refs/heads/main", cwd=clone)
        assert pushed.returncode != 0, "the push stage let a failing gate through"
        assert "pytest" in pushed.stdout + pushed.stderr


class TestSkippingTheSetupStepConverges:
    """`--no-install` is documented, so what it leaves behind must be usable."""

    @staticmethod
    @pytest.fixture(scope="class")
    def caught_up(tmp_path_factory: pytest.TempPathFactory) -> Path:
        """
        Generate a project with ``--no-install``, then finish it by hand.

        Exactly the sequence the README gives somebody who skipped the
        setup step, which has to reach the state the automatic path
        reaches or the documentation is wrong.

        :param tmp_path_factory: The fixture the project is created under.
        :return: The finished project.
        """
        parent = tmp_path_factory.mktemp("catchup")
        generated = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "new_project.py",
                "catch-up-app",
                "--into",
                str(parent),
                "--no-install",
            ],
            cwd=TEMPLATE_ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=child_environment(),
        )
        assert generated.returncode == 0, generated.stdout + generated.stderr
        created = parent / "catch-up-app"
        assert not (created / ".git").exists(), "--no-install should not have run git init"
        git("init", "--quiet", cwd=created)
        git("config", "user.email", "journey@example.com", cwd=created)
        git("config", "user.name", "Journey", cwd=created)
        setup = subprocess.run(
            ["uv", "run", "python", "qa.py", "setup"],  # noqa: S607
            cwd=created,
            check=False,
            capture_output=True,
            text=True,
            env=child_environment(),
        )
        assert setup.returncode == 0, setup.stdout + setup.stderr
        return created

    def test_it_ends_up_with_both_hooks_installed(self, caught_up: Path) -> None:
        """The manual path must not leave somebody with half the gates."""
        assert (caught_up / ".git" / "hooks" / "pre-commit").is_file()
        assert (caught_up / ".git" / "hooks" / "pre-push").is_file()

    def test_staging_everything_reports_no_line_ending_warnings(self, caught_up: Path) -> None:
        """Twenty warnings about files nobody wrote reads as something broken."""
        # Not the same question as whether the bytes on disk are LF, which
        # tests/test_new_project.py already asks. This is what Git itself
        # says when the whole project is staged for its first commit, with
        # the generated .gitattributes in force - the thing somebody
        # actually sees, and which used to fill a screen.
        added = git("add", "-A", cwd=caught_up)
        assert "CRLF" not in added.stderr, added.stderr
