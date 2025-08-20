# Quality Assurance

This document explains the steps required to install and configure all the
required elements of the quality assurance in place for any Python project.
Moreover, includes the configuration details for the `pyproject.toml` and
`.pre-commit-config.yaml` files regarding code quality, security, and testing.

```text
uv (virtual environment and project management)
  |
  |                 |-pre-commit-> black -> ruff -> mypy
  |-> pre-commit ---|
                    |-pre-push-> pytest + coverage
```

**NOTICE:** Using UNIX shell commands in a Debian GNU/Linux Bash shell.
Adapt accordingly your Operating System.

## Step by Step

**NOTICE:** Make sure you've completed the
[Prerequisites](../README.md#prerequisites) for your operating system case!

### Clean and Tidy

#### `/.gitignore`

Avoid committing and pushing generated, private, local files. More exclusions
may be added at your discretion.

```shell
/**/__pycache__/
/.idea/
/.venv/
/build/
/dist/
/*.egg-info/
```

### Code Formatting

`black`

```shell
uv add black --dev
```

`pyproject.toml`

```toml
[tool.black]
# https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html#line-length
line-length = 100
# Assume Python 3.11 (see `ruff`)
target-version = ['py311']
extend-exclude = '''
(
  ^/notebooks
  | ^/.pytest_cache
  | ^/.ruff_cache
)
'''
```

```shell
uv run black .
```

### Code Style Enforcement

`ruff`

Actually, below `ruff` configuration (`select`) includes security and some code
formatting.

```shell
uv add ruff --dev
```

`pyproject.toml`

```toml
[tool.ruff]
fix = true
exclude = [
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
]
# Useful for pre-commit: https://beta.ruff.rs/docs/settings/#force-exclude
force-exclude = true
# https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html#line-length
line-length = 100
# Allow unused variables when underscore-prefixed.
# dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"
# Assume Python 3.11 (see `black`)
target-version = "py311"

[tool.ruff.lint]
select = [
    "A", "B", "C", "D", "E", "F", "G", "I", "N", "Q", "S", "T", "W", "ANN",
    "ARG", "BLE", "COM", "DJ", "DTZ", "EM", "ERA", "EXE", "FBT", "ICN", "INP",
    "ISC", "NPY", "PD", "PGH", "PIE", "PL", "PT", "PTH", "PYI", "RET", "RSE",
    "RUF", "SIM", "SLF", "TCH", "TID", "TRY", "UP", "YTT",
]
ignore = ["D203", "D212", "D400", "D415"]
mccabe.max-complexity = 10
```

```shell
uv run ruff check .
```

### Type Checking

`mypy`

```shell
uv add mypy --dev
```

`pyproject.toml`

```toml
[tool.mypy]
files = "."
ignore_missing_imports = true
```

```shell
uv run mypy .
```

### Security

`pyproject.toml`

```toml
### SECURITY

# NO CONFIGURATION REQUIRED. INCLUDED IN `ruff` (e.g., `bandit`).
```

### Testing

`pytest`, `pytest-cov`

```shell
uv add pytest pytest-cov --dev
```

`pyproject.toml`

```toml
[tool.pytest.ini_options]
addopts = "--cov --cov-fail-under=100"

[tool.coverage.run]
source = ["."]

[tool.coverage.report]
show_missing = true
omit = ["*/tests/*"]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:"
]
```

```shell
uv run pytest
```

### Git Hooks

`pre-commit`

Putting it all together, i.e., automating while distinguishing Git `commit`
fast-checking requirement from the Git `push` more time-consuming possible
actions such as `pytest` (including coverage).

```shell
uv add pre-commit --dev
```

`.pre-commit-config.yaml`

**NOTICE:** The `pytest` (including coverage) is configured to run only on
Git `push`!

```yaml
repos:
  - repo: local
    hooks:

      ### CODE FORMATTING

      - id: black
        name: black
        stages: [ pre-commit ]
        language: system
        entry: uv run black .
        types: [ python ]

      ### CODE STYLE ENFORCEMENT + SECURITY

      - id: ruff
        name: ruff
        stages: [ pre-commit ]
        language: system
        entry: uv run ruff check .
        types: [ python ]

      ### TYPE CHECKING

      - id: mypy
        name: mypy
        stages: [ pre-commit ]
        language: system
        entry: uv run mypy .
        types: [ python ]
        pass_filenames: false

      ### TESTING

      - id: pytest
        name: pytest
        stages: [ pre-push ]
        language: system
        entry: uv run pytest
        types: [ python ]
        pass_filenames: false
```

```shell
uv run pre-commit install -t pre-commit
uv run pre-commit install -t pre-push
```

## Back to [README Wrap-up](../README.md#wrap-up)
