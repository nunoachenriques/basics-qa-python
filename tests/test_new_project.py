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

Test the ``new_project`` bootstrap script.
"""

import contextlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

import new_project
from new_project import (
    PROJECT_NAME_PATTERN,
    ProjectError,
    build_parser,
    copy_template,
    create_project,
    install_environment,
    is_excluded,
    main,
    resolve_destination,
    rewrite,
    run,
    to_package_name,
    to_script_name,
    to_title,
    validate_project_name,
)

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


class TestNameConversion:
    """Test the name-derivation helpers."""

    def test_package_name_replaces_hyphens(self) -> None:
        """A distribution name becomes a valid Python identifier."""
        assert to_package_name("my-new-project") == "my_new_project"

    def test_title_capitalises_each_word(self) -> None:
        """A distribution name becomes a readable title."""
        assert to_title("my-new-project") == "My New Project"

    def test_script_name_matches_distribution(self) -> None:
        """The console script keeps the distribution name."""
        assert to_script_name("my-new-project") == "my-new-project"


class TestCopyFailsClearly:
    """A filesystem error must say what to do, not print a traceback."""

    def test_a_copy_failure_is_explained(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The Windows 260-character path limit arrives as a bare OSError."""

        def boom(*_args: object, **_kwargs: object) -> None:
            raise OSError(2, "The system cannot find the file specified")

        monkeypatch.setattr(shutil, "copytree", boom)
        with pytest.raises(ProjectError, match="260 characters"):
            copy_template(TEMPLATE_ROOT, tmp_path / "somewhere")


class TestValidation:
    """Test :py:func:`validate_project_name`."""

    @pytest.mark.parametrize("name", ["con", "prn", "aux", "nul", "com1", "lpt1"])
    def test_rejects_windows_device_names(self, name: str) -> None:
        """Windows resolves these to devices, so the directory misbehaves."""
        # `nul` is the worst of them: Path("nul").exists() is True in an empty
        # directory, so the collision check reported that a project already
        # existed somewhere nothing did.
        with pytest.raises(ProjectError, match="reserves"):
            validate_project_name(name)

    @pytest.mark.parametrize("name", ["a", "my-project", "project2", "a-b-c"])
    def test_accepts_valid_names(self, name: str) -> None:
        """Valid PEP 503 style names are accepted."""
        validate_project_name(name)

    @pytest.mark.parametrize(
        "name",
        [
            "My-Project",
            "my_project",
            "2project",
            "my--project",
            "my-",
            "-my",
            "",
            # Found by the property test below, kept here as an example
            # because Hypothesis's own record of it is a local cache that
            # Git never sees. `$` matches before a trailing newline, so this
            # validated and then created a directory with a newline in its
            # name; the pattern is anchored with `\Z` now.
            "my-project\n",
        ],
    )
    def test_rejects_invalid_names(self, name: str) -> None:
        """Names that would break packaging are rejected."""
        with pytest.raises(ProjectError, match="not a valid project name"):
            validate_project_name(name)


class TestRewrite:
    """Test :py:func:`rewrite`."""

    def test_replaces_distribution_name(self) -> None:
        """The distribution name is replaced."""
        assert rewrite('name = "basics-qa-python"', "my-app") == 'name = "my-app"'

    def test_replaces_package_name_whole_word_only(self) -> None:
        """The package name is replaced, but only as a whole word."""
        assert rewrite("from basics import x", "my-app") == "from my_app import x"
        assert rewrite("the basicsxyz thing", "my-app") == "the basicsxyz thing"

    def test_replaces_capitalised_prose(self) -> None:
        """The capitalised template name in prose is replaced too."""
        assert rewrite("Basics rocks", "my-app") == "My App rocks"

    def test_replaces_full_title(self) -> None:
        """The full template title is replaced as a unit."""
        assert rewrite("Basics on Quality Assurance in Python", "my-app") == "My App"

    def test_replaces_console_script_name(self) -> None:
        """The console script keeps a usable name."""
        assert 'my-app = "' in rewrite('basics-qa = "basics.cli:main"', "my-app")

    def test_replaces_script_name_in_prose_too(self) -> None:
        """A mention of the script in a comment is renamed, not mangled."""
        assert rewrite("run basics-qa ARG", "my-app") == "run my-app ARG"

    def test_distribution_name_is_not_mangled_by_script_name(self) -> None:
        """The distribution name contains the script name; order must hold."""
        assert rewrite('"basics-qa-python"', "my-app") == '"my-app"'


