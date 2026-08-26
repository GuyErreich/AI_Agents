# Coupling & Decoupling

The hard judgment call: when to join two pieces of code and when to keep them apart. The goal is a codebase where a single change touches a single place, without inventing abstractions you do not need.

## Couple what changes together

If two pieces of logic always change for the same reason, keep them together. Splitting them forces every change to edit two places in lockstep and invites drift.

## Decouple what changes for different reasons

If two pieces change for different reasons or on different schedules, separate them even if they look similar today. Forcing them through one shared abstraction creates a unit with multiple reasons to change and tangled conditionals.

## Coincidental duplication is not duplication

Two blocks that look alike but represent different concepts will evolve apart. Extracting them into one shared unit is premature abstraction — it couples things that should be independent. Wait until you are confident they share a single reason to change.

## Avoid premature abstraction

- Do not add an abstraction layer (a one or two line wrapper, a config object, an interface) for a single current caller and a hypothetical future one.
- Prefer a small amount of duplication over the wrong abstraction. The wrong abstraction is more expensive to undo than duplication.
- Add the abstraction when the second real, same-reason use case appears.

## Avoid shotgun coupling

- A change that ripples across many modules signals hidden coupling. Concentrate the volatile decision in one place.
- Depend on stable interfaces, not on the internals of another module.

## Decision checklist

1. Do these change for the **same reason**? → couple.
2. Do they change for **different reasons**? → decouple.
3. Are they similar **by coincidence**? → keep separate; revisit later.
4. Is the abstraction earning its keep with two real uses? → if not, wait.
