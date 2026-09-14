# UI Extraction Triggers & Targets

Extract shared UI immediately when any of these occur:

- The same JSX shell appears in 2+ places.
- The same state/effect orchestration appears in 2+ places.
- The same utility-class chain appears in 2+ places.
- A component becomes hard to read due to mixed concerns (data + layout + interactions).

## Extraction targets

| Repeated thing | Extract to |
|---|---|
| JSX shell | a shared component in a common boundary |
| State/effect orchestration | a hook in a responsibility folder |
| Utility-class chain | a named style class |
| Data transformation/orchestration | a shared utility or hook, out of the view |

Exact folder names are project conventions — see the nearest `AGENT.md`.

## Default enforcement

- When a change touches duplicated UI shell, motion, or interaction logic, extraction is part of the same change.
- Do not stop at visual parity while the same logic still exists elsewhere.
- Skip same-change extraction only when the user explicitly asks for a minimal one-off patch.

## CSS classes over inline styles

Prefer a named class over repeated inline `style` objects. Reserve inline style for runtime-computed values, animation library bindings, or genuinely one-off values with no reuse.
