[![Apache 2.0 License](https://img.shields.io/badge/license-Apache%202.0-blue.svg "Apache 2.0 License")](http://www.apache.org/licenses/LICENSE-2.0.html)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![code style - black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)

# Basics on Quality Assurance in Python

The basics towards better software with Python by means of development best
practices. A work in progress with a continuous improvement mindset.

There are some basic system-wide prerequisites such as `python`, `venv`, `pip`,
and `git`. Next, we will install `pipx` and use this tool to install `pipenv`
isolated from the general environment. Finally, `pyenv` is installed to assure
that any Python version requested is available and easily switched to
(independently of the system Python, it uses a collection of scripts).

**NOTICE:** Using UNIX shell commands in a Debian GNU/Linux Bash shell.
Adapt accordingly your Operating System.

## Content

* [Use](#use)
* [Develop](#develop)
  * [Fork](#fork)
  * [Prerequisites](#prerequisites)
  * [Quality Assurance](#quality-assurance)
  * [Wrap-up](#wrap-up)
  * [Run](#run)
* [History](#history)
* [License](#license)

## Use

**_TODO_**

## Develop

https://github.com/nunoachenriques/basics-qa-python

### Fork

In order to facilitate pull requests if you want to contribute then go to
https://github.com/nunoachenriques/basics-qa-python and hit **fork**!

### Prerequisites

**[Linux](docs/README-Linux.md)**

**[macOS](docs/README-macOS.md)**

**[Windows](docs/README-Windows.md)**

### Quality Assurance

**NOTICE:** Make sure you've completed the [Prerequisites](#prerequisites) for
your operating system case!

**SHORTCUT:** If you've completed the [Prerequisites](#prerequisites) AND
NOT interested in the details then you may skip this step-by-step guide and
jump to the next section [Wrap-up](#wrap-up).

**[Quality Assurance Step by Step](docs/README-QA-Steps.md)**

### Wrap-up

All the [prerequisites](#prerequisites) must be accomplished (by following
the above instructions or by means of a previous project installation).
The project files for [quality assurance](#quality-assurance) must be in place
by one of two options:

 * **Contributing** to the Basics QA Python project.

   **First**, a **[fork](#fork)** of the remote. **Second**, the **clone** in
   your own repository:

   ```shell
   git clone git@github.com:{YOUR_OWN_USER}/basics-qa-python.git
   ```
 
   ```shell
   cd basics-qa-python
   pipenv install --dev
   pipenv run pre-commit install -t pre-commit
   pipenv run pre-commit install -t pre-push
   ```
   
   **Third**, carry on coding, committing, and issuing pull requests to the main
   project.

   
 * **Developing a new project** using this quality assurance.

   **First**, **use the template** in the remote or **unzip a download** from
   [Basics QA Python GitHub](https://github.com/nunoachenriques/basics-qa-python).
   **Second**, choose **your own project name**:

   ```shell
   mv basics-qa-python YOUR-OWN-PROJECT-NAME
   cd YOUR-OWN-PROJECT-NAME
   pipenv install --dev
   git init
   pipenv run pre-commit install -t pre-commit
   pipenv run pre-commit install -t pre-push
   ```

   **Third**, custom everything you see fit (NOTICE: change basics-qa-python
   references and URL to your owns) then code, commit, and push to a remote
   if you've added your local Git-based repository to a newly created project
   with an `<URL>` provided by a remote (e.g., [GitLab](https://gitlab.com)).

   ```shell
   git remote add origin <URL>
   ```

How to test the `.pre-commit-config.yaml` calls and also the configuration in
`pyproject.toml`:

```shell
pipenv run pre-commit run --all-files --hook-stage commit
pipenv run pre-commit run --all-files --hook-stage push
```

### Run

A command-line interface is available and ready to run the application:

```shell
pipenv run python app_cli.py
```

## History

It started in 2022 with an urge to compile some basics of quality assurance
for application development in Python. The motivation was and is to simplify,
automate, and guarantee a proper normalised and more secure code.

By me [Nuno A. C. Henriques](https://github.com/nunoachenriques) and by
[Alexandre Almeida](https://github.com/alexandre1-almeida)'s precious
contributions in code and vivid discussions!

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
