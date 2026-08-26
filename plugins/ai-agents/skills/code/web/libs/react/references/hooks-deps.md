# Hook Dependencies & Effect Structure

## Complete dependency arrays

Include every value referenced inside the effect/callback.

```ts
// Bad — thoughtsLength used but missing
useEffect(() => {
  // ... uses thoughtsLength
}, [skipIntro]);

// Good
useEffect(() => {
  // ... uses thoughtsLength
}, [skipIntro, thoughtsLength]);
```

If a dependency causes an effect to run too often, restructure (memoize the value, move it into a ref, or split the effect) rather than omitting it or suppressing the linter.

## Async work in effects

An effect callback cannot be async. Wrap async work in a `void`-prefixed IIFE with `try/catch` (see `code/languages/nodejs` async-await reference).

## Cleanup

Every effect that creates a resource (listener, timer, subscription, context, GPU resource) must return a cleanup that releases it. See `code/quality/performance` for the catalog.

## useCallback / useMemo

- Memoize handlers and objects passed to memoized children or used in another hook's dependency array.
- Memoize genuinely expensive derived values.
- Do not memoize trivial primitives or values with no downstream dependency — it adds noise without benefit.
