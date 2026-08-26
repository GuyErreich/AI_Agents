# components/ui Hierarchy

Portable folder contract for web apps using responsive UI variants. Enforced by `code/web/components-ui-hierarchy.mdc` when editing under `**/components/ui/**`.

Composition rules (thin selectors, no duplicated base logic): `responsive-variants.md`.

## Tree

```text
components/ui/
├── AGENT.md                        # repo-local index (template below)
├── common/                         # cross-feature primitives (Button, Stack, Sheet, …)
├── desktop/                        # optional top-level desktop-only variant
├── <domain>/                       # feature area (schedule, gamedev, settings, …)
│   ├── AGENT.md                    # optional domain notes
│   ├── common/                     # domain shared blocks, data shells, controls
│   ├── mobile/                     # mobile layout composition only
│   └── desktop/                    # desktop layout composition only
└── <DomainSelector>.tsx            # thin root — picks mobile vs desktop variant
```

Path prefix varies by repo (`src/components/ui/`, `web/src/components/ui/`, etc.) — the **segment pattern** is what matters.

## Placement decisions

| You are building… | Put it in… |
|---|---|
| Reusable control used across features | `components/ui/common/` |
| Domain block shared by mobile and desktop | `components/ui/<domain>/common/` |
| Layout that only applies on coarse / narrow viewport | `components/ui/<domain>/mobile/` |
| Layout that only applies on wide / hover viewport | `components/ui/<domain>/desktop/` |
| Media-query selector between variants | Thin file at `<domain>/` root |

## Rules

- **Never** put viewport-specific layout in `common/` — only shared behavior and composition building blocks.
- **Never** duplicate base logic in `mobile/` and `desktop/` — both compose from `common/`.
- **Search before creating** — check `common/` and domain `common/` first.
- Feature root selectors stay thin: choose variant, pass props; no business logic.
- Repeated layout class chains → extract to shared component or `styles/components/`, not copy-paste across variants.

## Greenfield checklist

When scaffolding a new feature UI area:

```
- [ ] Create components/ui/<domain>/common/ first
- [ ] Add mobile/ and desktop/ only when layout genuinely diverges
- [ ] Add thin selector at domain root if both variants exist
- [ ] Add or update components/ui/AGENT.md (and domain AGENT.md if large)
- [ ] Cross-feature primitive? → components/ui/common/ instead
- [ ] Generative sound / Framer adoption? → nearest AGENT.md + code/web/ux → generative-sound.md
```

## AGENT.md template

Copy to `components/ui/AGENT.md` in new repos:

```markdown
# UI Folder Agent Notes

Search `components/ui/` before creating UI elsewhere.

## Structure

- Cross-feature primitives → `common/`
- Domain shared blocks → `<domain>/common/`
- Viewport layout variants → `<domain>/mobile/` and `<domain>/desktop/`

## Skills

- Structure / placement → `code/web/ui` → `components-ui-hierarchy.md`
- Mobile variant feel → `code/web/ux` + `mobile/*` refs (via `mobile-ux` rule)
- Desktop variant feel → `code/web/ux` + `desktop/*` refs (via `desktop-ux` rule)
- Generative sound adoption → nearest AGENT.md + `code/web/ux` → `generative-sound.md`
```

## Rule pairing

| Path glob | UI rule | UX rule |
|---|---|---|
| `**/components/ui/**` | `components-ui-hierarchy.mdc` | — |
| `**/components/ui/**/mobile/**` | `mobile-ui.mdc` | `mobile-ux.mdc` (same glob) |
| `**/components/ui/**/desktop/**` | `desktop-ui.mdc` | `desktop-ux.mdc` (same glob) |

Feature layout variants are not a PWA app shell — see `code/web/ux/references/viewport-routing.md`.