class TestPropertiesThatMustAlwaysHold:
    """
    Rules that hold for every input, not only the ones we thought of.

    The name is the very first thing anybody types, and it arrives from a
    shell that will hand over whatever was pasted into it.
    """

    @given(name=st.text())
    def test_validation_only_ever_raises_project_error(self, name: str) -> None:
        """Any other exception reaches a newcomer as a traceback."""
        # The entire point of validating is that a bad name produces an
        # explanation. A name that instead trips some IndexError deep inside
        # is the one case that explanation never covers.
        with contextlib.suppress(ProjectError):
            validate_project_name(name)

    @given(name=st.from_regex(PROJECT_NAME_PATTERN))
    def test_an_accepted_name_is_always_an_importable_package(self, name: str) -> None:
        """Accepting a name that cannot be imported only defers the failure."""
        try:
            validate_project_name(name)
        except ProjectError:
            return
        assert to_package_name(name).isidentifier()

    @given(text=st.text())
    def test_rewriting_twice_changes_nothing_further(self, text: str) -> None:
        """Renaming an already-renamed tree must leave it exactly as it was."""
        once = rewrite(text, "my-app")
        assert rewrite(once, "my-app") == once


class TestExclusion:
    """Test :py:func:`is_excluded`."""

    def test_excludes_cache_directories(self, tmp_path: Path) -> None:
        """Generated directories are not copied."""
        assert is_excluded(tmp_path / ".venv" / "x", tmp_path)

    def test_excludes_the_script_itself(self, tmp_path: Path) -> None:
        """A generated project is not itself a template."""
        assert is_excluded(tmp_path / "new_project.py", tmp_path)

    def test_keeps_source_files(self, tmp_path: Path) -> None:
        """Ordinary source files are copied."""
        assert not is_excluded(tmp_path / "basics" / "cli.py", tmp_path)


class TestCopyTemplate:
    """Test :py:func:`copy_template`."""

    def test_refuses_an_existing_destination(self, tmp_path: Path) -> None:
        """An existing directory is never overwritten."""
        destination = tmp_path / "already-here"
        destination.mkdir()
        with pytest.raises(ProjectError, match="already exists"):
            copy_template(TEMPLATE_ROOT, destination)


