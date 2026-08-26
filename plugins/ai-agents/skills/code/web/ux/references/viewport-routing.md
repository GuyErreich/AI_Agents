# Viewport Reference Routing

Which UX references to load — by **code path** and **task**. Skills do not auto-detect viewport; use this table and glob rules explicitly.

## Decision tree

1. **Editing `components/ui/**/mobile/**`** → `mobile/*` references (`mobile-ux.mdc`)
2. **Editing `components/ui/**/desktop/**`** → `desktop/*` references (`desktop-ux.mdc`)
3. **Overlays, press, motion libs, generative sound, a11y dismiss** → `shared/*` (all viewports)
4. **Unsure** → start `shared/`, then add viewport ref if layout diverges

## Reference map

| Viewport | When | Load |
|---|---|---|
| **Shared** | Sheets, dialogs, tap highlight, motion library choice, generative sound | `shared/overlay-patterns.md`, `shared/press-feedback.md`, `shared/motion-libraries.md`, `shared/generative-sound.md` |
| **Mobile tree** | `components/ui/**/mobile/**`, pickers, tab/sheet, edge list entrance | `mobile/navigation-motion.md`, `mobile/pickers-and-scrollers.md` |
| **Desktop tree** | `components/ui/**/desktop/**`, hover, wide layout, keyboard nav | `desktop/navigation-motion.md` |
| **Tool choice** | Adding animation/picker/overlay dependency | `library-selection.md` (root) |

## Code folder alignment

Rule pairing table: `code/web/ui` → `components-ui-hierarchy.md` → **Rule pairing**.

| Code path | UX references |
|---|---|
| `components/ui/**/common/` | `shared/*` + this file |
| `components/ui/**/mobile/` | `mobile/*` + `shared/*` |
| `components/ui/**/desktop/` | `desktop/*` + `shared/*` |

## Consuming projects

App-shell, tab-bar, and viewport-token contracts belong in the consuming repo `AGENT.md` (or a project skill). Feature motion still uses `mobile/*` and `desktop/*` refs under `components/ui/<domain>/`.

## Portable glob rules (`rules/code/web/`)

| Rule | Glob | Role |
|---|---|---|
| `ui.mdc` | `**/*.{tsx,jsx,css,scss}` | Structure → `code/web/ui` |
| `ux.mdc` | `**/*.{tsx,jsx,css,scss}` | Generic feel → `code/web/ux` |
| `components-ui-hierarchy.mdc` | `**/components/ui/**/*.{tsx,jsx,css,scss}` | Folder placement |
| `mobile-ui.mdc` | `**/components/ui/**/mobile/**/*.{tsx,jsx,css,scss}` | Mobile structure |
| `mobile-ux.mdc` | same as mobile-ui | Mobile feel + refs |
| `desktop-ui.mdc` | `**/components/ui/**/desktop/**/*.{tsx,jsx,css,scss}` | Desktop structure |
| `desktop-ux.mdc` | same as desktop-ui | Desktop feel + refs |
