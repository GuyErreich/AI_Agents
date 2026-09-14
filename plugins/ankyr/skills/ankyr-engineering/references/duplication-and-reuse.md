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

Extract on the second occurrence, in the same change. Do not wait for a third copy. The only exception is an explicit, temporary one-off patch the user requested.

## Before creating anything new

1. Search for an existing module/helper that does the same thing.
2. Search for the same logic already living inside another module.
3. If found in more than one place, extract immediately — do not leave the duplication behind.
