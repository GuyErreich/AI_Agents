---
name: ankyr-engineering
description: Universal software engineering foundation — duplication, typing intent, naming, folder structure, separation of concerns, and coupling discipline. Default when the project is silent. Use before writing or reviewing any code.
disable-model-invocation: true
---

# Engineering Foundations

Language-agnostic principles that every code skill assumes and extends. This skill owns the *why* of good code; downstream skills (`nodejs`, `python`, `ui`, `react`, `testing`, `security`) own the *how* for their domain. Do not restate language syntax or framework rules here.

This skill is the **default** for those principles when the project is silent. The project is authoritative: resolve `AGENT.md` → project rules → project skills before applying anything here.

## Principles

| Principle | Rule | Deep detail |
|---|---|---|
| No duplication | Same logic, structure, or pattern in 2+ places → extract a shared abstraction before adding a third copy | `references/duplication-and-reuse.md` |
| Proper typings | Explicit, honest types at boundaries; never use typing to hide a design gap; types document intent | `references/typing-discipline.md` |
| Proper naming | Names reveal responsibility; consistent domain vocabulary; no misleading suffixes or cryptic abbreviations | `references/naming.md` |
| Folder structure | Code layout: shared vs feature-local; general taxonomy via `hierarchy` | `references/folder-structure.md` |
| Separation of concerns | One module, one reason to change; keep data, orchestration, presentation, and I/O apart | `references/separation-of-concerns.md` |
| Coupling / decoupling | Couple what changes together; decouple what changes for different reasons; avoid both duplication and premature abstraction | `references/coupling-decoupling.md` |

## Workflow

1. **Search before creating.** Look for an existing module, helper, type, or pattern that already covers the need. Extend it when it covers most of the case.
2. **Decide the boundary first.** Before writing implementation detail, state where shared logic, feature-local logic, and composition each live.
3. **Write to the principles above.** Keep each unit single-responsibility and named for what it does.
4. **Extract on the second occurrence.** When a pattern repeats, extract it in the same change rather than leaving duplication.
5. **Review against the principles.** Reviewer Phase 0 runs these checks before any domain phase. Folder taxonomy and `references/folder-structure.md` belong to reviewer Phase 0c when the folder-taxonomy capability row matches — Phase 0 does not preload that reference.

## When to load references

Load a `references/` file only when a principle needs a decision you cannot make from the table above — for example, choosing whether to couple two modules, or whether a repeated block is true duplication or coincidental similarity. Do not preload them.

## Default, not authority

This skill supplies defaults. It does not override a project standard that already speaks.

- Resolve `AGENT.md` (leaf → root), then project rules, then project skills, then this skill if installed. The first source that speaks wins.
- Domain skills in this plugin add *how* for their language or surface. They must not contradict these principles unless a project standard already does.
- Project skills under `.cursor/skills/project/` may tighten or replace these defaults. They do not loosen consent, review-gate, or security floors.
- Downstream plugin skills open with `## Foundation` (a resolution pointer), never a hard load of this file.
