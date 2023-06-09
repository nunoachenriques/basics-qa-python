[![Apache 2.0 License](https://img.shields.io/badge/license-Apache%202.0-blue.svg "Apache 2.0 License")](http://www.apache.org/licenses/LICENSE-2.0.html)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![imports - isort](https://img.shields.io/badge/imports-isort-ef8336.svg)](https://github.com/pycqa/isort)
[![code style - black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

# Basics on Quality Assurance in Python

The basics towards better software with Python by means of development best
practices. A work in progress with a continuous improvement mindset.

There are some basic system-wide prerequisites such as `python`, `venv`, `pip`,
and `git`. Next, we will install `pipx` at user level and use this tool
to install `pipenv` isolated from the general environment. Finally, `pyenv`
is installed to assure that any Python version requested is available and
easily switched to (independently of the system Python, it uses a collection
of scripts).

![Pipenv and pre-commit flow diagram](docs/pipenv-pre-commit.jpg)
<figcaption><code>pipenv</code> and <code>pre-commit</code> flow diagram.</figcaption>

**NOTICE:** Using UNIX shell commands in a Debian GNU/Linux Bash shell.
Adapt accordingly your Operating System.

## Content

* [Prerequisites](#prerequisites)
* [Quality Assurance](#quality-assurance)
* [Wrap-up](#wrap-up)
* [License](#license)

## Prerequisites

**[Linux](docs/README-Linux.md)**

**[macOS](docs/README-macOS.md)**

**[Windows](docs/README-Windows.md)**

## Quality Assurance

**NOTICE:** Make sure you've completed the [Prerequisites](#prerequisites) for
your operating system case!

**SHORTCUT:** If you've completed the [Prerequisites](#prerequisites) AND
NOT interested in the details then you may skip this step-by-step guide and
jump to the next section [Wrap-up](#wrap-up).

**[Quality Assurance Step by Step](docs/README-QA-Steps.md)**

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

How to test the `.pre-commit-config.yaml` calls and also the configuration in
`pyproject.toml`:

```shell
pipenv run pre-commit run --all-files --hook-stage commit
pipenv run pre-commit run --all-files --hook-stage push
```

Later, you may add your local Git-based repository to a newly created project
with an `<URL>` provided by a remote (e.g., [GitLab](https://gitlab.com)).

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
