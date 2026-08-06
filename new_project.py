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

Create a new project from this template, in a new directory, ready to use.

Deliberately depends on the standard library only: it must run straight
after ``git clone``, before any environment exists, and it adds no
third-party code to the supply chain of either this repository or the
projects it creates.
"""

import argparse
import keyword
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

logger = logging.getLogger(__name__)

TEMPLATE_DISTRIBUTION = "basics-qa-python"
TEMPLATE_PACKAGE = "basics"
TEMPLATE_TITLE = "Basics on Quality Assurance in Python"
TEMPLATE_SCRIPT = "basics-qa"

#: Never copied into a generated project: caches, build output, the
#: template's own history, and this script together with its tests.
EXCLUDED_NAMES = frozenset(
    {
        ".git",
        ".venv",
        ".hypothesis",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        ".coverage",
        "coverage.xml",
        "CHANGELOG.md",
        "new_project.py",
        "test_new_project.py",
        "test_onboarding.py",
        # Clones the template and drives its onboarding, so in a generated
        # project it would clone a repository that has no commits yet.
        "test_journey.py",
    },
)

#: Never copied either, matched by prefix rather than in full. Coverage
#: writes one file per process as ``.coverage.<host>.<pid>.<random>``, so a
#: run that happens while the template's own tests are running would
#: otherwise drop another machine's measurements into a brand new project.
EXCLUDED_PREFIXES = (".coverage",)

#: A distribution name per PEP 503: lowercase, digits, single separators.
#: Anchored with ``\Z``, not ``$``: ``$`` also matches immediately before a
#: trailing newline, so ``"my-app\n"`` - which is what a name pasted out of
#: a file or a here-document arrives as - passed validation and went on to
#: create a directory with a newline in its name.
PROJECT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*\Z")

#: The version a generated project starts at.
INITIAL_VERSION = "0.1.0"

#: The ``version = "..."`` line of a TOML table, anchored so that keys which
#: merely end in ``version`` (``target-version``) cannot match. Read rather
#: than hardcoded: a literal copy of the template's current version would
#: silently stop matching the day the template is released again, leaving
#: every generated project claiming the template's version as its own.
VERSION_PATTERN = re.compile(r'^version = "[^"]*"$', re.MULTILINE)

#: A top-level TOML array assignment, from the key to its closing bracket.
ARRAY_PATTERN = "^{key} = \\[\n(?:.*\n)*?^\\]\n"

#: The ``[project.urls]`` table, header and entries. A generated project has
#: no home page yet, and inheriting the template's would point every new
#: project at somebody else's repository.
URLS_PATTERN = re.compile(r"^\[project\.urls\]\n(?:[A-Za-z].*\n)+\n", re.MULTILINE)

#: Placeholder ownership for a generated project, replacing the template
#: authors. Shipping a new project that credits this template's authors
#: states something untrue about who wrote it.
FRESH_AUTHORS = """authors = [
  {name = "Your Name", email = "you@example.com"},
]
"""

#: The template's copyright line, at the top of every source file and once
#: more in the README's licence section.
TEMPLATE_COPYRIGHT = "Copyright 2022 Nuno A. C. Henriques https://nunoachenriques.net"

#: What replaces it in a generated project's README, and ONLY there.
#:
#: The notices in the source files stay exactly as they are: the Apache
#: licence requires a derivative work to keep them, and stripping them
#: would be the actual violation. The README is different - it describes
#: the new project, and saying that project's copyright belongs to
#: somebody else is simply untrue. The template is not named here because
#: nothing generated may carry the template's name; ``CHANGELOG.md``
#: records which template this came from, and is exempt for that reason.
FRESH_COPYRIGHT = """Copyright {year} Your Name

