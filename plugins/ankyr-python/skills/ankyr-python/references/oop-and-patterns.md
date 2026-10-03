# OOP in Python

How to express the engineering OOP patterns in Python. The meaning of each pattern — interface, delegation, orchestration, strategy, factory, adapter — and when to enforce it lives in the engineering skill's `references/oop-and-patterns.md` when that skill is installed. That reference also owns when a function beats an object and the Expression Problem. This page is the syntax.

Use a `Protocol` when a second real variant of the same concern exists. One implementation stays a concrete class or a function.

## Interface

`Protocol` is the interface: structural, no shared base class. Use `abc.ABC` only when subclasses must share implementation. Do not inherit from a base just to mark a type.

```python
from collections.abc import Mapping
from typing import Protocol


class Exporter(Protocol):
    def export(self, record: Mapping[str, str], *, level: int) -> None: ...
```

Methods take structured values: mappings, level ints, plain text. They do not take a pre-rendered string or a caller-supplied width. The implementation owns layout.

## Delegation and the factory

Pass collaborators into the constructor. That is delegation. A module-level factory is the only place that selects the implementation.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ExportConfig:
    """Host values. A dataclass is the data object, not a pattern."""

    kind: str
    destination: str


class Publish:
    def __init__(self, exporter: Exporter) -> None:
        self._exporter = exporter

    def run(self, record: Mapping[str, str]) -> None:
        self._exporter.export(record, level=20)


class LocalExporter:
    def __init__(self, destination: str) -> None:
        self._destination = destination

    def export(self, record: Mapping[str, str], *, level: int) -> None:
        write_local(self._destination, record, level=level)


class RemoteExporter:
    def __init__(self, destination: str) -> None:
        self._destination = destination

    def export(self, record: Mapping[str, str], *, level: int) -> None:
        write_remote(self._destination, record, level=level)


def select_exporter(config: ExportConfig) -> Exporter:
    if config.kind == "remote":
        return RemoteExporter(config.destination)
    return LocalExporter(config.destination)
```

`Publish` sequences the step and forwards the work. `LocalExporter` and `RemoteExporter` are the two implementations. Call sites call `select_exporter` once and then talk to `Publish`. They do not branch on `config.kind`.

A `@dataclass` holds data you construct yourself. It is not an interface, a strategy, or a service.
