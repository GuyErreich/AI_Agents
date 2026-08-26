---
name: ux
description: Web UX — tactile feedback, motion, overlays, pickers, generative sound, and library choice for interactive surfaces. Use when adding buttons, sheets, tabs, transitions, pickers, or choosing animation/overlay libraries. Extends engineering and web/ui.
disable-model-invocation: true
---

# Web UX

Behavior, motion, and interactivity quality for web UIs. Generic structure and accessibility semantics live in `code/web/ui`; this skill covers **how interactions feel** and **which tools implement them**.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` and `skills/code/web/ui/SKILL.md` first (reuse, primitives, semantic elements). For React components, also load `skills/code/web/libs/react/SKILL.md` when hooks or animation cleanup apply.

## Core quality bar

Every interactive surface must meet these before shipping — libraries implement them; they do not replace them:

- **Press feedback** — no rectangular tap highlight on rounded controls; visible `:active` response; keyboard focus via `focus-visible` (not raw `outline` on every click)
- **Overlay dismiss** — portal above fixed chrome; stay mounted through exit animation; Cancel = press feedback → exit transition → `onClose`; `transitionend` + timeout fallback
- **Motion feel** — smooth easing for navigation, tabs, and panels; springs only for deliberate playfulness; honor `prefers-reduced-motion`
- **Pickers** — snap/wheel columns for enum/date selection on mobile; not raw scroll lists for primary flows
- **Generative sound** — optional adoption; Web Audio API helpers instead of static assets when repo mandates tactile sound (see nearest `AGENT.md`)
- **Library discipline** — check `package.json` first; prefer what is installed; add a dependency only when CSS + headless semantics cannot meet the bar

## Decision order

1. Check **`package.json`** — use what is already installed
2. Meet the quality bar with **CSS + headless semantics** when interaction is simple
3. **Add a focused library** when baseline is fragile (drag, complex focus trap, iOS sheet physics, timelines)
4. **Never add a second library** for the same concern without removing the first

Load `references/library-selection.md` before suggesting or adding any interaction library.

## Viewport routing

Load `references/viewport-routing.md` when the task spans `components/ui/**/mobile/**` or `components/ui/**/desktop/**` code paths.

| Viewport | When | References |
|---|---|---|
| **Routing** | Unsure which refs apply | `references/viewport-routing.md` |
| **Shared** | Overlays, press, motion libs, sound | `references/shared/*` |
| **Mobile tree** | `components/ui/**/mobile/**`, pickers, tab/sheet, edge entrance | `references/mobile/*` |
| **Desktop tree** | `components/ui/**/desktop/**`, hover, wide layout | `references/desktop/*` |
| **Tools** | Adding a dependency | `references/library-selection.md` |

## When to load references

| Topic | Reference |
|---|---|
| Viewport decision tree | `references/viewport-routing.md` |
| Situation → tool matrix | `references/library-selection.md` |
| CSS vs Framer vs GSAP vs View Transitions | `references/shared/motion-libraries.md` |
| Sheets, dialogs, dismiss lifecycle | `references/shared/overlay-patterns.md` |
| Tap highlight, focus rings, Framer press | `references/shared/press-feedback.md` |
| Web Audio hover/click/dismiss sound | `references/shared/generative-sound.md` |
| Wheel pickers, snap scrollers (mobile) | `references/mobile/pickers-and-scrollers.md` |
| Tabs, routes, edge stagger (mobile) | `references/mobile/navigation-motion.md` |
| Sidebar, hover, wide nav (desktop) | `references/desktop/navigation-motion.md` |

Load a reference only when the matching decision arises. Do not preload.

## Repo adoption

When the nearest `AGENT.md` mandates Framer motion + generative sound, treat missing hover/tap animation or sound on interactive controls as a defect. Helper import paths live in that `AGENT.md`, not here.
