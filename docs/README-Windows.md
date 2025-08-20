# Windows

## Prerequisites

`git`, `python` (`dev`, `pip`, `venv`), `uv`

### System-Wide

#### `git`, `python` (`dev`, `pip`, `venv`)

[Python Windows Download and Install](https://www.python.org/downloads/windows/)

[Git Windows Download and Install](https://git-scm.com/download/win)

**Restart your Windows!**

### User Specific

The unified tool for Python project virtual environment management:
[uv](https://docs.astral.sh/uv/getting-started/installation/)

#### `uv`

```shell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Restart your terminal (e.g., Windows PowerShell)!**

#### Start

```shell
mkdir project_name
cd project_name
uv sync
```

## Back to [README Quality Assurance](../README.md#quality-assurance)
