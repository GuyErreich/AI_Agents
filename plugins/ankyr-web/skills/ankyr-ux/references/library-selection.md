# Library Selection

Master matrix for interactive UI. Load this **before** adding dependencies or hand-rolling complex behavior.

## Decision order

1. **Check `package.json`** — use installed libs first
2. **CSS + headless semantics** — sufficient for simple press, tab indicator, sheet slide
3. **Add one focused lib** — when baseline is fragile or maintenance-heavy
4. **One lib per concern** — do not stack Framer + GSAP for the same animation

## Matrix

| Situation | Prefer (if installed) | Add if missing | Avoid |
|---|---|---|---|
| Button/chip press & focus | CSS `:active` + tokens | — | Raw `outline` on rounded controls |
| Accessible dialog/modal | Radix Dialog, React Aria Dialog | `@radix-ui/react-dialog` | Div overlays without focus trap |
| Mobile bottom sheet | Vaul, Radix Dialog + motion | `vaul` | Full-screen modal styled as sheet |
| Sheet dismiss animation | Lib exit props or CSS lifecycle | — | Instant unmount on Cancel |
| Tab bar indicator | CSS transition + measured layout | — | Independent pills per tab |
| Route/page transition (SPA) | Framer Motion `AnimatePresence`, View Transitions | `motion` | Re-mount without exit phase |
| Route transition (MPA/SSR) | View Transitions API | — | JS-only when CSS API suffices |
| Panel crossfade (e.g. month/day) | CSS transform/opacity | Framer `layout` if shared layout | 100% off-screen snap |
| Micro-interactions (hover/tap) | CSS | Framer/Motion `whileTap` | GSAP for simple scale |
| Complex timelines / scroll scenes | GSAP (+ `useGSAP` in React) | `gsap` | Framer for long choreographed timelines |
| Drag reorder / calendar drag | `@dnd-kit/core`, `@use-gesture/react` | dnd-kit | Manual pointer events without a11y |
| Date picker (form) | react-day-picker, native `input[type=date]` | per UX needs | Unstyled text field for dates |
| Wheel column picker (month/year) | Custom snap wheel (CSS) | `react-mobile-picker`, Embla | Plain `<select>` on mobile primary flows |
| Carousel / horizontal snap | Embla Carousel | `embla-carousel-react` | Horizontal overflow scroll |
| Form controls a11y | React Aria, Radix primitives | `@react-aria/*` | Custom roving tabindex from scratch |
| Toast / command palette | Radix Toast, cmdk, Sonner | one toast lib | `alert()` for non-errors |

## How to use each row

- **Prefer** — first choice when already in the project
- **Add if missing** — acceptable single dependency when quality bar cannot be met otherwise
- **Avoid** — common regressions; fix instead of workaround

Deep implementation guidance lives in specialized refs:

| Row topic | Reference |
|---|---|
| Motion libs | `shared/motion-libraries.md` |
| Overlays/sheets | `shared/overlay-patterns.md` |
| Press/focus | `shared/press-feedback.md` |
| Pickers/carousels | `mobile/pickers-and-scrollers.md` |
| Tabs/routes/panels | `mobile/navigation-motion.md` or `desktop/navigation-motion.md` |

## Non-React note

Vue: VueUse Motion, `<Transition>`. Svelte: built-in transitions, `@sveltejs/svelte-motion`. Same quality bar and decision order apply.

## Checklist before adding a dependency

```
- [ ] Checked package.json for existing lib covering this concern
- [ ] Tried CSS + semantic HTML / headless primitive first
- [ ] New lib solves one concern only (not overlapping Framer + GSAP + spring)
- [ ] Exit animations and reduced-motion path planned
- [ ] Bundle size justified for the interaction complexity
```
