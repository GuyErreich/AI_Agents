# Pickers and Scrollers

Wheel columns, snap lists, carousels, and date selection — mobile-first patterns and library options.

## When to use what

| UX need | Pattern |
|---|---|
| Month/year, hour/minute columns | **Snap wheel** (center highlight, inertial scroll) |
| Short enum (2–5 options) | Segmented control or native `<select>` on desktop |
| Form date entry | `input[type=date]`, react-day-picker, or locale-aware text + validation |
| Horizontal gallery | Embla or CSS scroll-snap |
| Long searchable list | Combobox (Radix/React Aria), not wheel |

Primary mobile flows should not use unstyled scroll lists for enum/date columns — use snap/wheel UX.

## Snap wheel (CSS + JS)

Structure:

- Viewport with fixed height showing ~3–5 rows; center row is "selected"
- Scroll container with `scroll-snap-type: y mandatory`; items `scroll-snap-align: center`
- On scroll end: read closest index, optionally programmatic scroll to center
- Highlight row via mask gradient or border on center slot

Libraries if hand-roll is costly:

- **react-mobile-picker** — iOS-style columns
- **Embla** — when horizontal or combined carousel behavior needed

## Native inputs

- `input[type=date]` — acceptable for admin/forms when visual polish is secondary
- `<select>` — OK for desktop secondary flows; avoid as primary mobile picker for calendar navigation

## react-day-picker

Use for inline calendar grids and range selection in forms. Distinct from column wheel used for compact month/year jump.

## Carousels (Embla)

- Install only when horizontal snap with drag is a primary interaction
- Loop, autoplay, and plugins add complexity — start minimal
- a11y: provide prev/next buttons with labels; do not rely on drag alone

## Scroll performance

- `overflow-y: auto` with `-webkit-overflow-scrolling: touch` on iOS when needed
- Avoid re-rendering all items on every scroll tick — derive selected index on scroll end
- Virtualize only when item count is large (100+)

## Checklist

```
- [ ] Mobile primary enum/date uses snap or wheel, not plain list
- [ ] Selected value visible in center or clearly marked
- [ ] Scroll end settles to valid index (no half-stopped state)
- [ ] Confirm/dismiss wired through overlay lifecycle if in sheet
- [ ] Keyboard alternative exists for desktop (type, arrows, or native select)
- [ ] prefers-reduced-motion: reduce scroll animation flair, keep selection usable
```

Library matrix row: `../library-selection.md`. Overlay hosting: `../shared/overlay-patterns.md`.
