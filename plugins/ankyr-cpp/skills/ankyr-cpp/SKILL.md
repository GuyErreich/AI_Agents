---
name: ankyr-cpp
description: C++20 syntax, ownership, diagnostics, and tooling discipline — honest types, RAII, no UB shortcuts, fail-fast errors, clang-tidy/CMake. Use when writing or reviewing .h/.hpp/.cc/.cpp files.
disable-model-invocation: true
---

# C++

Concrete language-level rules for C++20. This is the *how* for the typing and quality intent defined in `engineering`.

## Foundation

Resolve standards in this order: the `AGENT.md` chain (leaf → root), then project rules, then project skills, then this plugin's matching skill if installed. The first source that speaks wins. Consent, review-gate, and security floors always apply. Add language-specific rules only.

## Core rules

- **Honest types at boundaries.** No `void*`, C-style casts, or `auto` that hides a design problem. Prefer `std::span`, `std::string_view`, `enum class`, and named structs over bare `int`/`bool` parameters. See `references/types-and-ownership.md`.
- **Never silence diagnostics.** Build with `-Wall -Wextra -Wpedantic -Werror` (MSVC `/W4 /WX`). Do not `#pragma warning(disable)` or `// NOLINT` a real bug — fix the cause.
- **RAII; no raw `new`/`delete`.** `unique_ptr` by default, `shared_ptr` only for shared ownership, `weak_ptr` to break cycles. Rule of zero; otherwise rule of five.
- **Explicit ownership at the API.** Value for sink, `const&` for read, `&&` for move-sink. A raw pointer or reference is non-owning. Never return an owning raw pointer.
- **`const` / `constexpr` by default.** `noexcept` only when it is true. `[[nodiscard]]` on anything that returns a value or status.
- **No UB shortcuts.** `std::bit_cast` / `memcpy` over type-punning `reinterpret_cast`; `.at()` / `std::span` over unchecked indexing; never bind `string_view` or a reference to a temporary.
- **Fail fast, explicit errors.** A named status/result type at API boundaries (`std::expected` when the project is C++23+; otherwise `tl::expected` or an equivalent). Exceptions for exceptional failures only. No empty `catch (...) {}`, no ignored return codes. See `references/errors-and-diagnostics.md`.
- **No unused variables.** `[[maybe_unused]]` or delete.
- **Logging discipline.** No `printf` / `std::cout` / `std::cerr` debug output in shipped code. Use the project's logger; log a safe string, never secrets or raw exception objects.
- **Header hygiene.** `#pragma once`, include-what-you-use, no `using namespace` at header scope. See `references/headers-and-includes.md`.
- **Modern idioms.** `std::ranges` / algorithms over hand-rolled loops, structured bindings, `std::format` over stream chains, `constexpr` / templates over macros.
- **OOP patterns.** At a second variant of one concern, use a pure-virtual base or a concept and select the implementation in one place. Prefer composition over an inheritance tree. Do not add a base for a single implementation. What each pattern means, including function versus object and the Expression Problem, is the engineering skill's `references/oop-and-patterns.md` if that skill is installed.
- **Hot-loop layout.** When a loop streams one field across many elements, follow the performance skill's `references/data-layout.md` if installed.
- **Concurrency.** Guard shared mutable state. Every `std::atomic` memory order needs an explicit rationale.
- **Authority for semantics.** [cppreference](https://cppreference.com/) for language and library behavior; [Microsoft C++ docs](https://learn.microsoft.com/en-us/cpp/?view=msvc-170) for MSVC pragmas, intrinsics, and warning codes. [DevDocs C++](https://devdocs.io/cpp/) is a convenient offline-friendly index of the same material.

## When to load references

| Topic | Reference |
|---|---|
| Honest types, smart-pointer choice, rule of zero/five, span/string_view lifetimes | `references/types-and-ownership.md` |
| Status types vs exceptions, `assert` vs runtime check, `noexcept`, no silent catch | `references/errors-and-diagnostics.md` |
| IWYU, forward declarations, ODR, `#pragma once`, modules | `references/headers-and-includes.md` |
| CMake, clang-format / clang-tidy, warning set, sanitizers, vcpkg/Conan | `references/tooling.md` |
| GoogleTest / Catch2, fixtures, sanitizer-enabled test runs | `references/testing.md` |

Load a reference only when a rule above surfaces an issue you need patterns for. Do not preload.

## Validation

Before considering work complete, run the project's **Validate** commands from the repository `AGENT.md` and require zero errors.

- **Build** with warnings-as-errors after C++ changes.
- **Lint / tidy** when Validate includes `clang-tidy` (or the project's equivalent).
- **Format** when Validate includes `clang-format` (or the project's equivalent).
- **Tests** when behavior or fixtures changed — under ASan/UBSan when the project enables them.
- **Audit** when the dependency manifest or lockfile changed, and when Validate includes audit at milestones.

Load `references/tooling.md` for CMake, tidy, sanitizer, and package-manager discipline.
