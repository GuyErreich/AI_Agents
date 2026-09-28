---
name: ankyr-designer
description: >-
  UI/UX design planning — user job, approach graph, one primary action, a reason
  for every placement, and literal screen wireframes. Use when designing,
  planning UI, changing layout or hierarchy, defining buttons or calls to action,
  mapping user flow, or designing empty/error/loading states.
---

# Designer

Plans screens the way a designer works: what the person came to finish, how they
approach the surface, which control is primary, why each placement exists, and a
literal picture of the result. Implementation structure and feel belong to
`ankyr-ui` and `ankyr-ux` after the brief is accepted.

## Foundation

Resolve standards project-first (`AGENT.md` chain, project rules, project skills,
then this plugin if installed). Preferred companions if installed: `ankyr-ui` for
structure/reuse/a11y and `ankyr-ux` for press/motion/overlays — load them only
**after** the design brief is accepted, never as a substitute for this process.

## Process (fixed order)

1. **Job** — one sentence: what the person came to finish.
2. **Approach** — their path: scan → recognize → decide → act → confirm (person
   flow, not a component tree).
3. **One primary action** — the control they came for is obvious; everything else
   is quieter and farther from where the eye finishes and the hand lands.
4. **Reason** — each placement, label, and size gets a sentence.
5. **Picture** — a literal wireframe of the proposed screen (and before/after when
   changing an existing screen); include empty/error/pressed when the change is a
   state.

Load `references/design-process.md` for the full brief template. Load
`references/user-approach.md` for button and engagement rules. Load
`references/artifacts.md` before drawing graphs or calling `GenerateImage`. Load
`references/critique.md` and pass the self-check before handoff.

## When to load references

| Topic | Reference |
|---|---|
| Brief template, order, handoff | `references/design-process.md` |
| Approach path, buttons, engagement | `references/user-approach.md` |
| Mermaid graphs, GenerateImage wireframes, skip rules | `references/artifacts.md` |
| Pre-handoff self-check | `references/critique.md` |

Load a reference only when the matching decision arises. Do not preload.

## Handoff

After the brief is accepted (or the user asks to implement):

- Prefer the project's UI skill; if none, load `ankyr-ui` if installed.
- Prefer the project's UX skill; if none, load `ankyr-ux` if installed.
- Do **not** pick animation libraries, invent primitives, or restate press
  feedback / a11y here — those are ui/ux responsibilities.
- Do **not** redraw the brief when the design is already accepted; implement.

## Out of scope

- Hooks (judgment, not mechanical gates)
- Nested critic subagents (critique is in-process via `references/critique.md`)
- Growth tricks, fake urgency, hidden dismiss, confirm-shaming
