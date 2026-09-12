# C++ tooling

CMake, clang-format / clang-tidy, sanitizers, and package-manager hygiene. Concrete command names come from the repository `AGENT.md` **Validate** section when present.

## CMake

- One target per library or executable. Public headers live on `target_include_directories(... PUBLIC)`.
- `target_link_libraries` with `PUBLIC` / `PRIVATE` / `INTERFACE` — never a directory-level `include_directories` or `link_libraries`.
- Prefer CMake presets (`CMakePresets.json`) over ad-hoc `-D` flag piles. Compiler, generator, and sanitizer variants are presets, not README folklore.
- Require C++20: `target_compile_features(<tgt> PUBLIC cxx_std_20)` (or the project's documented standard).
- Warnings-as-errors on every project target:

```cmake
target_compile_options(<tgt> PRIVATE
  $<$<CXX_COMPILER_ID:MSVC>:/W4 /WX>
  $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Wpedantic -Werror>)
```

## clang-format / clang-tidy

- Run format and tidy via the project scripts from `AGENT.md`, not ad-hoc invocations that skip config.
- Do not invent `// NOLINT` or `#pragma clang diagnostic ignored` to land a change. Fix the finding or, if the rule is wrong for the repo, change the shared tidy config with user consent.
- A committed `.clang-format` and `.clang-tidy` are the source of truth.

## Sanitizers

- Tests and local debug builds run under ASan + UBSan. TSan is a separate preset — do not mix it with ASan.
- Never ship a sanitizer build as the production artifact unless the project explicitly does so.
- A sanitizer hit is a test failure. Do not `export ASAN_OPTIONS=...` to silence it.

## Package managers

- Prefer vcpkg manifests (`vcpkg.json`) or Conan — pick the one the repo already uses. Do not add a second manager.
- **Required** audit / lockfile check when the manifest or lockfile changed, and whenever Validate includes audit at milestones.
- Do not pin a package by copying a binary into the tree. Record the dependency and the lock.

## When work is complete

1. Build from `AGENT.md` — zero warnings, zero errors.
2. Tidy / format when those commands are listed.
3. Tests under sanitizers when behavior changed.
4. Audit when deps/lockfile changed or the milestone requires the full Validate suite.

Record pass/fail from **raw** shell exit codes.
