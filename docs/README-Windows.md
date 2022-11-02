# Windows

## Prerequisites

`python`, `venv`, `pip`, `git`, `pipx`, `pipenv`, `pyenv`

### System-Wide

#### `python`, `venv`, `pip`, `git`

[Python Windows Download and Install](https://www.python.org/downloads/windows/)

[Git Windows Download and Install](https://git-scm.com/download/win)

**Restart your Windows!**

### User Specific

#### `pipx`, `pipenv` 

In order to keep your system's Python untainted, every project should be
contained in a virtual environment. Moreover, use `pipx` to install `pipenv`
in order to keep the application and support libraries isolated from
the general environment. Therefore, install `pipx` first and then `pipenv` for
the environment management.

```shell
python -m pip install --user pipx
python -m pipx ensurepath
```

**Restart your terminal (e.g., Windows PowerShell)!**

```shell
pipx install pipenv
```

#### `pyenv`

Moreover, install `pyenv` to deal with different Python versions safely.
The [automated installer](https://github.com/pyenv-win/pyenv-win) is
recommended and used this way:

Windows PowerShell **Run as Administrator** 

```shell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

**Restart your terminal (e.g., Windows PowerShell)!**

#### Start

```shell
mkdir project_name
cd project_name
pipenv --python 3.11
```

## [Quality Assurance](../README.md#quality-assurance)
