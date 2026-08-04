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

Test the template from the point of view of somebody who has just cloned it.

The gates in this project all assume a working environment and a reader who
knows what the commands do. These tests assume neither. They cover the paths
somebody takes in their first hour - the name they pick, the command they
copy out of the README, the step they skip - and they are deliberately
written against the repository's own files, so documentation that drifts
away from the code fails here rather than in somebody's afternoon.

Not copied into generated projects: like ``test_new_project.py``, this
tests the template itself, and the script it tests does not ship.
"""

import keyword
import os
import re
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import pytest

import new_project
from new_project import (
    EXCLUDED_NAMES,
    PROJECT_NAME_PATTERN,
    TEMPLATE_PACKAGE,
    ProjectError,
    create_project,
    shipped_top_level_names,
    to_package_name,
    validate_destination,
    validate_no_collision,
    validate_project_name,
)
from qa import TASKS

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

#: Names that read as perfectly reasonable projects but break the moment
#: they become an import package.
KEYWORD_NAMES = ("class", "import", "del", "lambda", "return", "pass", "try")

#: Standard library modules somebody could plausibly name a project after.
STDLIB_NAMES = ("json", "email", "types", "string", "logging", "csv", "queue")

#: Directories and modules every generated project already contains.
COLLIDING_NAMES = ("tests", "docs", "qa", "app-cli")

#: Names that must keep working; the validation has to reject the bad ones
#: without also turning away the ordinary ones.
GOOD_NAMES = (
    "my-new-project",
    "api-pagamentos",
    "detetor2",
    "web-api",
    "zzz-last",
    "a",
    "classifier",
    "json-tools",
)


def read_text(relative: str) -> str:
    """
    Read one of the repository's own files.

    :param relative: Path relative to the repository root.
    :return: The file's text.
    """
    return (TEMPLATE_ROOT / relative).read_text(encoding="utf-8")


class TestNamesThatLookFineButBreak:
    """A name is typed once, by somebody with no reason to know the rules."""

    @pytest.mark.parametrize("name", KEYWORD_NAMES)
    def test_rejects_a_python_keyword(self, name: str) -> None:
        """`from class.cli import ...` is a SyntaxError, not a subtle problem."""
        with pytest.raises(ProjectError, match="keyword"):
            validate_project_name(name)

    @pytest.mark.parametrize("name", STDLIB_NAMES)
    def test_rejects_a_standard_library_module(self, name: str) -> None:
        """Shadowing `json` breaks whatever imports the real one, far from here."""
        with pytest.raises(ProjectError, match="standard library"):
            validate_project_name(name)

    @pytest.mark.parametrize("name", COLLIDING_NAMES)
    def test_rejects_a_name_the_template_already_ships(self, name: str) -> None:
        """`tests` used to abort mid-copy with a traceback and a half-built tree."""
        with pytest.raises(ProjectError, match="already contains"):
            validate_no_collision(name, TEMPLATE_ROOT)

    @pytest.mark.parametrize("name", GOOD_NAMES)
    def test_accepts_an_ordinary_name(self, name: str) -> None:
        """Rejecting the bad names must not start rejecting the good ones."""
        validate_project_name(name)
        validate_no_collision(name, TEMPLATE_ROOT)

    def test_the_template_package_is_not_treated_as_a_collision(self) -> None:
        """That directory is the one being renamed, so its name is free."""
        validate_no_collision(TEMPLATE_PACKAGE, TEMPLATE_ROOT)

    @pytest.mark.parametrize(
        "name",
        ["My-Project", "my_project", "2fast", "-leading", "trailing-", "my--project", ""],
    )
    def test_rejects_a_malformed_name(self, name: str) -> None:
        """The shape rules are checked before anything else happens."""
        with pytest.raises(ProjectError, match="not a valid project name"):
            validate_project_name(name)

    def test_every_message_says_what_to_do_instead(self) -> None:
        """A refusal that does not suggest a fix just moves the problem."""
        for name in (*KEYWORD_NAMES, *STDLIB_NAMES, "My-Project"):
            with pytest.raises(ProjectError) as exc_info:
                validate_project_name(name)
            assert "example" in str(exc_info.value)

    def test_a_rejected_name_writes_nothing(self, tmp_path: Path) -> None:
        """Refusing halfway through would leave a directory nobody asked for."""
        destination = tmp_path / "class"
        with pytest.raises(ProjectError):
            create_project("class", destination, TEMPLATE_ROOT, install=False)
        assert not destination.exists()

    def test_a_collision_writes_nothing(self, tmp_path: Path) -> None:
        """The `tests` crash left a half-built tree behind; it must not now."""
        destination = tmp_path / "tests"
        with pytest.raises(ProjectError):
            create_project("tests", destination, TEMPLATE_ROOT, install=False)
        assert not destination.exists()


class TestWhereTheProjectLands:
    """`--into .` is one keystroke away, and it used to break the template."""

    def test_refuses_to_generate_inside_the_template(self) -> None:
        """Nested, both copies are collected and every test module fails to import."""
        with pytest.raises(ProjectError, match="inside the template"):
            validate_destination(TEMPLATE_ROOT / "nested-app", TEMPLATE_ROOT)

    def test_refuses_a_deeply_nested_destination(self) -> None:
        """Any depth inside the template has the same effect, not just the top."""
        with pytest.raises(ProjectError, match="inside the template"):
            validate_destination(TEMPLATE_ROOT / "docs" / "deep" / "app", TEMPLATE_ROOT)

    def test_refuses_the_template_root_itself(self) -> None:
        """Copying the template over itself is the worst case of all."""
        with pytest.raises(ProjectError, match="inside the template"):
            validate_destination(TEMPLATE_ROOT, TEMPLATE_ROOT)

    def test_refuses_a_relative_path_that_resolves_inside(self, tmp_path: Path) -> None:
        """`--into .` arrives unresolved, so a plain comparison would miss it."""
        with pytest.raises(ProjectError, match="inside the template"):
            validate_destination(TEMPLATE_ROOT / "sub" / ".." / "app", TEMPLATE_ROOT)
        # A relative path outside the template must still be allowed.
        validate_destination(tmp_path / "app", TEMPLATE_ROOT)

    def test_allows_the_default_sibling_destination(self) -> None:
        """The documented default puts the project next to the template."""
        validate_destination(TEMPLATE_ROOT.parent / "my-new-project", TEMPLATE_ROOT)

    def test_allows_an_unrelated_directory(self, tmp_path: Path) -> None:
        """`--into ~/work` is documented and must keep working."""
        validate_destination(tmp_path / "my-new-project", TEMPLATE_ROOT)

    def test_refuses_a_symlink_that_leads_back_into_the_template(self, tmp_path: Path) -> None:
        """A path can point inside the template without looking as though it does."""
        link = tmp_path / "shortcut"
        try:
            link.symlink_to(TEMPLATE_ROOT, target_is_directory=True)
        except (OSError, NotImplementedError):
            # Windows needs Developer Mode or elevation to create one.
            pytest.skip("this platform does not permit creating a symlink here")
        with pytest.raises(ProjectError, match="inside the template"):
            validate_destination(link / "nested-app", TEMPLATE_ROOT)

    def test_nothing_is_written_when_the_destination_is_refused(self) -> None:
        """Refusing after copying would leave the very mess this prevents."""
        destination = TEMPLATE_ROOT / "nested-app"
        with pytest.raises(ProjectError):
            create_project("nested-app", destination, TEMPLATE_ROOT, install=False)
        assert not destination.exists()


class TestFailedSetupIsImpossibleToMiss:
    """Reporting success after a failed setup step is the worst possible answer."""

    @staticmethod
    def break_every_command(monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Make every setup command fail, as a missing tool would.

        :param monkeypatch: The fixture to patch through.
        """
        monkeypatch.setattr(new_project, "run", lambda _command, _cwd: False)

    def test_failures_are_reported_on_stderr_not_through_the_logger(
        self,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """The logger sits at CRITICAL by default, which swallowed the warning."""
        new_project.run(["definitely-not-a-real-command"], tmp_path)
        assert "definitely-not-a-real-command" in capsys.readouterr().err

    def test_run_reports_success_and_failure(self, tmp_path: Path) -> None:
        """The caller cannot count failures it is not told about."""
        assert new_project.run([sys.executable, "-c", "pass"], TEMPLATE_ROOT) is True
        assert new_project.run(["definitely-not-a-real-command"], tmp_path) is False

    def test_install_environment_returns_what_failed(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Every command is still attempted, so the report is complete."""
        self.break_every_command(monkeypatch)
        failures = new_project.install_environment(tmp_path)
        assert ["uv", "sync", "--dev"] in failures
        assert ["git", "init", "--quiet"] in failures
        assert len(failures) == len(new_project.install_environment(tmp_path))

    def test_main_exits_non_zero_when_setup_fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Exit zero after a failed uv sync is the worst possible answer."""
        self.break_every_command(monkeypatch)
        monkeypatch.setattr(
            sys,
            "argv",
            ["new_project.py", "my-app", "--into", str(tmp_path)],
        )
        with pytest.raises(SystemExit) as exc_info:
            new_project.main()
        assert exc_info.value.code == 1

    def test_main_names_the_commands_to_run_by_hand(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """Telling somebody setup failed without saying what to run just worries them."""
        self.break_every_command(monkeypatch)
        monkeypatch.setattr(
            sys,
            "argv",
            ["new_project.py", "my-app", "--into", str(tmp_path)],
        )
        with pytest.raises(SystemExit):
            new_project.main()
        captured = capsys.readouterr()
        assert "Setup did not finish" in captured.err
        assert "uv sync --dev" in captured.err
        # The directory really was created, so say so rather than implying
        # the whole thing failed and leaving a stray directory unexplained.
        assert "Created" in captured.out

    def test_a_clean_run_still_exits_zero(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The failure path must not start firing on successful runs."""
        monkeypatch.setattr(new_project, "run", lambda _command, _cwd: True)
        monkeypatch.setattr(
            sys,
            "argv",
            ["new_project.py", "my-app", "--into", str(tmp_path)],
        )
        with pytest.raises(SystemExit) as exc_info:
            new_project.main()
        assert exc_info.value.code == 0


class TestTasksSucceedWhenTheyShould:
    """A task that always fails teaches people to ignore the output."""

    def test_fast_does_not_apply_the_coverage_gate(self) -> None:
        """The integration tests are the only cover for app_cli.py."""
        command = TASKS["fast"].commands[0]
        assert "--no-cov" in command, (
            "`fast` deselects the integration tests, so the 100% gate is "
            "unreachable and the task would fail every time it is run."
        )

    def test_only_fast_disables_coverage(self) -> None:
        """Any other task dropping the gate would hide a real regression."""
        for name, task in TASKS.items():
            if name == "fast":
                continue
            for command in task.commands:
                assert "--no-cov" not in command

    def test_test_keeps_the_coverage_gate(self) -> None:
        """`test` is the one that has to hold the line."""
        assert TASKS["test"].commands == (("uv", "run", "pytest"),)

    def test_the_marker_help_points_at_the_safe_command(self) -> None:
        """The marker's own hint in pyproject.toml described the failing invocation."""
        assert "deselect with qa.py fast" in read_text("pyproject.toml")


class TestGeneratedProjectActuallyRuns:
    """The first thing anyone does is run the thing they just generated."""

    @staticmethod
    @pytest.fixture(scope="class")
    def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
        """Generate one project, shared across this class's tests."""
        destination = tmp_path_factory.mktemp("onboarding") / "web-api"
        created, _failures = create_project("web-api", destination, TEMPLATE_ROOT, install=False)
        return created

    def test_every_python_file_parses(self, project: Path) -> None:
        """Renaming must not produce a file Python cannot even read."""
        for path in project.rglob("*.py"):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_the_package_is_importable_by_name(self, project: Path) -> None:
        """The renamed package has to be a legal identifier, not just a directory."""
        package = to_package_name("web-api")
        assert (project / package / "__init__.py").is_file()
        assert package.isidentifier()
        assert not keyword.iskeyword(package)

    def test_the_template_script_does_not_ship(self, project: Path) -> None:
        """A generated project is not itself a template."""
        assert not (project / "new_project.py").exists()

    def test_tests_of_the_template_do_not_ship(self, project: Path) -> None:
        """They import new_project, which is not there, so they could only fail."""
        assert not (project / "tests" / "test_new_project.py").exists()
        assert not (project / "tests" / "test_onboarding.py").exists()

    def test_the_task_runner_ships(self, project: Path) -> None:
        """The commands have to come along, or the gates go unrun."""
        assert (project / "qa.py").is_file()
        assert (project / "tests" / "test_qa.py").is_file()

    def test_the_hooks_configuration_ships(self, project: Path) -> None:
        """Without it `pre-commit install` has nothing to install."""
        assert (project / ".pre-commit-config.yaml").is_file()

    def test_no_template_name_survives_anywhere(self, project: Path) -> None:
        """A missed reference ships the template's name in somebody's --help."""
        for path in project.rglob("*"):
            # CHANGELOG.md is exempt: the fresh changelog deliberately records
            # which template the project was generated from, which is
            # provenance worth keeping, not a rename that was missed.
            if path.name == "CHANGELOG.md":
                continue
            if path.is_file() and path.suffix in {".py", ".toml", ".yaml", ".yml", ".md"}:
                assert TEMPLATE_PACKAGE not in path.read_text(encoding="utf-8").lower()

    def test_it_starts_at_version_zero_one_zero(self, project: Path) -> None:
        """Inheriting the template's version would be wrong from the first commit."""
        assert 'version = "0.1.0"' in (project / "pyproject.toml").read_text(encoding="utf-8")

    def test_the_lock_file_agrees_with_the_version(self, project: Path) -> None:
        """A lock that disagrees makes `qa.py setup` fail before it installs anything."""
        # uv.lock records the project as one of its own packages. Renaming
        # alone left that entry at the template's version, and the first
        # documented command runs `uv sync --locked`, which refuses outright.
        lock = (project / "uv.lock").read_text(encoding="utf-8")
        entry = re.search(r'name = "web-api"\r?\nversion = "([^"]+)"', lock)
        assert entry is not None, "the lock file has no entry for the project"
        assert entry.group(1) == "0.1.0"

    def test_the_readme_does_not_send_you_to_a_missing_script(self, project: Path) -> None:
        """The generated README kept telling its reader to run new_project.py."""
        assert "new_project.py" not in (project / "README.md").read_text(encoding="utf-8")

    def test_it_does_not_inherit_the_template_authors(self, project: Path) -> None:
        """Shipping a new project credited to somebody else states something untrue."""
        pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
        assert "nunoachenriques" not in pyproject
        assert "alex.mf.alm" not in pyproject

    def test_it_does_not_claim_the_template_authors_copyright(self, project: Path) -> None:
        """A new project whose README says somebody else owns it is simply wrong."""
        # The source files keep the template's notice, and must: the Apache
        # licence requires a derivative work to retain it. The README is a
        # different thing - it describes THIS project - and it used to say
        # the whole of it was copyright the template's author, while the
        # pyproject.toml two directories away said "Your Name".
        readme = (project / "README.md").read_text(encoding="utf-8")
        assert "Copyright 2022 Nuno A. C. Henriques https://" not in readme
        assert "Your Name" in readme
        # The attribution the licence does require is still there.
        assert "Nuno A. C. Henriques" in readme

    def test_the_source_headers_keep_the_original_notice(self, project: Path) -> None:
        """Stripping them would be the actual licence violation."""
        header = (project / to_package_name("web-api") / "cli.py").read_text(encoding="utf-8")
        assert "Copyright 2022 Nuno A. C. Henriques" in header

    def test_it_does_not_inherit_the_template_history(self, project: Path) -> None:
        """The template's origin story is not the new project's."""
        readme = (project / "README.md").read_text(encoding="utf-8")
        assert "## History" not in readme
        # That section also carried the one place "basics" appeared as an
        # ordinary English word rather than as the package name, so renaming
        # turned it into "compile some web_api of quality assurance".
        assert "of quality assurance" not in readme
        assert "](#history)" not in readme, "the contents list still links to it"

    def test_no_stray_coverage_data_is_copied(self, project: Path) -> None:
        """Coverage writes .coverage.<host>.<pid>.<random>, which a plain name misses."""
        assert not list(project.glob(".coverage*"))

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "gate",
        [
            ["-m", "ruff", "format", "--check", "."],
            ["-m", "ruff", "check", ".", "--no-fix"],
            ["-m", "mypy", "."],
        ],
        ids=["format", "lint", "types"],
    )
    def test_it_passes_its_own_gates(self, project: Path, gate: list[str]) -> None:
        """The template's whole promise is that the checks come along working."""
        # This is the test whose absence let a real regression ship: renaming
        # perturbed import order and line length, so a generated project
        # failed two of its own gates from the first minute. Nothing here ran
        # a gate against generated code, so nothing noticed.
        #
        # `-m` rather than the bare executable: same interpreter as the suite,
        # and no dependency on what happens to be on PATH.
        #
        # COV_CORE_* is stripped from the environment because pytest-cov hooks
        # every subprocess it can. Left in place, these runs report the
        # generated project's own files as uncovered and drag the measured
        # total below the gate.
        environment = {
            name: value for name, value in os.environ.items() if not name.startswith("COV_CORE")
        }
        result = subprocess.run(  # noqa: S603
            [sys.executable, *gate],
            cwd=project,
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        assert result.returncode == 0, result.stdout + result.stderr


class TestTheDocumentedCommandsAreReal:
    """Somebody's first commands are copied out of the README verbatim."""

    @staticmethod
    def documented_tasks(text: str) -> set[str]:
        """
        Collect every `qa.py <task>` named in a document.

        :param text: The document's text.
        :return: The task names it mentions.
        """
        return set(re.findall(r"qa\.py ([a-z]+)", text))

    def test_every_task_the_readme_names_exists(self) -> None:
        """A command that does not exist is worse than one nobody mentioned."""
        assert self.documented_tasks(read_text("README.md")) <= set(TASKS)

    def test_every_task_the_changelog_names_exists(self) -> None:
        """The changelog is read by people deciding whether to upgrade."""
        assert self.documented_tasks(read_text("CHANGELOG.md")) <= set(TASKS)

    def test_the_readme_shows_the_setup_command(self) -> None:
        """The one step a fresh clone cannot do without."""
        assert "qa.py setup" in read_text("README.md")

    def test_the_readme_uses_the_uv_run_prefix_throughout(self) -> None:
        """Dropping it is the classic way to install into the wrong environment."""
        for line in read_text("README.md").splitlines():
            stripped = line.strip()
            if stripped.startswith(("python ", "pytest", "ruff ", "mypy ", "pip ")):
                pytest.fail(f"README shows an unprefixed command: {stripped}")

    @pytest.mark.parametrize("document", ["README.md", "CONTRIBUTING.md"])
    def test_no_removed_tool_is_still_recommended(self, document: str) -> None:
        """`pipenv` went in 3.0.0; being told to run it wastes a newcomer's hour."""
        assert "pipenv" not in read_text(document)

    @pytest.mark.parametrize("document", ["README.md", "CONTRIBUTING.md"])
    def test_referenced_repository_files_exist(self, document: str) -> None:
        """A dead link in the first page somebody reads is a bad first impression."""
        for target in re.findall(r"\]\((docs/[^)#]+|[A-Z][A-Za-z-]*\.md)\)", read_text(document)):
            assert (TEMPLATE_ROOT / target).exists(), f"{document} links to missing {target}"


class TestSetupLeavesNothingToRemember:
    """Git does not clone .git/hooks, so a fresh checkout has no gates."""

    def test_setup_installs_both_hook_stages(self) -> None:
        """One missing stage means half the gates silently never run."""
        commands = TASKS["setup"].commands
        assert ("uv", "run", "pre-commit", "install", "-t", "pre-commit") in commands
        assert ("uv", "run", "pre-commit", "install", "-t", "pre-push") in commands

    def test_setup_installs_the_environment_first(self) -> None:
        """pre-commit is itself a dev dependency; installing hooks first cannot work."""
        commands = list(TASKS["setup"].commands)
        assert commands[0] == ("uv", "sync", "--dev", "--locked")

    def test_setup_is_the_first_task_offered(self) -> None:
        """`qa.py` with no argument lists the tasks; the first one should be step one."""
        assert next(iter(TASKS)) == "setup"

    def test_every_hook_stage_in_the_configuration_is_installed(self) -> None:
        """A stage configured but never installed is a gate that does not exist."""
        # Read the whole bracketed list, not one \S+ token: a hook declaring
        # two stages would have gone unnoticed rather than failing, because
        # \S+ cannot span the space between them.
        configured = {
            stage.strip()
            for group in re.findall(r"stages:\s*\[([^\]]*)\]", read_text(".pre-commit-config.yaml"))
            for stage in group.split(",")
        }
        installed = {
            command[-1] for command in TASKS["setup"].commands if "pre-commit" in command[:3]
        }
        assert configured == installed


class TestTheGatesAgreeWithEachOther:
    """Local gates that differ from CI teach people to distrust the local ones."""

    @staticmethod
    def workflow_text() -> str:
        """
        Read both continuous integration definitions as one blob.

        :return: The GitHub and GitLab configurations, concatenated.
        """
        return read_text(".github/workflows/qa.yml") + read_text(".gitlab-ci.yml")

    @pytest.mark.parametrize("workflow", [".github/workflows/qa.yml", ".gitlab-ci.yml"])
    @pytest.mark.parametrize(
        "gate",
        [
            r"uv run ruff format --check \.$",
            r"uv run ruff check \. --no-fix",
            r"uv run mypy \.$",
            r"uv run pytest(?: |$)",
            r"uv run pip-audit$",
        ],
        ids=["format", "lint", "types", "test", "audit"],
    )
    def test_continuous_integration_runs_the_gate(self, gate: str, workflow: str) -> None:
        """`qa.py check` promises to mirror CI, so CI must actually run these."""
        # Each file separately, not both concatenated: read as one blob, a
        # gate present in only one of the two pipelines passed for both, and
        # the pipeline missing it went green having never run it.
        #
        # Anchored patterns rather than plain substrings. "pip-audit" also
        # appears in the SBOM step and in comments, so a bare substring
        # search still passed with the audit gate deleted outright.
        assert re.search(gate, read_text(workflow), re.MULTILINE), f"{workflow} does not run {gate}"

    def test_check_runs_every_gate_continuous_integration_runs(self) -> None:
        """A gate only CI runs is one that fails after the push, not before."""
        checked = {command[2] for command in TASKS["check"].commands if command[1] == "run"}
        assert checked == {"ruff", "mypy", "pytest", "pip-audit"}

    def test_check_installs_from_the_lock_before_any_gate(self) -> None:
        """CI installs first, so a drifted lock fails there before a gate runs."""
        assert TASKS["check"].commands[0] == ("uv", "sync", "--dev", "--locked")

    def test_check_never_edits_files(self) -> None:
        """A command called `check` that rewrites code is a nasty surprise."""
        for command in TASKS["check"].commands:
            assert "--fix" not in command
            assert command[:4] != ("uv", "run", "ruff", "format") or "--check" in command

    def test_the_linter_runs_before_the_formatter_everywhere(self) -> None:
        """Three files used to disagree about this; they must not drift apart again."""
        hooks = read_text(".pre-commit-config.yaml")
        assert hooks.index("ruff check . --fix") < hooks.index("ruff format .")
        fix = list(TASKS["fix"].commands)
        assert fix.index(("uv", "run", "ruff", "check", ".", "--fix")) < fix.index(
            ("uv", "run", "ruff", "format", "."),
        )


class TestTheEnvironmentIsPinnedConsistently:
    """Version drift is invisible until it is a failing build nobody can reproduce."""

    @staticmethod
    def pyproject() -> dict[str, object]:
        """
        Parse the project's own metadata.

        :return: The parsed ``pyproject.toml``.
        """
        return tomllib.loads(read_text("pyproject.toml"))

    def test_the_pinned_interpreter_satisfies_the_declared_minimum(self) -> None:
        """`.python-version` decides what uv installs; it has to be allowed."""
        pinned = read_text(".python-version").strip()
        project = self.pyproject()["project"]
        assert isinstance(project, dict)
        minimum = str(project["requires-python"]).lstrip(">=")
        assert tuple(map(int, pinned.split("."))) >= tuple(map(int, minimum.split(".")))

    def test_the_linter_targets_the_oldest_supported_interpreter(self) -> None:
        """Linting for a newer version lets through code the minimum cannot run."""
        project = self.pyproject()["project"]
        assert isinstance(project, dict)
        minimum = str(project["requires-python"]).lstrip(">=").replace(".", "")
        assert f'target-version = "py{minimum}"' in read_text("pyproject.toml")

    def test_the_lock_file_is_committed(self) -> None:
        """Without it `uv sync --locked` cannot reproduce anything."""
        assert (TEMPLATE_ROOT / "uv.lock").is_file()

    def test_the_project_declares_no_runtime_dependencies(self) -> None:
        """A template that drags in libraries imposes them on every project built from it."""
        project = self.pyproject()["project"]
        assert isinstance(project, dict)
        assert project["dependencies"] == []


class TestOnboardingStaysQuick:
    """
    The first command has to feel instant, and nothing else guards that.

    Every gate here measures correctness. None measures the thing somebody
    actually experiences first, which is how long they wait after typing
    the command out of the README - and that degrades one carried file at
    a time, invisibly, until the template feels heavy.
    """

    #: Generous by an order of magnitude. This is not a benchmark; it is a
    #: tripwire for somebody adding a large file to the template and not
    #: noticing that every generated project now carries it.
    BUDGET_SECONDS = 15.0

    def test_generating_a_project_is_not_slow(self, tmp_path: Path) -> None:
        """Copy and rename only - no environment, so no network and no cache."""
        started = time.monotonic()
        create_project("budget-app", tmp_path / "budget-app", TEMPLATE_ROOT, install=False)
        elapsed = time.monotonic() - started
        assert elapsed < self.BUDGET_SECONDS, (
            f"generating a project took {elapsed:.1f}s, over the {self.BUDGET_SECONDS}s "
            "budget: something large is being carried into every new project"
        )


class TestTheRepositoryIsSafeToCloneTwice:
    """Generated state must never be committed, or the next clone inherits it."""

    @pytest.mark.parametrize("name", [".venv", "__pycache__", ".coverage", ".ruff_cache"])
    def test_generated_state_is_ignored(self, name: str) -> None:
        """Committing a virtual environment is a classic, and painful, first mistake."""
        assert name in read_text(".gitignore")

    @pytest.mark.parametrize("name", [".venv", "__pycache__", ".git", ".mypy_cache"])
    def test_generated_state_is_never_copied_into_a_new_project(self, name: str) -> None:
        """Copying `.venv` would hand the new project the old one's absolute paths."""
        assert name in EXCLUDED_NAMES

    def test_the_shipped_names_are_what_the_collision_check_uses(self) -> None:
        """The check is only as good as the list it consults."""
        shipped = shipped_top_level_names(TEMPLATE_ROOT)
        assert {"tests", "docs", "qa", TEMPLATE_PACKAGE} <= shipped
        assert "new_project" not in shipped
        assert ".venv" not in shipped

    def test_the_name_pattern_matches_the_documented_rules(self) -> None:
        """The README's table of valid and invalid names must not be aspirational."""
        assert PROJECT_NAME_PATTERN.match("my-new-project")
        assert not PROJECT_NAME_PATTERN.match("My-New-Project")
        assert not PROJECT_NAME_PATTERN.match("my_new_project")
        assert not PROJECT_NAME_PATTERN.match("2fast")

    def test_the_standard_library_list_is_the_real_one(self) -> None:
        """Hand-maintained copies of this list go stale every release."""
        assert "json" in sys.stdlib_module_names
        assert "tomllib" in sys.stdlib_module_names
