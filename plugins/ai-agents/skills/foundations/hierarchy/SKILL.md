---
name: hierarchy
description: Domain-agnostic folder hierarchy decisions — where a folder belongs, when to nest for context vs stay generic, one axis per level, and when to restructure a drifted tree. Use before creating, naming, moving, or reorganizing folders in any tree (source, docs, assets, skills, rules).
disable-model-invocation: true
---

# Folder Hierarchy

Universal taxonomy logic for any folder tree. A folder is a **promise about context**: everything inside inherits the parent's meaning, and the path should read as a sentence that narrows scope (for example `code/web/libs/react`).

This skill is domain-agnostic. Code-specific application (shared vs feature-local, abstraction-then-extension) lives in `code/foundations/engineering` → `references/folder-structure.md`. Agent-library container tiers (rule vs skill vs `references/`) live in `ai-agent/hierarchy`.

## Principles

| Principle | Rule | Deep detail |
|---|---|---|
| Context promise | Path = narrowing sentence; children inherit parent meaning | — |
| Nesting test | Nest only when the item is wrong or meaningless outside its parent | — |
| Retrieval test | Put it where a newcomer with only their intent would look first | — |
| Generic high, specific low | Universal material stays high; domain-bound material nests; split rather than mislabel | `references/worked-examples.md` |
| One axis per level | Siblings at a level are alternatives on the same axis (languages, platforms, lifecycle phases) | — |
| Earn every level | Add a grouping level at 3+ siblings sharing real context; collapse single long-term occupants | `references/restructure-playbook.md` |
| Change unit + depth | Group what changes together; keep meaningful depth to ~3–4 levels, each answering a distinct question | — |

## Two tests

Most placement decisions reduce to these:

1. **Nesting test** — "Is this item wrong or meaningless outside its proposed parent?"
   - Yes → nest under that parent.
   - No → keep it a sibling (or higher).
2. **Retrieval test** — "Where would a newcomer look first, knowing only their intent?"
   - Put it there.

**Conflict:** when the tests disagree, favor **retrieval** and leave a pointer (index row, short redirect, or cross-link) from the other location.

## Decision procedure

1. **Name the responsibility** in one phrase (not the current file name).
2. **Pick the axis** at each level you descend — siblings must share that axis.
3. **Run the nesting test** against the candidate parent.
4. **Run the retrieval test** against the candidate path.
5. **Resolve conflicts** toward discoverability; add a pointer if needed.
6. **Refuse mixed axes** at one level (for example mixing `languages/` with `ci/` as siblings of the same parent without a shared axis).

## When to restructure

Load `references/restructure-playbook.md` when any of these appear:

- Hesitation about where to file a new item
- Sibling names share a repeated prefix (names simulating a missing folder)
- Every item in a folder only makes sense with one qualifier
- Cross-references constantly reach sideways
- The folder name no longer describes its contents

## When to load references

| Topic | Reference |
|---|---|
| Drift signals, six operations, safe migration | `references/restructure-playbook.md` |
| Illustrative decisions (no moves applied) | `references/worked-examples.md` |
