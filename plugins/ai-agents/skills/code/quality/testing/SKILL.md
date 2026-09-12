---
name: testing
description: Test-authoring discipline — test behavior at seams, mock only true I/O, prefer fakes and real files over mocking internals, shared fixtures, one regression test per bug. Use when writing or reviewing tests. Extends engineering.
disable-model-invocation: true
---

# Testing

Language-agnostic rules for writing tests. Language runners and fixture libraries live in `references/`.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first.

## Core rules

- **Test behavior at seams**, not private internals. Assert observable outcomes (return value, file written, event emitted).
- **Mock only true I/O** — network, clock, subprocess, VCS, the filesystem when a fake is required. Do not mock the code under test.
- **Prefer real temp files and fakes** over mocking your own modules. See `references/fixtures-and-fakes.md`.
- **One shared fixture module per domain**, composed rather than copy-pasted.
- **Cover branches and edge cases.** One parametrized case per interesting input beats three copy-pasted tests.
- **One regression test per bug fix.** The test fails if the fix is reverted.
- **No test that still passes when the code under test is deleted.** If it would, it is not testing the behavior.

## When to load references

| Topic | Reference |
|---|---|
| Consolidating mocks, fixture composition, when a fake beats a mock | `references/fixtures-and-fakes.md` |
| pytest, pytest-mock, pyfakefs, shared `tests/fixtures/` | `references/python-pytest.md` |

Load a reference only when a rule above surfaces an issue you need patterns for. Do not preload.

## Validation

Run the project's test command from the repository `AGENT.md` Validate block. New tests must pass; existing tests must stay green.
