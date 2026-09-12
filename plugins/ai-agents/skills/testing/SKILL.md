---
name: testing
description: Test-authoring discipline — test behavior at seams, mock only true I/O, prefer fakes and real files over mocking internals, shared setup, one regression test per bug. Use when writing or reviewing tests. Extends engineering.
disable-model-invocation: true
---

# Testing

Language-agnostic rules for writing tests. Runner and library specifics live on the matching language skill (`python` → `references/testing.md`, `nodejs` → `references/testing.md`).

## Extends

Load `skills/engineering/SKILL.md` first.

## Core rules

- **Test behavior at seams**, not private internals. Assert observable outcomes (return value, file written, event emitted, HTTP status).
- **Mock only true I/O** — network, clock, subprocess, VCS, the filesystem when a fake is required. Do not mock the code under test. **Exception:** end-to-end and security smoke tests deliberately mock nothing, because the boundary under test is the real system.
- **Prefer real temp files and fakes** over mocking your own modules. A fake is an in-process stand-in with the same interface (in-memory store, temp clock). A mock records calls and returns scripted values. Fakes catch more contract drift.
- **Share setup.** If two tests build the same object, extract a factory or helper. Compose helpers instead of nesting setup in every test. Do not grow a second copy in a nearby file.
- **Table-driven cases.** One named row per interesting input beats three copy-pasted tests. A fixture is a named data file of `{name, input, expected}` rows, or a factory function — not a framework decorator.
- **Cover branches and edge cases** (empty, quoted, prefixed, missing, disallowed).
- **One regression test per bug fix.** The test fails if the fix is reverted.
- **No test that still passes when the code under test is deleted.** If it would, it is not testing the behavior.
- **A failing test must exit non-zero** so the build fails. Runner-less suites have to do this by hand (`process.exit(1)`, `sys.exit(1)`). A script that prints FAIL and exits 0 is invisible to CI.

## Shared data vs mocks

| Prefer a fake / real file / data file when… | Prefer a mock when… |
|---|---|
| The unit reads or writes files, YAML, or JSON | The collaborator is a remote API or git process |
| Two implementations must agree on the same cases | You only need to confirm a call happened |
| The real type is small and deterministic | Constructing the real type needs the network |

Do not mock internals (`_helper`, private methods) to force a path. Drive that path through the public API, or extract a seam you own and fake *that*.

When a shared case file drives more than one implementation, update every reader in the same change.

## Validation

Run the project's test command from the repository `AGENT.md` Validate block. New tests must pass; existing tests must stay green.
