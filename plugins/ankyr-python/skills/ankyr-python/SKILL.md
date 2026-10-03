---
name: ankyr-python
description: Python 3.12+ syntax, typing, imports, and tooling discipline — builtin generics, no Any, Google docstrings, pathlib, Protocol and factory for OOP patterns, uv/ruff/mypy. Use when writing or reviewing .py/.pyi files.
disable-model-invocation: true
---

# Python

Concrete language-level rules for Python. This is the *how* for the typing and quality intent defined in `engineering`.

## Foundation

Resolve standards in this order: the `AGENT.md` chain (leaf → root), then project rules, then project skills, then this plugin's matching skill if installed. The first source that speaks wins. Consent, review-gate, and security floors always apply. Add language-specific rules only.

## Core rules

- **Builtin generics.** Use `list`, `dict`, `tuple`, `set` — never `typing.List`, `typing.Dict`, or other legacy aliases.
- **Explicit annotations** at every public boundary. Never `Any` or bare `object` — use `TypeAlias`, `NewType`, `Protocol`, or a Pydantic model. See `references/typing-and-models.md`.
- **`dataclass`** for plain structured data; **Pydantic v2** when parsing or validating external input.
- **Google-style docstrings** on public modules, classes, and functions, with `Args:` / `Returns:` / `Raises:` when those apply.
- **Explicit relative imports** within a package; grouped import order (stdlib, third-party, internal); `__all__` for the public surface; do not re-export internals through `__init__.py`. See `references/imports-and-packaging.md`.
- **`pathlib`**, never `os.path`.
- **Fail fast** with early returns. Raise semantic custom exceptions, never bare `Exception`; no silent `except: pass`. See `references/errors-and-logging.md`.
- **OOP shapes.** Express an interface as a `Protocol`, inject collaborators through the constructor, and select the implementation in one factory. A single implementation stays a concrete class or a function. See `references/oop-and-patterns.md`. Function versus object, and which extension axis stays open, are the engineering skill's `references/oop-and-patterns.md`.
- **Hot-loop layout.** When a loop streams one field across many elements, follow the performance skill's `references/data-layout.md` if installed.
- **Keyword-only arguments** after a bare `*` for multi-argument functions. Optional parameters always carry an explicit default.

## When to load references

| Topic | Reference |
|---|---|
| Any-free patterns, `TypeAlias` / `NewType` / `Protocol`, dataclass vs Pydantic v2 | `references/typing-and-models.md` |
| Relative imports, `__all__`, uv and `pyproject.toml` | `references/imports-and-packaging.md` |
| Fail-fast validation, custom exceptions, logging severity, no `print` | `references/errors-and-logging.md` |
| `Protocol`, constructor injection, factory, structured method inputs | `references/oop-and-patterns.md` |
| pytest, pytest-mock, pyfakefs, shared `tests/fixtures/` | `references/testing.md` |

Load a reference only when a rule above surfaces an issue you need patterns for. Do not preload.

## Validation

Before considering work complete, run the project's **Validate** commands from the repository `AGENT.md` and require zero errors.

- **Lint** after Python changes (`ruff`).
- **Type-check** when Validate includes `mypy` (or the project's equivalent).
- **Tests** when behavior or fixtures changed.
- **Audit** when `pyproject.toml` / lockfile changed, and when Validate includes audit at milestones.
