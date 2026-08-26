# Accessible Interactive Elements

Interactive behavior must live on semantic interactive elements so keyboard and screen-reader users can reach it.

## Never attach activation handlers to non-interactive elements

`<div>`, `<span>`, and styled non-button wrappers are not keyboard-focusable or activatable.

```tsx
// BAD — not focusable, not activatable via Enter/Space
<span onClick={handleClick}>Open section</span>

// GOOD
<button type="button" onClick={handleClick}>Open section</button>
```

## Correct element per intent

| Intent | Element |
|---|---|
| Navigation | `<a href>` / router link |
| Action | `<button type="button">` |
| Close an overlay | `<button type="button" aria-label="Close">` |
| Backdrop/overlay dismiss | `<button type="button" aria-label="Close">` |

## Labels

- Icon-only controls with no visible text must have an `aria-label`.
- Labels must describe the action, not the icon.

## Focus and keyboard

- Interactive elements must be reachable via Tab and activatable via Enter/Space (native elements give this for free).
- Do not remove focus outlines without providing an equally visible alternative.
- Focus ring styling, tap highlight, and active press feedback: `code/web/ux` → `references/shared/press-feedback.md`.

Project-specific motion and sound wiring (when repo adopts generative sound) is documented in nearest `AGENT.md` and `code/web/ux` → `generative-sound.md`.
