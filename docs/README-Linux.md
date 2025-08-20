# Debian GNU/Linux

## Prerequisites

`curl`, `git`, `python` (`dev`, `pip`, `venv`), `uv`

### System-Wide

#### `curl` + Linux build environment

```shell
sudo apt install build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils \
tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

#### `git`, `python` (`dev`, `pip`, `venv`)

```shell
sudo apt install git python3-venv python3-pip python3-dev
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
