# Contributing

Thanks for considering a contribution!

## Before you start

- Install the prerequisites for your operating system:
  [Linux](docs/README-Linux.md), [macOS](docs/README-macOS.md), or
  [Windows](docs/README-Windows.md).
- Skim [QA, step by step](docs/README-QA-Steps.md) to see
  which tools run and why.

## Workflow

1. Fork the repository on GitHub and clone your fork.

2. Set up the environment and Git hooks:

   ```shell
   uv run python qa.py setup
   ```

   Git does not clone `.git/hooks`, so until you run this your checkout has no
   local checks at all.

3. Create a branch for your change.

4. Make the change, in small focused commits. One logical change per commit is
   easier to review and to revert.

5. Check your work:

   ```shell
   uv run python qa.py check
   ```

   That runs exactly what the pipeline runs. The hooks also run automatically:
   formatting, linting, and types on every commit; tests and the dependency
   audit on every push.

6. Open a pull request.

## Commit messages

A short title, then one paragraph explaining why the change was needed. That
is enough.

```text
fix(cli): show warnings at the default verbosity

The default level was CRITICAL, so an application built on this skeleton
lost its own warning and error messages unless the user passed -v. WARNING
keeps the default run quiet while letting real problems through.
```

Use a [Conventional Commits](https://www.conventionalcommits.org/) prefix
(`feat`, `fix`, `docs`, `build`, `ci`, `test`, `refactor`) so the changelog
can be assembled from the history. Describe the change and the reason for it;
leave out who got it wrong and how it was found.

## Style expectations

- Public functions and classes need type annotations and docstrings, enforced
  by ruff's `ANN` and `D` rule families.
- Tests use plain `assert`, which pytest rewrites into a readable diff on
  failure.
- Tests run in a random order, so none may rely on another having run first.
  A failure prints the seed that produced it; pass that value back as
  `--randomly-seed=` to replay the same order.
- Where a rule holds for every input rather than for one case, write it as a
  property with `hypothesis` rather than a longer list of examples. There is a
  worked example in `tests/test_qa.py`. When a property finds a failure, fix
  it and add the case as a parametrised example as well — Hypothesis's own
  record of it is a local cache that Git never sees.
- Keep coverage at 100%. If a line genuinely cannot be tested, exclude it
  explicitly in `[tool.coverage.report]` rather than writing a test that
  asserts nothing.

## Reporting issues

Please open an issue with a clear description and, where possible, a minimal
reproduction.

## Changes

Notable changes are tracked in [CHANGELOG.md](CHANGELOG.md).
