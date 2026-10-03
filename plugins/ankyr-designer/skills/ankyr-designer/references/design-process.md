# Design process

Every UI/UX plan answers five things **in this order**. Do not skip ahead to
components or pixels until Job and Approach are stated.

## Brief template

```markdown
## Design brief

### Job
<one sentence: what the person came to finish>

### Approach
<mermaid: entry → scan → recognize → decide → act → confirm>

### Primary action
<control label + where it sits + why it is the one action>

### Placement reasons
- <element>: <one sentence why>
- …

### States (when relevant)
- empty: …
- loading: …
- error: …
- pressed / success: …

### Pictures
- proposed: <wireframe generated>
- before (if changing existing): <wireframe or reference screenshot>
```

## Order rules

1. **Job first.** If you cannot say the job in one sentence, ask — do not invent
   a multipurpose screen.
2. **Approach is the person.** Draw how they move through the moment, not how
   components nest.
3. **One primary.** If two controls compete for primary styling, the job is
   unclear — resolve before drawing.
4. **Reason every placement.** Labels, size, and position without a reason are
   incomplete. Prefer “Save sits at the end of the form because that is where the
   decision finishes” over “put Save on the right.”
5. **Picture last among the five.** Graph and reasons come before
   `GenerateImage`. See `artifacts.md`.

## Handoff

When the user accepts the brief or asks to build:

1. Stop redesigning unless they reopen design questions.
2. Hand structure/reuse/a11y to `ankyr-ui` (or the project UI skill).
3. Hand press/motion/overlays to `ankyr-ux` (or the project UX skill).
4. Keep this brief as the source of truth for hierarchy and primary action —
   implementation must not invent a second primary.
