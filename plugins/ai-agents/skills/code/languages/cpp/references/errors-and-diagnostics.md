# Errors and diagnostics

## Fail fast

Validate inputs and preconditions at the top of the function. Return a status or throw — do not nest the happy path.

```cpp
struct BumpResult {
  Version value{};
  BumpError error{BumpError::none};
};

[[nodiscard]] BumpResult bump(std::string_view version, BumpKind kind) {
  if (version.empty()) {
    return BumpResult{.error = BumpError::empty_version};
  }
  if (!is_allowed(kind)) {
    return BumpResult{.error = BumpError::unknown_kind};
  }
  return BumpResult{.value = apply_bump(version, kind)};
}
```

C++20 projects use a named result type or `tl::expected`. Switch to `std::expected` only when the project is C++23+. Pick one convention per repo (`AGENT.md`) and stay consistent.

## Status types vs exceptions

| Use | When |
|---|---|
| Status / `expected` | Recoverable API failures the caller must handle (parse, I/O, lookup) |
| Exception | Truly exceptional — invariant broken, cannot continue this operation |
| `assert` / `[[assume]]` | Debug-only programmer errors that must never happen in correct code |

- Never `throw` a bare type (`int`, `const char*`). Throw a semantic type (`ConfigLoadError`).
- Never `catch (...) {}`. Bind only when you use the exception; log a safe string and rethrow, or handle a specific type.
- Never ignore a `[[nodiscard]]` return. If discarding is intentional, `static_cast<void>` with a comment — prefer not discarding.

## `noexcept`

Mark `noexcept` only when the function truly cannot throw (moves of noexcept members, trivial accessors). A lying `noexcept` turns a throw into `std::terminate`.

## Logging

- Use the project's logger. Do not `printf`, `std::cout`, or `std::cerr` from library code.
- Severity matches the event: debug traces, info milestones, warning for recoverable degradation, error for failures that stop the operation.
- Log context (path, operation, identifiers) — not secrets, tokens, or raw exception objects.

MSVC warning codes and pragmas: [Microsoft C++ docs](https://learn.microsoft.com/en-us/cpp/?view=msvc-170). Do not disable a warning to hide a real bug.