class TestRun:
    """Test :py:func:`run`."""

    def test_reports_a_missing_command_without_raising(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A missing tool warns rather than aborting the whole run."""
        # Deliberately stderr, not the logger: the logger is at CRITICAL
        # unless -v was passed, which used to swallow this entirely.
        assert run(["definitely-not-a-real-command"], tmp_path) is False
        assert "definitely-not-a-real-command" in capsys.readouterr().err

    def test_reports_a_failing_command_without_raising(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A non-zero exit warns rather than aborting the whole run."""

        def fail(*_args: object, **_kwargs: object) -> None:
            raise subprocess.CalledProcessError(1, "boom")

        monkeypatch.setattr(subprocess, "run", fail)
        assert run(["boom"], tmp_path) is False
        assert "boom failed" in capsys.readouterr().err

    def test_runs_a_real_command(self) -> None:
        """A working command runs to completion without warning."""
        # Deliberately run from the template root rather than a tmp directory:
        # pytest-cov measures subprocesses, and a subprocess started where
        # pyproject.toml is not discoverable records statement-only data,
        # which then cannot be combined with this run's branch data.
        assert run([sys.executable, "-c", "pass"], TEMPLATE_ROOT) is True

    def test_does_not_leak_the_template_environment(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The template's ``VIRTUAL_ENV`` is not inherited by setup commands."""
        captured: dict[str, str] = {}

        def capture(*_args: object, env: dict[str, str], **_kwargs: object) -> None:
            captured.update(env)

        monkeypatch.setenv("VIRTUAL_ENV", str(TEMPLATE_ROOT / ".venv"))
        monkeypatch.setenv("QA_SENTINEL", "kept")
        monkeypatch.setattr(subprocess, "run", capture)
        run(["uv", "sync", "--dev"], tmp_path)
        assert "VIRTUAL_ENV" not in captured
        # The rest of the environment must survive: dropping one variable, not
        # handing the child an empty one.
        assert captured["QA_SENTINEL"] == "kept"


class TestCreateProject:
    """Test :py:func:`create_project` end to end, without installing."""

    @staticmethod
    @pytest.fixture(scope="class")
    def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
        """Generate one project and share it across this class's tests."""
        destination = tmp_path_factory.mktemp("generated") / "my-app"
        created, _failures = create_project("my-app", destination, TEMPLATE_ROOT, install=False)
        return created

    def test_package_directory_is_renamed(self, project: Path) -> None:
        """The import package takes the new name."""
        assert (project / "my_app").is_dir()
        assert not (project / "basics").exists()

    def test_no_template_identifiers_remain(self, project: Path) -> None:
        """Nothing in the generated code still refers to the template."""
        for path in project.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".toml", ".yaml", ".yml"}:
                assert "basics" not in path.read_text(encoding="utf-8").lower()

    def test_version_is_reset(self, project: Path) -> None:
        """A new project starts at 0.1.0, not the template's version."""
        assert 'version = "0.1.0"' in (project / "pyproject.toml").read_text(encoding="utf-8")

    def test_changelog_is_fresh(self, project: Path) -> None:
        """The template's release history is not inherited."""
        assert "generated from the Basics QA Python template" in (
            project / "CHANGELOG.md"
        ).read_text(encoding="utf-8")

    def test_script_is_not_copied(self, project: Path) -> None:
        """A generated project is not itself a template."""
        assert not (project / "new_project.py").exists()

    def test_quality_configuration_is_carried_over(self, project: Path) -> None:
        """The point of the template - its gates - comes along."""
        assert (project / ".pre-commit-config.yaml").is_file()
        assert (project / "pyproject.toml").is_file()
        assert (project / "my_app" / "py.typed").is_file()

    def test_every_generated_file_uses_lf_line_endings(self, project: Path) -> None:
        """A CRLF tree drowns the new project's first commit in Git warnings."""
        # write_text's platform default translated every rewritten file to
        # CRLF on Windows, which the generated .gitattributes (eol=lf) then
        # flagged file by file the moment anything was staged.
        for path in project.rglob("*"):
            if path.is_file():
                assert b"\r\n" not in path.read_bytes(), path

    def test_rejects_an_invalid_name(self, tmp_path: Path) -> None:
        """Validation happens before anything is written."""
        destination = tmp_path / "Bad-Name"
        with pytest.raises(ProjectError, match="not a valid project name"):
            create_project("Bad-Name", destination, TEMPLATE_ROOT, install=False)
        assert not destination.exists()


class TestMain:
    """Test the :py:func:`main` entry point."""

    def test_creates_a_project(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """A valid invocation creates the project and exits zero."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["new_project.py", "my-app", "--into", str(tmp_path), "--no-install", "-v"],
        )
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        assert (tmp_path / "my-app" / "my_app").is_dir()

    def test_reports_an_invalid_name(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An invalid name exits non-zero with a message on stderr."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["new_project.py", "Bad-Name", "--into", str(tmp_path), "--no-install", "-vv"],
        )
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "not a valid project name" in capsys.readouterr().err


class TestInstallEnvironment:
    """Test :py:func:`install_environment`."""

    def test_runs_the_expected_setup_commands(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Git init, uv sync, and both hook stages are all set up."""
        calls: list[list[str]] = []

        def succeed(command: list[str], _cwd: Path) -> bool:
            calls.append(command)
            return True

        monkeypatch.setattr(new_project, "run", succeed)
        assert install_environment(tmp_path) == []
        assert calls[0] == ["git", "init", "--quiet"]
        assert calls[1] == ["uv", "sync", "--dev"]
        # Order matters: ruff recommends the linter before the formatter.
        assert calls.index(["uv", "run", "ruff", "check", ".", "--fix"]) < calls.index(
            ["uv", "run", "ruff", "format", "."],
        )
        assert ["uv", "run", "pre-commit", "install", "-t", "pre-commit"] in calls
        assert ["uv", "run", "pre-commit", "install", "-t", "pre-push"] in calls


class TestCreateProjectInstalls:
    """Test that :py:func:`create_project` honours the install flag."""

    def test_install_is_performed_when_requested(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """With install=True the environment setup runs."""
        performed: list[Path] = []

        def record(destination: Path) -> list[list[str]]:
            performed.append(destination)
            return []

        monkeypatch.setattr(new_project, "install_environment", record)
        create_project("my-app", tmp_path / "my-app", TEMPLATE_ROOT, install=True)
        assert performed == [tmp_path / "my-app"]


class TestResolveDestination:
    """Test :py:func:`resolve_destination`."""

    def test_defaults_beside_the_template(self, tmp_path: Path) -> None:
        """Without --into, the project is created next to the template."""
        template_root = tmp_path / "template"
        assert resolve_destination("my-app", None, template_root) == tmp_path / "my-app"

    def test_honours_an_explicit_parent(self, tmp_path: Path) -> None:
        """With --into, the project is created inside the given directory."""
        assert resolve_destination("my-app", tmp_path, tmp_path / "t") == tmp_path / "my-app"

    def test_expands_a_literal_tilde(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The documented `--into ~/work` reaches here unexpanded from PowerShell."""
        # expanduser reads HOME on POSIX and USERPROFILE on Windows.
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        destination = resolve_destination("my-app", Path("~") / "work", tmp_path / "t")
        assert destination == tmp_path / "work" / "my-app"


class TestParser:
    """Test :py:func:`build_parser`."""

    def test_no_install_defaults_to_false(self) -> None:
        """Installation happens unless it is explicitly skipped."""
        assert build_parser().parse_args(["my-app"]).no_install is False
