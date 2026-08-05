# Contributing to configgle

Thanks for helping improve configgle.

## Why this file exists

configgle accepts public changes through a generated public repository while the source tree stays canonical. Contributors need to know how to validate changes locally and which branches are safe to edit.

## Development setup

Requires Python 3.12 and uv.

```bash
uv sync --all-groups
uv run pytest
```

Before opening a pull request, run:

```bash
uv sync --all-groups
uv run ruff check --no-fix --no-cache .
uv run ruff format --check --no-cache .
uv run codespell .
uv run ty check
uv run basedpyright configgle
uv run pytest
uv run python -c "import configgle"
uv build
```

## Public contribution flow

The public repository is synchronized with the canonical source tree. Public
changes should be made on normal contributor branches. After validation, the
sync workflow imports accepted changes back to the source repository for review.

Do not edit generated `configgle/export/*` branches directly.

## Pull request expectations

- Keep changes focused.
- Include tests for behavior changes.
- Update README or docs when public behavior changes.
- Do not include secrets, private credentials, generated caches, or local environment files.
