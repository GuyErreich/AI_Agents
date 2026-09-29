# Critique (in-process)

Run this self-check **before** presenting the brief or handing off to
implementation. Do not spawn a nested critic subagent.

## Checklist

| Check | Pass when |
|---|---|
| Squint test | Blurring the layout, one region clearly dominates as the action |
| One primary | Exactly one primary action per view; no tied competitors |
| Label is the outcome | Primary label names what the person gets, not a vague system verb |
| Approach clear | Mermaid path covers entry → … → confirm for this job |
| Reason on every placement | Each called-out element has a one-sentence why |
| States covered | Empty / loading / error / success addressed when the flow needs them |
| No dark patterns | No fake urgency, hidden dismiss, or confirm-shaming |
| Handoff clean | Brief does not prescribe animation libraries or new primitives |

## Failures

If any row fails, fix the brief in place and re-check. Do not hand off a failing
brief. If the job itself is ambiguous, ask the user — do not invent a second
primary to paper over it.

## Mode note

Critique is a **mode of this skill**, not a separate agent. The `designer` agent
loads this reference; it does not launch Task/subagents for review.
