# Windows

You need two tools: `git` and `uv`. You do not need to install Python
yourself — `uv` downloads and manages the interpreter this project asks for.

## 1. Install Git

[Download and run the installer](https://git-scm.com/download/win).

## 2. Install uv

In PowerShell:

```shell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

The installer puts `uv` in `%USERPROFILE%\.local\bin` and adds it to your
`PATH`. That change only applies to terminals opened afterwards.

**Close this terminal and open a new one.**

## 3. Check both are installed

```shell
git --version
uv --version
```

Both must print a version. If `uv` reports that the term is not recognised,
the `PATH` change has not reached your shell yet: open a new terminal and try
again. If it still fails, add `%USERPROFILE%\.local\bin` to your `PATH`
manually and reopen the terminal.

Do not skip this step. Every command in this project starts with `uv`, and a
missing `uv` is the most common reason the first one fails.

## Next

Back to [Get started](../README.md#get-started).
