# Separation of Concerns

One module, one reason to change. Keep distinct responsibilities in distinct units.

## The four concerns to keep apart

- **Data** — fetching, persistence, schema, queries.
- **Orchestration** — state machines, sequencing, business rules.
- **Presentation** — layout, rendering, formatting.
- **I/O and side effects** — network, storage, timers, device APIs.

A unit that mixes all four is hard to test, reuse, and reason about. Move data/orchestration out of presentation when a module becomes mixed-concern; presentation should consume typed inputs from a hook or service rather than reaching into a data source directly.

## Code block separation within a unit

Inside a function or component body, separate distinct logical groups with a single blank line, grouped by what the code does. A common order:

1. Configuration / feature flags / derived config
2. State and refs
3. Derived values (pure, no side effects)
4. Effects
5. Handlers and actions
6. Return / output

Keep tightly-related lines together (no blank line between two declarations in the same group). Always add a blank line before the final return. Separate sibling handler functions with a blank line even within the same group.

## Single-responsibility sizing

When a unit grows past comfortable readability, split it: extract sub-units into their own files and shared helpers into a shared module. Do not leave non-trivial helpers defined inside a parent they do not belong to.

## Smell

If you cannot describe a module's job in one sentence without "and", it probably has more than one concern.
