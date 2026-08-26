---
name: nodejs
description: TypeScript and JavaScript syntax, typing, and tooling discipline — no any, no suppression, async/await, lint hygiene. Use when writing or reviewing .ts/.tsx/.js files. Extends engineering.
disable-model-invocation: true
---

# Node.js / TypeScript

Concrete language-level rules for TypeScript and JavaScript. This is the *how* for the typing and quality intent defined in `engineering`.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first. Do not contradict engineering principles; add language-specific rules only.

## Core rules

- **Never use `any`.** Use a specific type or a named interface. If none exists, define one.
- **Never use `@ts-nocheck` or per-line suppression to silence errors.** Fix the underlying type issue.
- **Prefer canonical and official types.** Use a library's exported types and `@types/*` packages over hand-rolled approximations or `ReturnType<typeof ...>` workarounds. Define a named project alias only when a stable domain name helps.
- **Async/await only — never `.then()/.catch()` chains.** See `references/async-await.md`.
- **No empty `catch (e) {}`.** Use `catch {}` (no binding) for intentional suppression, or log and re-throw. See `references/lint-hygiene.md`.
- **No unused variables.** Prefix intentionally unused with `_` or remove. Remove unused imports.
- **Complete hook/effect dependency arrays** where the framework requires them.
- **Console discipline.** Only `console.error`/`console.warn` for unrecoverable or expected-degradation cases; never `console.log/debug/info` in shipped code. Log `e instanceof Error ? e.message : String(e)`, never the raw error object.

## When to load references

| Topic | Reference |
|---|---|
| No-`any` patterns, typed refs, vendor API extension, timer-handle typing, type packages | `references/typescript.md` |
| Promise chains → async/await conversions, `useEffect` async patterns | `references/async-await.md` |
| Empty catch, unused vars, fast-refresh exports, console rules, ESLint conventions | `references/lint-hygiene.md` |
| npm scripts, lint/audit cadence, lockfile changes | `references/npm-tooling.md` |

Load a reference only when a rule above surfaces an issue you need patterns for. Do not preload.

## Validation

Before considering work complete, run the project's **Validate** commands from the repository `AGENT.md` and require zero errors.

- **Lint** after JS/TS changes.
- **Build** when types or the build surface were touched.
- **Audit** when `package.json` / lockfile changed, and when Validate includes audit at milestones.

Load `references/npm-tooling.md` for npm script and audit discipline.
