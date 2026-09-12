# Navigation Motion (Desktop / Wide)

Navigation and layout motion for **desktop tree** components (`**/desktop/**`) and wide breakpoints.

Load `../viewport-routing.md` first.

## Principles

Same timing and reduced-motion rules as `mobile/navigation-motion.md`. Desktop adds **hover** and **keyboard** continuity.

## Sidebar and top nav

- Prefer **width/transform** or **opacity** transitions — avoid animating layout-heavy properties
- Active item: background or indicator slide — one shared indicator element when possible
- Collapse/expand: 200–280ms ease-out; respect `prefers-reduced-motion`

## Hover vs touch

| Input | Motion |
|---|---|
| `hover: hover` | Subtle lift/scale on links and cards; no hover-only critical affordances |
| Keyboard | Focus-visible ring; skip hover animations on `:focus-visible` |
| Coarse pointer on wide screens | Fall back to mobile press patterns from `../shared/press-feedback.md` |

## Route and panel transitions

- Crossfade or ±8–16px translate — same SPA rules as mobile
- Wide layouts may use **parallel column** transitions (master-detail) instead of full-page slide
- Preserve scroll position per column when switching selection

## Edge stagger on wide layouts

Edge entrance is usually **mobile-shell** concern. On desktop tree pages:

- Prefer **fade-up stagger** or **short translateY** for dense grids
- Use horizontal edge stagger only when mirroring mobile tab semantics intentionally

## Multi-column and master-detail

- Selecting an item: highlight + content pane crossfade
- Do not slide entire viewport when only detail pane changes

## Checklist

```
- [ ] Hover states do not replace keyboard focus visibility
- [ ] Master-detail updates scoped to pane, not full viewport
- [ ] No hover-only required actions
- [ ] Shared motion tokens; no ad-hoc durations per screen
- [ ] prefers-reduced-motion honored
```

Mobile / PWA: `../mobile/navigation-motion.md`. Shared libs: `../shared/motion-libraries.md`.
