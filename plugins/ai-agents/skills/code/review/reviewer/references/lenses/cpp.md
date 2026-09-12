# Lens — C++

Activate with `code/languages/cpp`. Hunt language-level honesty, not style taste.

## Hunt list

- **Lifetime / dangling** — `string_view` / `span` / reference bound to a temporary; returned pointer to a local; iterator used after invalidation
- **Ownership ambiguity** — raw owning pointer, unclear `unique_ptr` vs `shared_ptr`, missing `weak_ptr` on a cycle
- **UB shortcuts** — `reinterpret_cast` punning, unchecked `[]` on untrusted indexes, signed overflow, uninitialized reads
- **Discarded status** — ignored `[[nodiscard]]`, unused `expected` / error code, empty `catch (...) {}`
- **Suppressed diagnostics** — `#pragma warning(disable)`, `// NOLINT`, `-Wno-*` added to "make it compile"
- **Concurrency** — shared mutable state without a mutex; `std::atomic` with an unexplained memory order; data race
- **Header / ODR** — `using namespace` in a header, missing include, non-inline definition in a header

Trace each finding to a runtime, sanitizer, or compile-time failure, not “I prefer another syntax.”
