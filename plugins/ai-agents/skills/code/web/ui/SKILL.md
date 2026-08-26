---
name: ui
description: Web UI architecture — reuse-driven component/hook/style extraction, responsive variant structure, and accessible interactive elements. Use when designing or refactoring UI structure. Extends engineering.
disable-model-invocation: true
---

# Web UI Architecture

Web-specific application of the engineering principles to component structure, styling, and accessibility. Generic reuse/structure/naming live in `engineering`; this skill covers what is specific to building UI.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first, then `skills/code/languages/nodejs/SKILL.md` for `.tsx` files. Add UI-specific rules only.

## Core rules

- **Reuse-first.** Search for an existing component, hook, or style class before creating one. Extend a primitive that covers most of the need rather than cloning it.
- **Component composition.** Top-level components compose; they do not carry implementation detail. Keep wrappers minimal — each must justify itself with layout, semantics, a state boundary, or a scroll boundary.
- **Data/view separation.** Move data fetching and state orchestration into hooks when a UI file becomes mixed-concern; components consume typed props.
- **Modern layout primitives.** Use Flexbox/Grid for structure; never table layout for page structure.
- **No magic values.** Reuse existing tokens/variables/classes; when a literal would repeat in 2+ places, name it once in the same change.
- **Hierarchy-first sizing.** Solve positioning and sizing at the highest layout boundary first; add deeper overrides only when a higher-level fix cannot satisfy the requirement.
- **Accessibility is mandatory.** Interactive behavior belongs on semantic interactive elements.
- **components/ui hierarchy.** New or moved UI under `components/ui/` must follow `references/components-ui-hierarchy.md` — `common/`, `<domain>/common/`, `mobile/`, `desktop/` placement.
- **UX is separate.** Load `skills/code/web/ux/SKILL.md` when adding or editing interactive **behavior** — press feedback, motion, overlays, pickers, transitions, or animation library choice.

## When to load references

| Topic | Reference |
|---|---|
| **Greenfield / `components/ui/` placement** | `references/components-ui-hierarchy.md` |
| Extraction triggers and targets (components, hooks, styles) | `references/reuse-extraction.md` |
| Responsive variant folder structure (common/desktop/mobile) | `references/responsive-variants.md` |
| Accessible interactive elements (semantic elements, aria) | `references/a11y-interactive.md` |
| Shared primitives catalog (Button, Stack, Sheet shell, etc.) | `references/standard-primitives.md` |

Load a reference only when the matching decision arises. Do not preload.

## Project layout

The concrete viewport/layout contract (navbar variables, section frames, card sizing) is project-specific. Read the nearest `AGENT.md` (for example the styles and components folders) for the repository's layout model.
