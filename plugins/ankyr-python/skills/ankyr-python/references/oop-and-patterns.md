# OOP and patterns

Use this when a **second real backend** appears for the same concern. One implementation does not get a Protocol — wait for the second same-reason use case (see engineering coupling defaults).

## One concern, one interface

N backends for one job implement one strategy surface (`Protocol`), selected by a single factory. Do not invent N ad-hoc mechanisms (a logging `Handler`, a bolted `StreamHandler`, and an observer that writes `sys.stdout`).

```python
from collections.abc import Mapping
from typing import Protocol


class Renderer(Protocol):
    def emit(self, message: str, *, level: int, fields: Mapping[str, str]) -> None: ...


def select_renderer(config: Config) -> Renderer:
    if config.backend == "github":
        return GitHubRenderer(config)
    if config.backend == "rich":
        return RichRenderer(config)
    return PlainRenderer(config)
```

| Smell | Fix |
|---|---|
| N backends via N mechanisms | One `Renderer` Protocol; factory selects the implementation |
| Bidirectional imports (core ↔ adapter) | Facade depends on the Protocol; adapters never import core view code |
| Collaborator reaches `view._observers`, `_spinning`, `_refresh()` | If a collaborator needs it, put it on the public Protocol |
| Extra handlers bolted onto a shared process logger | Composition + delegation through one `Reporter` facade |
| `setLogRecordFactory()` (or similar) at import time | Wire in an explicit `install(config)` setup function |
| `is_github_actions()` (or host checks) scattered at call sites | Centralize environment variation in `select_renderer()` |
| Host literals (log file name, logger name) hardcoded in the library | Constructor `Config` / `Theme` dataclasses so the package is extractable |

## Dependency direction

```
facade / Reporter  -->  Renderer (Protocol)
                              ^
              rich / plain / github adapters
```

- Call sites talk to the facade. The facade holds a `Renderer` and delegates.
- Adapter modules may import shared types and the Protocol. Core view code must not import a concrete adapter.
- Do not reach into collaborator `_private` attributes. Promote what collaborators need onto the public surface.

## Structured data on the seam

Protocol methods accept structured data — `Mapping[str, str]`, level ints, plain text. Never pre-rendered or pre-wrapped strings, and never an explicit width from the caller. Otherwise the abstraction silently strips a backend's ability to lay itself out (for example Rich reflowing from `console.width`).

```python
# Forbidden — caller owns layout
renderer.emit(panel.render(width=80))

# Prefer — backend owns layout
renderer.emit("done", level=logging.INFO, fields={"step": "publish"})
```

## Composition and explicit setup

- Prefer composition and delegation over bolting extras onto a shared global (root logger, process-wide factories).
- Import-time side effects that reconfigure the process are forbidden. Expose `install(config: Config) -> Reporter` (or equivalent) and call it from the host's entrypoint.
- Host-specific values (file paths, logger names, theme colors) belong in constructor `Config` / `Theme` dataclasses from day one when the package may later leave the host repo.
