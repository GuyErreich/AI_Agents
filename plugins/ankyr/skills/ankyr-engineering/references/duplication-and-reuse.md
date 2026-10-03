# Duplication & Reuse

One implementation, imported everywhere. Duplicated logic drifts: a fix lands in one copy and not the others.

## Identifying duplication

- Identical or near-identical functions where only a constant or label differs.
- The same block of orchestration, validation, or transformation in two modules.
- The same structural shell repeated with small variations.

Coincidental similarity is not duplication. Two blocks that happen to look alike but change for different reasons should stay separate (see `coupling-decoupling.md`).

## Parameterize instead of copy

When functions differ only by a value, add a parameter rather than copying:

```text
BAD  — three modules each define createThing() with a different hardcoded label
GOOD — one createThing(label) used by all three
```

## Extraction targets

- Repeated pure logic → a shared utility module.
- Repeated stateful/effectful behavior → a shared hook or service.
- Repeated structure → a shared component or template.

The concrete destination folder is a project decision (see the project `AGENT.md` and `folder-structure.md`).

## Rule of thumb

Extract a second copy only when it is the same rule — the same reason to change. Do that in the same change.

Similar shape is not enough. If the blocks might be different concepts, leave them (AHA: avoid hasty abstractions). The Rule of Three applies to that uncertainty: a third occurrence under the same context is the signal they are one rule. Duplication is cheaper than the wrong abstraction.

Do not extract a one- or two-line wrapper. That is a shallow module (see `separation-of-concerns.md`).

The only other exception is an explicit, temporary one-off patch the user requested.

## Before creating anything new

1. Search for an existing module/helper that does the same thing.
2. Search for the same logic already living inside another module.
3. If a second copy is the same reason to change, extract it. If the match is only syntactic, leave it.
