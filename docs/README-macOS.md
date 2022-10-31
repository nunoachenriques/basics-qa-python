# !!!TODO!!! macOS

## Prerequisites

`python`, `venv`, `pip`, `git`, `pipx`, `pipenv`, `pyenv`

### System-Wide

#### [Linux build environment (suggested by `pyenv`)](https://github.com/pyenv/pyenv/wiki#suggested-build-environment)

**NOTICE:** Check https://github.com/pyenv/pyenv/wiki#suggested-build-environment
for other Operating Systems (e.g., macOS, Windows).

```shell
sudo apt install build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils \
tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

#### `python`, `venv`, `pip`, `git`

```shell
sudo apt install python3-venv python3-pip python3-dev git
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

#### [`pyenv`](https://github.com/pyenv/pyenv)

Moreover, install `pyenv` to deal with different Python versions safely.
The [automated installer](https://github.com/pyenv/pyenv-installer) is
recommended and used this way:

```shell
curl https://pyenv.run | bash
```

Edit `~/.bashrc` and add the following:

```shell
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
```

Finally, restart your shell to instantiate the path, and call the doctor to
be safe (check for issues):

```shell
exec $SHELL
```
```shell
pyenv doctor
```

#### Start

```shell
mkdir project_name
cd project_name
pipenv --python 3.10
```

## [Quality Assurance](../README.md#quality-assurance)
