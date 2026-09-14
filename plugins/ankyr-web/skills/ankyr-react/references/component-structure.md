# Component Structure & Render Optimization

## File size and splitting

Keep component files focused. When a file grows past comfortable readability:

- Extract each logical sub-component into its own file.
- Extract shared utilities (math, formatting, audio helpers) into non-component modules.
- Never leave non-trivial helper components defined inside a parent they do not belong to.

## Body ordering

Order a component/hook body by responsibility, separated by single blank lines:

1. Responsive config / feature flags / derived config constants
2. State and refs
3. Derived values (pure)
4. Effects
5. Handlers and actions
6. Return

Keep same-group lines together; always blank line before `return`; separate sibling handler functions with a blank line. Apply the same blank-line grouping to logically distinct sibling elements inside the returned JSX.

## Render optimization

| Tool | Use when |
|---|---|
| `useCallback` | a handler is passed to a memoized child or used in a dependency array |
| `useMemo` | a derived value is expensive or passed to a memoized child |
| `React.memo` | a child should not re-render on unrelated parent state changes |

Measure before optimizing broadly; do not wrap everything reflexively.

## Continuous values

For values that update every frame, mutate a ref rather than calling `setState`, to avoid a re-render per frame.
