# Overlay Patterns

Sheets, dialogs, and modals — portal placement, focus, and **dismiss lifecycle**. Quality bar applies to library-backed and hand-rolled overlays.

## Structure

| Concern | Rule |
|---|---|
| Stacking | Render in a **portal** at document root — above fixed nav/tab bars |
| z-index | Use a single overlay token; avoid per-feature z-index wars |
| Backdrop | Semantic `<button type="button" aria-label="Close">` or lib equivalent — not inert div with click handler only |
| Focus trap | Required for modal/dialog; sheet may allow partial background interaction only when lib explicitly supports it |
| Scroll lock | Lock body scroll while open; restore on close |

## Library choice

| Need | Prefer |
|---|---|
| Centered modal, focus trap | Radix Dialog, React Aria Modal |
| Mobile bottom sheet, drag dismiss | Vaul |
| Simple confirm | Radix Alert Dialog |
| Zero deps, simple panel | Hand-rolled portal + CSS transition (see lifecycle below) |

Load `library-selection.md` before adding Vaul or Radix if another overlay lib is already installed.

## Dismiss paths

Every user-visible way to close must run the **same exit sequence**:

1. Close button (header X or Cancel)
2. Backdrop tap
3. Escape key (modals)
4. Drag-to-dismiss (sheets, when supported)
5. Programmatic close after save — still animate out unless reduced motion

When the repo adopts generative sound (`generative-sound.md`), every dismiss path above must also fire `playMenuCloseSound` through the same close handler.

**Cancel is not instant unmount.** Sequence:

1. Optional press feedback on Cancel (~100–160ms)
2. Add closing/exit class or lib `open={false}` with exit animation
3. Wait for `transitionend` on the animating element (filter to `transform`/`opacity` if needed)
4. **Fallback timeout** (~400ms) if transitionend never fires
5. Call `onClose` / remove from tree / navigate away
6. Restore focus to trigger

## Hand-rolled lifecycle (React)

State model:

- `mounted` — in DOM
- `shown` — enter transition active
- `closing` — exit transition active

Enter: mount → `requestAnimationFrame` × 2 → add `shown` class.

Exit: user dismiss → `closing` → on `transitionend` (or timeout) → unmount + `onClose`.

Keep the overlay **mounted** during exit — never `{open && <Sheet />}` without exit phase unless reduced motion.

## Vaul / Radix notes

- **Vaul** — use `onOpenChange`; ensure Cancel goes through close animation, not conditional render skip
- **Radix Dialog** — `onOpenChange(false)` triggers exit when using CSS data attributes or Framer `AnimatePresence` wrapping content
- Wire **every** dismiss path through the same close handler

## Accessibility

- `aria-modal="true"` on dialog role where appropriate
- Title via `DialogTitle` or `aria-labelledby`
- Initial focus on first focusable or primary action
- On close: `focus()` trigger ref

## Checklist

```
- [ ] Portal at root; z-index above app chrome
- [ ] All dismiss paths share exit animation
- [ ] Cancel does not instant-unmount
- [ ] transitionend + timeout fallback implemented
- [ ] Body scroll locked while open
- [ ] Focus trapped (modal) and restored on close
- [ ] Backdrop is keyboard-accessible or lib handles equivalent
- [ ] prefers-reduced-motion: shorten or skip motion, keep dismiss functional
```

Primitive shell structure: `code/web/ui` → `standard-primitives.md`.
