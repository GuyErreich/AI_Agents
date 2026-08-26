# Lens — TypeScript / JS

Activate with `code/languages/nodejs`. Hunt language-level honesty, not style taste.

## Hunt list

- **Lying types** — `as` / non-null `!` / `any` papering over uncertainty at boundaries
- **Narrowing gaps** — union members unhandled; `unknown` from JSON/fetch not validated
- **Async correctness** — missing `await`, floating promises, error swallowed in `catch` empty
- **Exhaustiveness** — switches/ifs on discriminated unions missing a variant
- **Module boundaries** — public exports that force callers into unsafe casts
- **Import discipline** — type-only imports where required by lint; circular imports that hide init bugs
- **Dead / divergent copies** — same helper rewritten with subtly different null rules

Trace each finding to a runtime or compile-time failure, not “I prefer another syntax.”
