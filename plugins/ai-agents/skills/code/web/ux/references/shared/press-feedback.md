# Press Feedback

Lib-agnostic rules for tactile response on interactive controls. Applies whether motion comes from CSS, Framer Motion, or another library.

## Problems to eliminate

| Symptom | Cause | Fix |
|---|---|---|
| Rectangular flash on rounded button | `-webkit-tap-highlight-color` default | Set transparent on interactive elements |
| Harsh ring on every mouse click | `:focus` without `:focus-visible` | Style `focus-visible` only |
| Flat, dead-feeling tap | No active state | Add `:active` scale or background shift |
| Focus lost after dismiss | Focus not restored | Return focus to trigger on overlay close |

## Global baseline (CSS)

Apply to buttons, links used as actions, chips, tab items, and icon controls:

```css
button,
[role="button"],
a[href].interactive {
  -webkit-tap-highlight-color: transparent;
  outline: none;
}

button:focus-visible,
[role="button"]:focus-visible {
  box-shadow: 0 0 0 2px var(--focus-ring-color);
}

button:active:not(:disabled) {
  transform: scale(0.97);
  transition: transform 120ms ease;
}
```

Use design tokens for ring color and active scale — not magic numbers scattered per component.

## Rounded controls

When `border-radius` is large, never rely on browser default `outline` — it follows the border box but often looks rectangular on tap highlight. Combine:

- `tap-highlight-color: transparent`
- `focus-visible` box-shadow matching border-radius
- Optional `:active` background darken instead of scale when scale would clip in overflow containers

## Framer as default for React interactive elements

When Framer Motion is installed, prefer semantic motion elements over plain HTML for interactive controls:

- Replace `<button>` / `<a>` with `<motion.button>` / `<motion.a>` (or wrap with `motion()`)
- Wire `whileHover` and `whileTap` on every button, link, menu item, and icon control
- Adjust scale to fit layout (typical range 0.85–0.97 for `whileTap`; subtle hover scale when space allows)
- Do not disable `:focus-visible` styling on the underlying element
- Prefer `transition={{ type: 'tween', duration: 0.12 }}` for press — springs feel sluggish on tap

When the repo adopts generative sound (see nearest `AGENT.md`), also wire hover/click helpers — `generative-sound.md`.

GSAP press feedback is rarely worth it — use CSS or Framer for micro scale.

## Disabled and loading states

- `:active` and `whileTap` must not fire when disabled or loading
- Loading buttons keep focus ring behavior; show spinner without removing hit target size

## Checklist

```
- [ ] Tap highlight transparent on all tappable surfaces
- [ ] Keyboard focus visible via focus-visible (not mouse click ring)
- [ ] Active/whileTap feedback on primary actions
- [ ] Icon-only buttons still meet minimum touch target (see project UX if defined)
- [ ] Overlay close restores focus to trigger element
```

Semantic element requirements: `code/web/ui` → `a11y-interactive.md`. Focus ring policy cross-links here from that ref.
