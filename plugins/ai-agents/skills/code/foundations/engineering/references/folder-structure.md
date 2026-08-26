# Folder Structure

Organize by responsibility and feature, not by file type alone. The location of a file should tell the reader who owns it and whether it is shared.

For **domain-agnostic** placement (nesting vs hoist, one axis per level, restructure when trees drift), load `foundations/hierarchy` first. This file keeps only the **code** application of those principles.

## Principles

- **Shared vs feature-local is obvious from the path.** Reusable building blocks live in a shared/common boundary; feature-specific code lives under the feature.
- **Group what changes together.** Files edited together for a single reason belong in the same folder.
- **Predictable locations.** A new contributor should be able to guess where something lives from its responsibility.
- **Thin composition at the top.** Entry/selector modules choose and compose; they do not carry implementation detail.

## Abstraction-then-extension pattern

A widely useful structure for features that have shared behavior plus variants:

1. **Base primitive** in a top-level shared/common boundary — the reusable core.
2. **Thin wrappers** that apply variant-specific theme, naming, or behavior on top of the base.
3. **Variant composition** (for example responsive `desktop`/`mobile`) that composes wrappers, never duplicating the base logic.

Define the base first, wrappers second, variants last. When variant differences are known up front, create the wrappers first and route implementation through them rather than calling the base directly from feature screens.

## Anti-patterns

- A reusable hook or utility buried inside a single component's folder.
- The same logic duplicated across variant files instead of shared in a base.
- Deeply nested folders that mirror file type (`components/buttons/primary/...`) rather than responsibility.

## Project specifics

The exact folder names (for example `src/lib/`, `src/hooks/`, `common/`, `desktop/`, `mobile/`) are project conventions. Read the nearest `AGENT.md` and the `code/web/ui` skill for the concrete layout in this repository.
