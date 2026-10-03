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

Split a unit when it has a second reason to change. Keep one algorithm readable from top to bottom. Extract sub-units into their own files and shared helpers into a shared module. Do not leave non-trivial helpers defined inside a parent they do not belong to.

- **Do** extract when a reader must understand a separate responsibility, or when a step will vary independently.
- **Do not** split a routine into micro-methods because a function passed a line count. A two-to-four-line wrapper whose name restates its body is a shallow module.

## Module depth

A **deep module** hides a lot of behavior behind a small interface: parsing, retry, cache layout, a batch transform. Callers use the interface without reading the body.

A **shallow module** has an interface almost as large as its implementation. Splitting one algorithm into many tiny methods does not remove complexity. It moves the load from reading a sequence into jumping across names.

- **Enforce** a deep module when one stable interface covers a rich job.
- **Do not** add a facade, helper, or class that only forwards one call.

Comments carry what syntax cannot: invariants, why a layout was chosen, and hardware constraints. Names carry what the code does. A comment that repeats the next line is noise. A comment that states a constraint the syntax cannot is part of the interface.

## Smell

If you cannot describe a module's job in one sentence without "and", it probably has more than one concern.
