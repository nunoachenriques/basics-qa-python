# macOS

## Prerequisites

`python`, `venv`, `pip`, `git`, `pipx`, `pipenv`, `pyenv`, `brew`

### System-Wide

#### Homebrew (`brew`)
```shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### `python`, `venv`, `pip`, `git`

[Python macOS Download and Install](https://www.python.org/downloads/macos/)

```shell
brew install python
```

[Git macOS Download and Install](https://git-scm.com/download/mac)

```shell
brew install git
```

### User Specific

#### `pipx`, `pipenv` 

In order to keep your system's Python untainted, every project should be
contained in a virtual environment. Moreover, use `pipx` to install `pipenv`
in order to keep the application and support libraries isolated from
the general environment. Therefore, install `pipx` first and then `pipenv` for
the environment management.

```shell
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install pipenv
```

#### [`pyenv`](https://github.com/pyenv/pyenv#homebrew-in-macos)

Moreover, install `pyenv` to deal with different Python versions safely.
The [automated installer](https://github.com/pyenv/pyenv#homebrew-in-macos) is
recommended and used this way:

```shell
brew install pyenv
```

Finally, **restart your shell** to instantiate the path!

#### Start

```shell
mkdir project_name
cd project_name
pipenv --python 3.11
```

## [Quality Assurance](../README.md#quality-assurance)
