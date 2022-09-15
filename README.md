[![Apache 2.0 License](https://img.shields.io/badge/license-Apache%202.0-blue.svg "Apache 2.0 License")](http://www.apache.org/licenses/LICENSE-2.0.html)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![imports - isort](https://img.shields.io/badge/imports-isort-ef8336.svg)](https://github.com/pycqa/isort)
[![code style - black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

# Basics on Quality Assurance in Python

The basics towards better software with Python by means of development best
practices. A work in progress with a continuous improvement mindset.

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

**NOTICE:** black and isort may have conflits, since they both enforce styles in the code (https://pycqa.github.io/isort/docs/configuration/black_compatibility.html). To ensure isort follows the same style as black, add a line in the configuration file as showed below:

`pyproject.toml`

```toml
[tool.isort]
profile = "black"
```

```shell
pipenv run isort .
pipenv run black .
```

### Code Style Enforcement

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

### Git Hooks

`pre-commit`

Putting it all together, i.e., automating while distinguishing Git `commit`
fast-checking requirement from the Git `push` more time-consuming possible
actions such as `pytest` (including coverage) and `pipenv check`.

```shell
pipenv install pre-commit --dev
```

`.pre-commit-config.yaml`

**NOTICE:** The `pipenv check` and the `pytest` (including coverage) are
configured to run only on Git `push`!

```yaml
repos:
  - repo: local
    hooks:

      ### CODE FORMATTING

      - id: isort
        name: isort
        stages: [ commit ]
        language: system
        entry: pipenv run isort .
        types: [ python ]

      - id: black
        name: black
        stages: [ commit ]
        language: system
        entry: pipenv run black .
        types: [ python ]

      ### CODE STYLE ENFORCEMENT

      - id: flake8
        name: flake8
        stages: [ commit ]
        language: system
        entry: pipenv run flake8p .
        types: [ python ]

      ### TYPE CHECKING

      - id: mypy
        name: mypy
        stages: [ commit ]
        language: system
        entry: pipenv run mypy .
        types: [ python ]
        pass_filenames: false

      ### SECURITY

      - id: bandit
        name: bandit
        stages: [ commit ]
        language: system
        entry: pipenv run bandit -c pyproject.toml -r .
        types: [ python ]

      - id: check
        name: check
        stages: [ push ]
        language: system
        entry: pipenv check
        types: [ python ]

      ### TESTING

      - id: pytest
        name: pytest
        stages: [ push ]
        language: system
        entry: pipenv run pytest
        types: [ python ]
        pass_filenames: false
```

```shell
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```

It may be run without the Git `commit` hook triggering. This presents a 
useful way of testing the `.pre-commit-config.yaml` calls and also the
configuration in `pyproject.toml`:

```shell
pipenv run pre-commit run --all-files --hook-stage commit
pipenv run pre-commit run --all-files --hook-stage push
```

## Wrap-up

All the [prerequisites](#prerequisites) must be accomplished (by following
the above instructions or by means of a previous project installation).
The project files for [quality assurance](#quality-assurance) must be in place
(by means of unzipping a download from
[GitHub](https://github.com/nunoachenriques/basics-qa-python)).

```shell
pipenv install --dev
git init
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```

Later, you may add your local Git-based repository to a remote, such as,
[GitLab](https://gitlab.com).

```shell
git remote add origin <URL>
```

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
