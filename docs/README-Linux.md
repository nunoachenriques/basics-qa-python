# Debian GNU/Linux

You need two tools: `git` and `uv`. You do not need to install Python
yourself — `uv` downloads and manages the interpreter this project asks for.

## 1. Install Git and curl

```shell
sudo apt install git curl
```

## 2. Install uv

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

The installer puts `uv` in `~/.local/bin` and adds it to your `PATH` in your
shell profile. That change only applies to shells started afterwards.

**Open a new terminal, or run `source ~/.bashrc`.**

## 3. Check both are installed

```shell
git --version
uv --version
```

Both must print a version. If `uv` reports "command not found", your shell has
not picked up the `PATH` change yet: open a new terminal and try again.

Do not skip this step. Every command in this project starts with `uv`, and a
missing `uv` is the most common reason the first one fails.

## Building Python from source

Only needed if you ask `uv` to build an interpreter rather than download one,
which is not the default and not required here:

```shell
sudo apt install build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget llvm libncursesw5-dev xz-utils \
tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

## Next

Back to [Get started](../README.md#get-started).
