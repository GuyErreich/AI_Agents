# Responsive Variant Structure

For UI-heavy features with shared behavior plus per-viewport differences, use the abstraction-then-extension pattern (see engineering `folder-structure.md` and **`components-ui-hierarchy.md`** for the full tree).

- `common/` — shared shells, controls, types, and data constants.
- `desktop/` — desktop-specific layout composition.
- `mobile/` — mobile-specific layout composition.
- A thin feature-root selector that chooses the variant via a media-query hook.

## Rules

- Keep selector components thin and declarative — they choose composition, nothing more.
- Reuse section wrappers across responsive variants; do not duplicate implementation between `desktop/` and `mobile/`.
- Define the base primitive first, section wrappers second, responsive variants last.
- When section differences are known up front (theme, spacing, behavior), create the wrappers first and route implementation through them rather than calling the base directly from feature screens.
- Keep naming aligned with the dominant domain naming in the feature; do not introduce alternate suffixes that fragment conventions.

This pattern applies broadly (cards, controls, overlays, filter bars, pagination), not to one element type.

## Skill and rule loading by folder

When working in responsive variant folders, load matching skills from `code/web/ui` and `code/web/ux`. Rule pairing table: **`components-ui-hierarchy.md`** → Rule pairing.

| Code folder | UI | UX |
|---|---|---|
| `components/ui/**` | `components-ui-hierarchy.mdc` → hierarchy ref | — |
| `common/` | `ui.mdc` | `ux.mdc` → `shared/*` + `viewport-routing.md` |
| `mobile/` | `mobile-ui.mdc` | `mobile-ux.mdc` → `mobile/*` + shared |
| `desktop/` | `desktop-ui.mdc` | `desktop-ux.mdc` → `desktop/*` + shared |

## Project specifics

The concrete path prefix (`src/` vs `web/src/`) is repo-specific. Read the nearest `AGENT.md` for local conventions. This portfolio has no PWA shell — feature motion uses `mobile/*` and `desktop/*` refs.
