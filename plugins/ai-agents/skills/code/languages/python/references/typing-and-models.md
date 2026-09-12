# Typing and models

## Never use `Any` or bare `object`

Use a specific type. If none exists, define one.

```python
# Forbidden
def load(data: Any) -> object: ...

# Prefer
from typing import TypeAlias

RawPayload: TypeAlias = dict[str, str]


def load(data: RawPayload) -> ParsedConfig: ...
```

### `TypeAlias`, `NewType`, `Protocol`

- **`TypeAlias`** — a documented name for an existing shape (`JsonObject: TypeAlias = dict[str, object]` is still too loose; name the real keys instead).
- **`NewType`** — a distinct domain id that must not mix with a raw `str` / `int`.
- **`Protocol`** — a structural interface when you need a method surface, not a concrete class.

### Dataclass vs Pydantic v2

| Use | When |
|---|---|
| `@dataclass` | In-process structured data you construct yourself |
| Pydantic `BaseModel` | External input — YAML, JSON, env, HTTP, CLI — that must be parsed and rejected if invalid |

Do not wrap a dataclass in ad-hoc `isinstance` checks to validate untrusted input. Load it through Pydantic (or an equivalent schema) at the boundary, then pass a typed model inward.

### Optional and unions

Write `str | None`, not `Optional[str]`. Every optional parameter has an explicit default (`arg: str | None = None`). Do not leave a parameter "optional" without a default.