Generated from a project template, Copyright 2022 Nuno A. C. Henriques,
and licensed the same way. The notice at the top of each source file is
the template's; the Apache licence requires a derivative work to keep it,
so leave it in place and add your own beside it as you rewrite a file."""

#: Marks the part of the README that only makes sense in the template, and
#: is removed from a generated project. A generated project does not ship
#: ``new_project.py``, so instructions for running it cannot be followed.
#: A marker may be indented: inside the README's Contents list the markers
#: sit as list-item continuation lines, because a comment at column zero is
#: an HTML block that splits the list into separate lists when rendered.
README_TEMPLATE_ONLY = re.compile(
    r"[ \t]*<!-- template-only:start -->\n.*?<!-- template-only:end -->\n",
    re.DOTALL,
)

#: Documents carrying sections marked with the pair above. Every document
#: is scanned, not only the README: the quality guide describes the
#: template's own onboarding test, which a generated project does not ship.
TEMPLATE_ONLY_DOCUMENTS = (
    Path("README.md"),
    Path("docs") / "README-QA-Steps.md",
)

#: Reserved by Windows for devices, at any extension and in any directory.
#: ``open("con")`` talks to the console rather than creating a file, and
#: ``Path("nul").exists()`` is True in an empty directory, so a project by
#: one of these names misbehaves in ways that look nothing like their cause.
WINDOWS_DEVICE_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{digit}" for digit in "123456789"}
    | {f"lpt{digit}" for digit in "123456789"},
)

FRESH_CHANGELOG = """# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project, generated from the Basics QA Python template.
"""


class ProjectError(Exception):
    """Raised when a project cannot be created."""


def to_package_name(project_name: str) -> str:
    """
    Convert a distribution name to its import package name.

    ``my-new-project`` becomes ``my_new_project``, because a distribution
    name may contain hyphens and a Python identifier may not.

    :param project_name: The distribution name.
    :return: The import package name.
    """
    return project_name.replace("-", "_")


def to_title(project_name: str) -> str:
    """
    Convert a distribution name to a human-readable title.

    :param project_name: The distribution name.
    :return: The title, e.g. ``My New Project``.
    """
    return " ".join(word.capitalize() for word in project_name.split("-"))


def to_script_name(project_name: str) -> str:
    """
    Choose the console-script name for a project.

    The distribution name is already a valid command, and reusing it avoids
    the awkward names a blind search-and-replace would otherwise produce.

    :param project_name: The distribution name.
    :return: The console-script name.
    """
    return project_name


def validate_project_name(project_name: str) -> None:
    """
    Reject names that would not survive being turned into a package.

    Four separate ways a name that looks perfectly reasonable goes wrong,
    each of them silent until much later if it is not caught here. A name
    is only ever typed once, and always by someone who has no reason yet to
    know any of this, so the message has to say what to do instead.

    :param project_name: The proposed distribution name.
    :raises ProjectError: If the name is not usable.
    """
    if not PROJECT_NAME_PATTERN.match(project_name):
        msg = (
            f"'{project_name}' is not a valid project name. Use lowercase "
            "letters, digits, and single hyphens, starting with a letter: "
            "for example 'my-new-project'."
        )
        raise ProjectError(msg)
    package = to_package_name(project_name)
    if keyword.iskeyword(package) or keyword.issoftkeyword(package):
        # `from class.cli import ...` is a SyntaxError, so the generated
        # project could not be imported, tested, or run at all.
        msg = (
            f"'{project_name}' becomes the package '{package}', which is a "
            "Python keyword, so no file could ever import it. Add a second "
            f"word: '{project_name}-app', for example."
        )
        raise ProjectError(msg)
    if project_name in WINDOWS_DEVICE_NAMES or package in WINDOWS_DEVICE_NAMES:
        msg = (
            f"'{project_name}' is a name Windows reserves for a device, so "
            "the project directory cannot be created or opened reliably "
            f"there. Add a second word: '{project_name}-app', for example."
        )
        raise ProjectError(msg)
    if package in sys.stdlib_module_names:
        # Shadowing works until something in the dependency tree imports the
        # real module and gets this one, which is a genuinely hard bug to
        # read - far better refused at the only moment it is cheap to fix.
        msg = (
            f"'{project_name}' becomes the package '{package}', which is "
            "the name of a Python standard library module and would hide "
            f"it. Add a second word: '{project_name}-app', for example."
        )
        raise ProjectError(msg)


def rewrite(text: str, project_name: str) -> str:
    """
    Replace every template identifier in a file's text.

    Order matters: the distribution name contains the package name, so it
    is replaced first. Whole-word boundaries prevent a package called
    ``basics`` from corrupting an unrelated word.

    :param text: The original file text.
    :param project_name: The new distribution name.
    :return: The rewritten text.
    """
    package = to_package_name(project_name)
    # Order matters. The distribution name ("basics-qa-python") contains the
    # script name ("basics-qa"), which in turn contains the package name
    # ("basics"), so each must be consumed before the shorter one it contains.
    text = text.replace(TEMPLATE_TITLE, to_title(project_name))
    text = text.replace(TEMPLATE_DISTRIBUTION, project_name)
    text = text.replace(TEMPLATE_SCRIPT, to_script_name(project_name))
    text = re.sub(rf"\b{TEMPLATE_PACKAGE}\b", package, text)
    return re.sub(rf"\b{TEMPLATE_PACKAGE.capitalize()}\b", to_title(project_name), text)


def shipped_top_level_names(template_root: Path) -> set[str]:
    """
    Report the top-level names a generated project will contain.

    Directories keep their name; modules lose the ``.py``, because the name
    they occupy once imported is what a package could collide with.

    :param template_root: The template repository root.
    :return: The names, as they stand before the package is renamed.
    """
    return {
        path.stem if path.suffix == ".py" else path.name
        for path in template_root.iterdir()
        if not is_excluded(path, template_root)
    }


def validate_no_collision(project_name: str, template_root: Path) -> None:
    """
    Reject a name that something the template already ships would clash with.

    ``tests`` is the one people reach for, and it used to abort halfway
    through with a ``FileExistsError`` traceback and a half-built directory
    left behind: renaming the package onto ``tests/`` cannot work when the
    template ships a ``tests/`` of its own.

    :param project_name: The proposed distribution name.
    :param template_root: The template repository root.
    :raises ProjectError: If the name collides with a shipped name.
    """
    package = to_package_name(project_name)
    # The template's own package is excluded: that is the one being renamed,
    # so it is free by the time the new name needs it.
    taken = shipped_top_level_names(template_root) - {TEMPLATE_PACKAGE}
    if package in taken:
        msg = (
            f"'{project_name}' becomes the package '{package}', but every "
            f"generated project already contains a '{package}'. Add a "
            f"second word: '{project_name}-app', for example."
        )
        raise ProjectError(msg)


def validate_destination(destination: Path, template_root: Path) -> None:
    """
    Refuse to create a project inside the template itself.

    A generated project nested in the template is picked up by the
    template's own tooling. Both copies of ``tests/test_cli.py`` are
    collected, and pytest then aborts *every* test module with "import
    file mismatch" - the whole suite, not just the copy - while ruff lints
    the duplicate too. The template looks thoroughly broken, and nothing in
    the output points at the extra directory that caused it.

    :param destination: The directory that would be created.
    :param template_root: The template repository root.
    :raises ProjectError: If the destination lies inside the template.
    """
    resolved = destination.resolve()
    root = template_root.resolve()
    if resolved == root or root in resolved.parents:
        msg = (
            f"{resolved} is inside the template. A project generated there "
            "is collected by the template's own tests and linters, which "
            "then fail in ways that point nowhere near the cause. Leave "
            "--into unset to create it alongside the template instead."
        )
        raise ProjectError(msg)
    parent = destination.parent
    if parent.exists() and not parent.is_dir():
        # Checked here rather than left to copytree, which fails with "the
        # system cannot find the path specified" naming a path that plainly
        # exists - and which the handler in copy_template then blames on the
        # Windows 260-character limit, sending somebody off to shorten a
        # name that was never the problem.
        msg = (
            f"{parent} is a file, not a directory, so nothing can be created "
            "inside it. Pass --into a directory, or leave it unset to create "
            "the project alongside the template."
        )
        raise ProjectError(msg)


def is_excluded(path: Path, root: Path) -> bool:
    """
    Report whether a path must not be copied into a new project.

    :param path: The candidate path.
    :param root: The template root the path lies under.
    :return: True if any part of the relative path is excluded.
    """
    return any(
        part in EXCLUDED_NAMES or part.startswith(EXCLUDED_PREFIXES)
        for part in path.relative_to(root).parts
    )


def copy_template(template_root: Path, destination: Path) -> None:
    """
    Copy the template into a new, empty directory.

    :param template_root: The template repository root.
    :param destination: The directory to create.
    :raises ProjectError: If the destination exists or cannot be written.
    """
    if destination.exists():
        msg = f"{destination} already exists. Choose another name or remove it first."
        raise ProjectError(msg)
    try:
        shutil.copytree(
            template_root,
            destination,
            ignore=lambda directory, names: {
                name for name in names if is_excluded(Path(directory) / name, template_root)
            },
        )
    except PermissionError as error:
        # Before the generic handler below, which it would otherwise reach:
        # PermissionError is an OSError, and being told to shorten a name
        # helps nobody whose only problem is where they are allowed to write.
        msg = (
            f"Could not create {destination} ({error}). Nothing may be "
            "written there. Choose somewhere you own with --into, or grant "
            "yourself write access to that directory first."
        )
        raise ProjectError(msg) from error
    except OSError as error:
        # Long destinations are the common case on Windows, where the path
        # limit is 260 characters and the failure arrives as a bare "cannot
        # find the file specified" naming a path that plainly exists.
        msg = (
            f"Could not create {destination} ({error}). On Windows a path "
            "longer than 260 characters fails this way: choose a shorter "
            "name, or pass --into with a directory closer to the drive root."
        )
        raise ProjectError(msg) from error
    logger.info("Copied the template to %s", destination)


def rename_contents(destination: Path, project_name: str) -> None:
    """
    Rewrite every text file, then rename the package directory.

    :param destination: The generated project root.
    :param project_name: The new distribution name.
    """
    for path in sorted(destination.rglob("*")):
        if not path.is_file():
            continue
        # newline="" on both sides, so line endings pass through this code
        # untranslated and end up LF whatever the host. The defaults
        # translated every written file to CRLF on Windows, and the first
        # commit in the new project - which .gitattributes normalises to
        # LF - then drowned in "CRLF will be replaced by LF" warnings.
        try:
            with path.open(encoding="utf-8", newline="") as file:
                original = file.read()
        except UnicodeDecodeError:  # pragma: no cover - no binary files ship today
            continue
        updated = rewrite(original.replace("\r\n", "\n"), project_name)
        if updated != original:
            with path.open("w", encoding="utf-8", newline="") as file:
                file.write(updated)
    package_directory = destination / TEMPLATE_PACKAGE
    package_directory.rename(destination / to_package_name(project_name))
    logger.info("Renamed the package to %s", to_package_name(project_name))


def reset_project_metadata(destination: Path, project_name: str) -> None:
    """
    Give the new project its own version, ownership, and changelog.

    A generated project starts at 0.1.0; inheriting the template's version,
    release history, authors, or repository URLs would be wrong on every
    count. The lock file carries the version too, and a lock that disagrees
    with ``pyproject.toml`` fails ``uv sync --locked`` - which is the first
    thing ``qa.py setup`` runs.

    :param destination: The generated project root.
    :param project_name: The new distribution name.
    """
    pyproject = destination / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    text = VERSION_PATTERN.sub(f'version = "{INITIAL_VERSION}"', text, count=1)
    text = re.sub(
        ARRAY_PATTERN.format(key="authors"),
        FRESH_AUTHORS,
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        ARRAY_PATTERN.format(key="maintainers"),
        "",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    # newline="\n" on every write below: read_text translates the file to
    # bare "\n" in memory, and writing that back through the platform
    # default turns the whole file CRLF on Windows (see rename_contents).
    pyproject.write_text(URLS_PATTERN.sub("", text, count=1), encoding="utf-8", newline="\n")
    reset_lock_version(destination, project_name)
    (destination / "CHANGELOG.md").write_text(FRESH_CHANGELOG, encoding="utf-8", newline="\n")
    strip_template_only_sections(destination)
    reset_readme_copyright(destination)
    logger.info("Reset %s to version %s", project_name, INITIAL_VERSION)


def reset_lock_version(destination: Path, project_name: str) -> None:
    """
    Point the lock file's entry for the project at the new version.

    ``uv.lock`` records the project itself as one of its packages. Renaming
    alone leaves that entry claiming the template's version, and
    ``uv sync --locked`` then refuses to install anything at all.

    :param destination: The generated project root.
    :param project_name: The new distribution name.
    """
    lock = destination / "uv.lock"
    if not lock.is_file():  # pragma: no cover - the template always ships one
        return
    text = lock.read_text(encoding="utf-8")
    entry = re.compile(
        rf'(^name = "{re.escape(project_name)}"\nversion = )"[^"]*"',
        re.MULTILINE,
    )
    lock.write_text(
        entry.sub(rf'\g<1>"{INITIAL_VERSION}"', text, count=1),
        encoding="utf-8",
        newline="\n",
    )


def strip_template_only_sections(destination: Path) -> None:
    """
    Remove the documentation that only applies to the template itself.

    A generated project ships neither ``new_project.py`` nor the tests that
    drive it, so a section telling its reader to run either describes files
    they do not have - which is exactly the documentation drift the rest of
    this project works to prevent.

    :param destination: The generated project root.
    """
    for relative in TEMPLATE_ONLY_DOCUMENTS:
        document = destination / relative
        if not document.is_file():  # pragma: no cover - the template ships them all
            continue
        text = document.read_text(encoding="utf-8")
        document.write_text(README_TEMPLATE_ONLY.sub("", text), encoding="utf-8", newline="\n")


def reset_readme_copyright(destination: Path) -> None:
    """
    Give the generated project's README its own copyright line.

    Only the README. Every source file keeps the template's notice, which
    the Apache licence requires a derivative work to retain, and which the
    replacement text explains rather than leaving as a mystery.

    Runs after the renaming pass, so the attribution written here cannot
    itself be rewritten.

    :param destination: The generated project root.
    """
    readme = destination / "README.md"
    if not readme.is_file():  # pragma: no cover - the template always ships one
        return
    text = readme.read_text(encoding="utf-8")
    fresh = FRESH_COPYRIGHT.format(year=datetime.now(UTC).year)
    readme.write_text(text.replace(TEMPLATE_COPYRIGHT, fresh, 1), encoding="utf-8", newline="\n")


def run(command: list[str], cwd: Path) -> bool:
    """
    Run a setup command, reporting failure without aborting the whole run.

    A missing ``git`` or ``uv`` should leave a usable project directory and
    a clear message, not a half-built tree and a traceback.

    The failure goes to stderr rather than through ``logger``, which is at
    CRITICAL unless ``-v`` was passed: this message used to be suppressed
    at the default verbosity, so a failed ``uv sync`` printed nothing from
    this script, and "Created ..." followed it as though all was well.

    ``VIRTUAL_ENV`` is dropped from the child environment. This script is
    normally started with ``uv run``, which exports that variable pointing
    at the TEMPLATE's environment; inherited by a command running in the
    new project, it makes every ``uv`` call report that it does not match
    the project environment and is being ignored. The commands still did
    the right thing, but the warning suggests ``--active``, which here
    would mean installing the new project into the template's environment.

    :param command: The command and its arguments.
    :param cwd: The working directory to run it in.
    :return: True if the command succeeded.
    """
    logger.info("Running %s", " ".join(command))
    environment = dict(os.environ)
    environment.pop("VIRTUAL_ENV", None)
    try:
        subprocess.run(command, cwd=cwd, check=True, env=environment)  # noqa: S603
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        sys.stderr.write(f"warning: {' '.join(command)} failed ({error}).\n")
        return False
    return True


def install_environment(destination: Path) -> list[list[str]]:
    """
    Create the virtual environment and install the Git hooks.

    Every command is attempted even after one fails, so a single missing
    tool does not hide what else would have needed doing.

    :param destination: The generated project root.
    :return: The commands that failed, in the order they were tried.
    """
    commands = [
        ["git", "init", "--quiet"],
        ["uv", "sync", "--dev"],
        # A safety net, not the fix. The template's own sources are written
        # so that renaming cannot perturb import order or line length, which
        # is what `--no-install` relies on: it skips these commands, and a
        # project that needed them would start out failing its own gates.
        # --fix before format, the order ruff recommends: sorting imports is
        # itself a linter fix, so formatting first would leave it unformatted.
        ["uv", "run", "ruff", "check", ".", "--fix"],
        ["uv", "run", "ruff", "format", "."],
        ["uv", "run", "pre-commit", "install", "-t", "pre-commit"],
        ["uv", "run", "pre-commit", "install", "-t", "pre-push"],
    ]
    return [command for command in commands if not run(command, destination)]


def create_project(
    project_name: str,
    destination: Path,
    template_root: Path,
    *,
    install: bool = True,
) -> tuple[Path, list[list[str]]]:
    """
    Create a ready-to-use project from the template.

    :param project_name: The new distribution name.
    :param destination: The directory to create.
    :param template_root: The template repository root.
    :param install: Whether to create the environment and install hooks.
    :return: The generated project root, and any setup commands that failed.
    :raises ProjectError: If the name or destination is unusable.
    """
    validate_project_name(project_name)
    validate_no_collision(project_name, template_root)
    validate_destination(destination, template_root)
    copy_template(template_root, destination)
    rename_contents(destination, project_name)
    reset_project_metadata(destination, project_name)
    failures = install_environment(destination) if install else []
    return destination, failures


def resolve_destination(project_name: str, into: Path | None, template_root: Path) -> Path:
    """
    Decide where the new project directory goes.

    :param project_name: The new distribution name.
    :param into: An explicit parent directory, or None for the default.
    :param template_root: The template repository root.
    :return: The directory to create.
    """
    if into is None:
        return template_root.parent / project_name
    # expanduser, because PowerShell does not expand ~ in arguments to
    # native commands the way POSIX shells do. Passed through literally,
    # the documented `--into ~/work` creates a directory actually named
    # "~" - on the operating system most of this template's guard rails
    # exist for.
    return into.expanduser() / project_name


def build_parser() -> argparse.ArgumentParser:
    """
    Build the command-line parser.

    :return: The configured parser.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Create a new project from this template, in a new directory.",
        epilog=(
            "Examples:"
            "\n\n  Create ../my-new-project, installed and ready:"
            "\n    uv run python new_project.py my-new-project"
            "\n\n  Choose where it goes:"
            "\n    uv run python new_project.py my-new-project --into ~/work"
            "\n\n  Copy and rename only, without creating the environment:"
            "\n    uv run python new_project.py my-new-project --no-install"
        ),
    )
    parser.add_argument("project_name", type=str, help="Distribution name, e.g. my-new-project.")
    parser.add_argument(
        "--into",
        type=Path,
        default=None,
        help="Parent directory for the new project (default: alongside this template).",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Skip git init, uv sync, and hook installation.",
    )
    parser.add_argument(
        "-v",
        action="count",
        default=0,
        help="Output verbosity: none, info (-v), debug (-vv).",
    )
    return parser


def main() -> NoReturn:
    """
    Provide the command-line entry point.

    :raises SystemExit: Always; zero on success, one on a reported failure.
    """
    args = build_parser().parse_args()
    logging.basicConfig(format="%(levelname)s | %(message)s", force=True)
    logging.getLogger(__name__).setLevel(
        logging.WARNING if args.v == 0 else logging.INFO if args.v == 1 else logging.DEBUG,
    )
    template_root = Path(__file__).resolve().parent
    destination = resolve_destination(args.project_name, args.into, template_root)
    try:
        created, failures = create_project(
            args.project_name,
            destination,
            template_root,
            install=not args.no_install,
        )
    except ProjectError as error:
        sys.stderr.write(f"error: {error}\n")
        raise SystemExit(1) from error
    sys.stdout.write(f"Created {created}\n")
    if failures:
        # "Created" on its own used to be the last word even when uv had
        # just failed, which reads as success and is the worst possible
        # thing to tell somebody whose environment is not actually there.
        sys.stderr.write(
            "\nSetup did not finish. The directory exists, but run these "
            f"inside {created} before using it:\n",
        )
        for command in failures:
            sys.stderr.write(f"  {' '.join(command)}\n")
        raise SystemExit(1)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
