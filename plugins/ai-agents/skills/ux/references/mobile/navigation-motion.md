# Navigation Motion (Mobile)

Tabs, routes, sheets, and **edge list entrance** — mobile-first and PWA-primary patterns.

Load `../viewport-routing.md` when unsure if this ref or `desktop/navigation-motion.md` applies.

## Principles

| Principle | Guidance |
|---|---|
| Continuity | User should sense direction (forward/back, tab change) |
| Duration | 200–350ms for chrome; 120ms for micro feedback |
| Easing | Smooth ease-out for enter; ease-in for exit |
| Springs | Sheets and playful widgets only — not default tab motion |
| Reduced motion | Shorten or crossfade-only; never instant cut without user preference |

## Tab bar indicator

Preferred: **one sliding pill** behind labels, position/size via measured layout + CSS `transform` transition.

1. Measure active tab `offsetLeft` and `offsetWidth`
2. Apply to indicator with `transform: translateX()` and `width`
3. Transition with shared nav motion token

Avoid: independent background per tab that pops without shared indicator.

## Route / page transitions (SPA)

- **Framer `AnimatePresence`** keyed on route pathname — fade + slight translate (8–16px)
- **View Transitions API** when router integration is clean
- Scope motion to main content — not whole viewport unless intentional
- Exit must complete (or reduced-motion shortcut) before unmounting heavy content

## Stacked panels (month ↔ day, drill-down)

- Crossfade or horizontal slide; direction matches mental model (drill-down = from trailing edge in LTR)
- Local `useState` view switches still need enter/exit — no instant snap

## Edge list entrance (screen edge, not inner container)

Animations must read as entering from the **app frame edge**, not an inset padded box.

### Clip boundary

| Wrong | Right |
|---|---|
| Horizontal padding on the same ancestor that has `overflow: hidden` | Full-width clip viewport; padding on **inner** content |
| `overflow: hidden` on list stagger container **and** viewport | Clip once at viewport; no inner list clip |
| `translateX(±100%)` only | `translateX(calc(±100% ± content-inset))` so items start fully off-screen |

```text
main (padding-inline: 0)
  page-viewport (overflow-x: clip, full width)
    page-content (padding-inline: inset token)
      list stagger (optional negative margin to align bleed)
```

### Stagger direction

| UX intent | Entrance |
|---|---|
| Leading tab / home content | From **start** edge (LTR: left) |
| Trailing tabs / settings | From **end** edge (LTR: right) |
| Full-bleed surfaces (calendar planner) | No edge stagger — different motion contract |

### Checklist

```
- [ ] Clip at frame edge, not padded content box
- [ ] Transform distance includes horizontal content inset
- [ ] No double overflow clip on stagger wrapper
- [ ] prefers-reduced-motion: opacity-only or no slide
```

## Nav chrome vs content

- Tab bar: subtle indicator motion only
- Page content: slightly longer fade/slide or edge stagger
- Do not animate both with competing springs

## Reduced motion

When reduced: opacity-only or instant swap; keep tab indicator position update (no slide animation).

## Checklist

```
- [ ] Tab indicator moves smoothly (one shared element)
- [ ] Route/panel change has enter and exit
- [ ] Edge stagger clips at viewport, not inner padding wall
- [ ] Duration/easing from shared tokens
- [ ] prefers-reduced-motion honored
```

Shared: `../shared/motion-libraries.md`, `../shared/press-feedback.md`. Desktop wide layout: `../desktop/navigation-motion.md`.
