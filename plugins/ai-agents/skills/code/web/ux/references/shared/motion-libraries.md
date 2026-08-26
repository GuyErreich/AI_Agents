# Motion Libraries

When to use CSS, View Transitions, Framer Motion, React Spring, or GSAP — and how to use them without leaks or jank.

## Quick pick

| Use case | Tool |
|---|---|
| Sheet slide, tab indicator, hover scale | **CSS transitions** |
| SPA route enter/exit, list reorder exit | **Framer Motion / Motion** |
| Document-level route change (MPA, Astro) | **View Transitions API** |
| Physics-based shared element | **React Spring** (if already in project) |
| Scroll-linked scenes, hero timelines | **GSAP** |

Load `library-selection.md` before introducing a new animation dependency.

## CSS transitions (default)

Best for: overlay slide, opacity fades, tab pill slide, picker snap, `:active` press.

Rules:

- Animate **transform** and **opacity** only when possible (compositor-friendly)
- Use consistent duration tokens (e.g. 200–320ms for panels, 120ms for press)
- Easing: `cubic-bezier(0.4, 0, 0.2, 1)` or project motion tokens — avoid linear for UI chrome
- Pair with explicit lifecycle for exit (see `shared/overlay-patterns.md`)

## View Transitions API

Best for: full-page navigations in MPAs, progressive enhancement on link clicks.

- `document.startViewTransition(() => { ... })` wrapping DOM update
- CSS `::view-transition-old/root` and `::view-transition-new/root` for fade/slide
- React SPAs: consider only when router integration is clean; Framer is often simpler in pure SPA

## Framer Motion / Motion

Best for: React component mount/unmount, `AnimatePresence`, layout animations, gesture-driven UI.

Patterns:

- Wrap conditional UI in `AnimatePresence` with `mode="wait"` or `"popLayout"` as appropriate
- Exit variants required — `{ opacity: 0 }` minimum
- `layout` prop for shared-layout tab indicators when CSS measurement is awkward
- Cleanup: Motion handles most; avoid leaving `AnimatePresence` children without keys

Avoid Framer for: long scroll-scrubbed timelines (use GSAP).

## React Spring

Use when project already depends on it. Equivalent role to Framer for physics-y UI. Do not add alongside Framer for the same components.

## GSAP

Best for: marketing heroes, ScrollTrigger, sequenced timelines, fine-grained control.

React integration: see `code/web/libs/react/references/gsap-patterns.md` — `useGSAP`, context cleanup, kill timelines on unmount.

Avoid GSAP for: button `:active`, simple sheet slide, tab indicator (CSS is cheaper).

## Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

In JS libs: `useReducedMotion()` (Framer) or check `matchMedia('(prefers-reduced-motion: reduce)')` — skip or shorten enter/exit; **never** skip functional dismiss.

## Performance checklist

```
- [ ] Animating transform/opacity, not width/height/top/left when avoidable
- [ ] Exit animations complete before unmount (or reduced-motion instant path documented)
- [ ] GSAP timelines killed on unmount
- [ ] No duplicate libs animating the same element
- [ ] will-change used sparingly, removed after transition
```

Tab and route specifics: `mobile/navigation-motion.md` or `desktop/navigation-motion.md`.
