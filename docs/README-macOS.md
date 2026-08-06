# macOS

You need two tools: `git` and `uv`. You do not need to install Python
yourself — `uv` downloads and manages the interpreter this project asks for.

## 1. Install Homebrew

Skip this if you already have it.

```shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## 2. Install Git

macOS ships a Git, and the Xcode command line tools provide one too. For an
up-to-date version:

```shell
brew install git
```

## 3. Install uv

```shell
brew install uv
```

Or, without Homebrew:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

The standalone installer puts `uv` in `~/.local/bin` and adds it to your
`PATH` in your shell profile, which only applies to shells started afterwards.

**Open a new terminal.**

## 4. Check both are installed

```shell
git --version
uv --version
```

Both must print a version. If `uv` reports "command not found", your shell has
not picked up the `PATH` change yet: open a new terminal and try again.

Do not skip this step. Every command in this project starts with `uv`, and a
missing `uv` is the most common reason the first one fails.

## Next

Back to [Get started](../README.md#get-started).
