# User approach, buttons, and engagement

## Approach path

Model the person’s path, not the tree of components:

| Stage | Question |
|---|---|
| Entry | Where do they arrive from, and what do they already know? |
| Scan | What do they look for first? |
| Recognize | How do they know this is the right place? |
| Decide | What must they understand before acting? |
| Act | What is the one control that finishes the job? |
| Confirm | How do they know it worked (or failed)? |

Draw this as a mermaid flow (see `artifacts.md`). Extra steps stay only when they
protect against irreversible harm.

## Buttons and calls to action

- The **label is the outcome** the person wants (“Save draft”, “Send invite”) —
  not the system’s verb alone (“Submit”, “OK”) when a clearer outcome exists.
- The control **looks pressable** (affordance). Shape and contrast match the
  design system after handoff; the brief still names which control is primary.
- **Size, contrast, and position match importance.** One primary per view.
  Secondary and tertiary stay quieter and farther from where the eye finishes
  and the hand lands.
- **Destructive actions do not wear the primary style.** They need clear
  labeling and, when irreversible, a confirm step.
- **Few choices at the moment of decision.** Parallel equal-weight actions on
  the same job mean the job is split — fix the job or the hierarchy.

## Engagement (clarity, not growth tricks)

Engagement means the right action is easy to see and easy to hit.

Allowed:

- Clear primary, honest labels, visible result after press
- Designed empty, loading, and error states
- Confirm only when the action is hard to undo

Forbidden:

- Fake urgency (“Only 2 left!”) unless it is true product data the person needs
- Hidden dismiss or traps that make leaving harder than finishing
- Confirm-shaming (“No, I don’t want to save money”)
- Dark patterns that inflate clicks without finishing the job

## States

When the change is a state (or the flow depends on one), design:

- **Empty** — what to do next, not a blank void
- **Loading** — the person still knows where they are
- **Error** — how to recover; keep the primary path visible when safe
- **Pressed / success** — acknowledge the press, then show the result

Press *feel* (timing, springs, sound) is `ankyr-ux` after handoff. This skill
only requires that acknowledgment and result are part of the plan.
