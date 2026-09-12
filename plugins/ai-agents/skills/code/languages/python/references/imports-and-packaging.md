# Imports and packaging

## Relative imports inside the package

Prefer explicit relative imports within your own package (`from ..core.utils import parse_event`). Implicit absolute imports of internal modules break under CLI and pytest collection.

Imports must work from:

- The IDE
- CLI entry points
- `pytest` without setting `PYTHONPATH`
- CI runners

## Grouping

1. Standard library
2. Third-party
3. Internal

`ruff` is the sorter. Do not add `isort` unless the project already uses it.

## Public surface

- Do not re-export internals through `__init__.py` just to shorten import paths.
- Use `__all__` on shared modules that *do* define a public API.

## Tooling

- **uv** for installs, lockfiles, and running tools (`uv run …`). Do not add a parallel pip / `requirements.txt` workflow.
- **`pyproject.toml`** is the project config. Do not introduce `setup.py` or split tool configs unless the repo already has them.
- Pin via `uv.lock`. Do not hand-edit the lockfile.

Project-specific Validate commands (ruff, mypy, pytest, audit) live in the repository `AGENT.md`.
