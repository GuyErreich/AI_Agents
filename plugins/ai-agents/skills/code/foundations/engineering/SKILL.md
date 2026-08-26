---
name: engineering
description: Universal software engineering foundation — duplication, typing intent, naming, folder structure, separation of concerns, and coupling discipline. Base skill that every other code skill extends. Use before writing or reviewing any code.
disable-model-invocation: true
---

# Engineering Foundations

Language-agnostic principles that every `code/**` skill assumes and extends. This skill owns the *why* of good code; downstream skills (`languages/nodejs`, `web/ui`, `web/libs/*`, `quality/*`) own the *how* for their domain. Do not restate language syntax or framework rules here.

This is the **base of the inheritance chain**. Load it first, then layer the domain skill on top.

## Principles

| Principle | Rule | Deep detail |
|---|---|---|
| No duplication | Same logic, structure, or pattern in 2+ places → extract a shared abstraction before adding a third copy | `references/duplication-and-reuse.md` |
| Proper typings | Explicit, honest types at boundaries; never use typing to hide a design gap; types document intent | `references/typing-discipline.md` |
| Proper naming | Names reveal responsibility; consistent domain vocabulary; no misleading suffixes or cryptic abbreviations | `references/naming.md` |
| Folder structure | Code layout: shared vs feature-local; general taxonomy via `foundations/hierarchy` | `references/folder-structure.md` |
| Separation of concerns | One module, one reason to change; keep data, orchestration, presentation, and I/O apart | `references/separation-of-concerns.md` |
| Coupling / decoupling | Couple what changes together; decouple what changes for different reasons; avoid both duplication and premature abstraction | `references/coupling-decoupling.md` |

## Workflow

1. **Search before creating.** Look for an existing module, helper, type, or pattern that already covers the need. Extend it when it covers most of the case.
2. **Decide the boundary first.** Before writing implementation detail, state where shared logic, feature-local logic, and composition each live.
3. **Write to the principles above.** Keep each unit single-responsibility and named for what it does.
4. **Extract on the second occurrence.** When a pattern repeats, extract it in the same change rather than leaving duplication.
5. **Review against the principles.** Reviewer Phase 0 runs these checks before any domain phase.

## When to load references

Load a `references/` file only when a principle needs a decision you cannot make from the table above — for example, choosing whether to couple two modules, or whether a repeated block is true duplication or coincidental similarity. Do not preload them.

## Inheritance contract for downstream skills

Every skill under `code/` opens with an `## Extends` section pointing here and must not contradict these principles. It may add stricter, domain-specific rules. Project skills under `project/` may tighten rules further, never loosen them.
