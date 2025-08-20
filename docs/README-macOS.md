# macOS

## Prerequisites

`brew`, `git`, `python` (`dev`, `pip`, `venv`), `uv`

### System-Wide

#### Homebrew (`brew`)
```shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### `git`, `python` (`dev`, `pip`, `venv`)

[Python macOS Download and Install](https://www.python.org/downloads/macos/)

```shell
brew install python
```

[Git macOS Download and Install](https://git-scm.com/download/mac)

```shell
brew install git
```

### User Specific

The unified tool for Python project virtual environment management:
[uv](https://docs.astral.sh/uv/getting-started/installation/)

#### `uv`

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Start

```shell
mkdir project_name
cd project_name
uv sync
```

## Back to [README Quality Assurance](../README.md#quality-assurance)
