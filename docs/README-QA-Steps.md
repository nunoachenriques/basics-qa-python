# Quality Assurance

This document explains the steps required to install and configure all the
required elements of the quality assurance in place for any Python project.
Moreover, includes the configuration details for the `pyproject.toml` and
`.pre-commit-config.yaml` files regarding code quality, security, and testing.

```text
pipx
  |
  | isolated install
  v
pipenv (virtual environment installs)
  |
  |-uses-> pyenv
  |
  |-uses-> pip
  |                 |-pre-commit-> black -> ruff -> mypy
  |-> pre-commit ---|
                    |-pre-push-> pipenv check -> pytest + coverage
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
/build/
/dist/
/*.egg-info/
```

### Code Formatting

`black`

```shell
pipenv install black --dev
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
pipenv run black .
```

### Code Style Enforcement

`ruff`

Actually, below `ruff` configuration (`select`) includes security and some code
formatting.

```shell
pipenv install ruff --dev --pre
```

`pyproject.toml`

```toml
[tool.ruff]
fix = true
select = [
    "A", "B", "C", "D", "E", "F", "G", "I", "N", "Q", "S", "T", "W", "ANN",
    "ARG", "BLE", "COM", "DJ", "DTZ", "EM", "ERA", "EXE", "FBT", "ICN", "INP",
    "ISC", "NPY", "PD", "PGH", "PIE", "PL", "PT", "PTH", "PYI", "RET", "RSE",
    "RUF", "SIM", "SLF", "TCH", "TID", "TRY", "UP", "YTT",
]
ignore = ["D203", "D212", "D400", "D415"]
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

[tool.ruff.mccabe]
max-complexity = 10

```

```shell
pipenv run ruff check .
```

### Type Checking

`mypy`

```shell
pipenv install mypy --dev
```

`pyproject.toml`

```toml
[tool.mypy]
files = "."
ignore_missing_imports = true
```

```shell
pipenv run mypy .
```

### Security

`pipenv check`

`pyproject.toml`

```toml
### SECURITY

# NO CONFIGURATION REQUIRED. INCLUDED IN `ruff` (e.g., `bandit`) AND `pipenv check`.
```

```shell
pipenv check
```

### Testing

`pytest`, `pytest-cov`

```shell
pipenv install pytest pytest-cov --dev
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
pipenv run pytest
```

### Git Hooks

`pre-commit`

Putting it all together, i.e., automating while distinguishing Git `commit`
fast-checking requirement from the Git `push` more time-consuming possible
actions such as `pytest` (including coverage) and `pipenv check`.

```shell
pipenv install pre-commit --dev
```

`.pre-commit-config.yaml`

**NOTICE:** The `pipenv check` and the `pytest` (including coverage) are
configured to run only on Git `push`!

```yaml
repos:
  - repo: local
    hooks:

      ### CODE FORMATTING

      - id: black
        name: black
        stages: [ commit ]
        language: system
        entry: pipenv run black .
        types: [ python ]

      ### CODE STYLE ENFORCEMENT

      - id: ruff
        name: ruff
        stages: [ commit ]
        language: system
        entry: pipenv run ruff check .
        types: [ python ]

      ### TYPE CHECKING

      - id: mypy
        name: mypy
        stages: [ commit ]
        language: system
        entry: pipenv run mypy .
        types: [ python ]
        pass_filenames: false

      ### SECURITY

      - id: check
        name: check
        stages: [ push ]
        language: system
        entry: pipenv check
        types: [ python ]

      ### TESTING

      - id: pytest
        name: pytest
        stages: [ push ]
        language: system
        entry: pipenv run pytest
        types: [ python ]
        pass_filenames: false
```

```shell
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```

## Back to [README Wrap-up](../README.md#wrap-up)
