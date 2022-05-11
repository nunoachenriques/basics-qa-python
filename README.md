[![Apache 2.0 License](https://img.shields.io/badge/license-Apache%202.0-blue.svg "Apache 2.0 License")](http://www.apache.org/licenses/LICENSE-2.0.html)
[![imports - isort](https://img.shields.io/badge/imports-isort-ef8336.svg)](https://github.com/pycqa/isort)
[![code style - black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

# Basics on Quality Assurance in Python

The basics towards better software with Python by means of development best
practices.

**WARNING:** Work in Progress... NOT COMPLETED, YET...!

**NOTICE:** Using UNIX shell commands in a Debian GNU/Linux Bash shell.
Adapt accordingly your Operating System.

## Content

* [Prerequisites](#prerequisites)
* [Quality Assurance](#quality-assurance)
* [Wrap-up](#wrap-up)
* [License](#license)

## Prerequisites

`python`, `venv`, `pip`, `git`, `pipx`, `pipenv`, `pyenv`

### System-Wide

#### [build environment](https://github.com/pyenv/pyenv/wiki#suggested-build-environment)

**NOTICE:** Check https://github.com/pyenv/pyenv/wiki#suggested-build-environment
for other Operating Systems (e.g., macOS).

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

## Quality Assurance

**NOTICE:** Make sure you've completed [Prerequisites](#prerequisites) and
[Start](#start)!

### Clean and Tidy

#### `/.gitignore`

Avoid committing and pushing generated, private, local files.

```shell
/**/__pycache__/
/.idea/
/build/
/dist/
/*.egg-info/
```

#### `/.dockerignore`

Avoid bloating your docker with unnecessary files.

```shell
/k8s/
/test/
/**/__pycache__/
/.idea/
/build/
/dist/
/*.egg-info/
.git
.gitignore
.gitlab-ci.yml
.dockerignore
.pre-commit-config.yaml
Dockerfile
Pipfile*
docker_build.sh
docker_registry.sh
package_registry.sh
qa.sh
setup.py
```

### Code Formatting

`isort`, `black`

```shell
pipenv install isort black --dev
```

`pyproject.toml`

```toml
[tool.isort]
line_length = 120
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
honor_noqa = true
```

```shell
pipenv run isort .
pipenv run black .
```

### Style Enforcement

`flake8` + `pyproject.toml` support = `flake8p`

```shell
pipenv install Flake8-pyproject --dev
```

`pyproject.toml`

```toml
[tool.flake8]
max-line-length = 120
ignore = ["E203", "E266", "E501", "W503"]
max-complexity = 18
select = ["B", "C", "E", "F", "W", "T4"]
```

```shell
pipenv run flake8p .
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

`bandit`, `pipenv check`

```shell
pipenv install bandit[toml] --dev
```

`pyproject.toml`

```toml
[tool.bandit]
assert_used.skips = "*/tests/*"
```

```shell
pipenv run bandit -c pyproject.toml -r .
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

TODO

### Documentation

TODO

### Git Hooks

`pre-commit`

TODO

## Wrap-up

TODO

## License

Copyright 2022 Nuno A. C. Henriques https://nunoachenriques.net

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
