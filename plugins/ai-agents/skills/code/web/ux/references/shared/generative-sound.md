# Generative Sound

Web Audio API feedback for interactive controls — zero network overhead, no static `.mp3` assets. Optional adoption per repo; mandatory when the nearest `AGENT.md` mandates Framer + generative sound.

## Principles

- Do not use external audio assets for UI interaction sounds — they bloat load size.
- Synthesize via `window.AudioContext` (or a shared helper module).
- Wire sound on hover, click, and **every overlay dismiss path** — not only the primary action.

## Helper module

Repos that adopt this pattern expose helpers from a single module. Read the nearest `AGENT.md` for the import path (example: `<repo>/src/lib/sound/interactionSounds.ts`).

Typical exports:

| Helper | When |
|---|---|
| `playHoverSound` | `onMouseEnter` on buttons, links, menu items |
| `playClickSound` | `onClick` (in addition to the primary handler) |
| `playMenuOpenSound` | Menu / modal open |
| `playMenuCloseSound` | Every dismiss path (see checklist below) |

## Interactive button example

```tsx
import { motion } from "framer-motion";
import { playHoverSound, playClickSound } from "<repo>/src/lib/sound/interactionSounds";

export const InteractiveButton = () => {
  return (
    <motion.button
      type="button"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onMouseEnter={playHoverSound}
      onClick={playClickSound}
      className="p-2 bg-blue-500 rounded text-white"
    >
      Click Me
    </motion.button>
  );
};
```

Adjust scale values to fit layout — see `press-feedback.md`.

## Required wiring per element

| Element | Required |
|---|---|
| Button / link / menu item | `whileHover` + `whileTap` via `motion.*` |
| Button / link / menu item | `onMouseEnter={playHoverSound}` |
| Button / link / menu item | `onClick={playClickSound}` (plus the primary handler) |
| Icon-only button | `aria-label` |
| Menu / modal | `playMenuOpenSound` on open |

## Dismiss-path checklist (menus/modals)

Every dismiss path must fire `playMenuCloseSound`:

- [ ] Close button
- [ ] Backdrop / overlay click
- [ ] Navigation link clicks that close the menu
- [ ] Any programmatic close triggered by user action

Overlay exit animation lifecycle: `overlay-patterns.md`. Press and Framer wiring: `press-feedback.md`.
