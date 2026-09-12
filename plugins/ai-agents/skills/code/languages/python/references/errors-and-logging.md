# Errors and logging

## Fail fast

Validate inputs and preconditions at the top of the function. Return early or raise — do not nest the happy path.

```python
def bump(version: str, *, kind: str) -> str:
    if not version:
        raise InvalidVersionError("version is empty")
    if kind not in ALLOWED_KINDS:
        raise InvalidBumpKindError(kind)
    return apply_bump(version, kind=kind)
```

## Exceptions

- Raise a **semantic** exception (`ConfigLoadError`, `InvalidVersionError`), never bare `Exception`.
- Define a small hierarchy under one package-local base when callers need to catch a family of failures.
- Messages are actionable: what failed, which value, what to do next.
- No `except: pass` and no `except Exception:` that swallows the error. Bind only when you use the exception; otherwise `except SpecificError:`.

## Logging

- Use the project's logger (`logging.getLogger(__name__)` or the repo helper). Do not `print` from library code.
- Severity matches the event: DEBUG for traces, INFO for milestones, WARNING for recoverable degradation, ERROR for failures that stop the operation.
- Log context (path, operation, identifiers) — not secrets, tokens, or raw exception objects. Prefer `exc_info=True` on ERROR when the stack matters.

## Keyword-only arguments

Functions with several parameters declare the extras after a bare `*`:

```python
def write_lock(path: Path, *, version: str, branch: str) -> None: ...
```

That prevents positional mix-ups at call sites.
