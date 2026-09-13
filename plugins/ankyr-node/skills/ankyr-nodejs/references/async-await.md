# Async / Await Over Promise Chains

Always use `async/await` — never `.then()/.catch()` chains. Promise chains hide control flow and make error handling easy to get wrong.

## Regular async function

```ts
// Bad
getSession()
  .then(({ session }) => { if (session) go(); })
  .catch(() => {});

// Good
try {
  const { session } = await getSession();
  if (session) go();
} catch {
  // intentional — network failure; stay on current page
}
```

## Inside an effect that cannot be async directly

Wrap in an async IIFE and prefix with `void` to mark the returned Promise intentionally not awaited:

```ts
// Good
useEffect(() => {
  void (async () => {
    try {
      const result = await fetchData();
      setState(result);
    } catch (e: unknown) {
      console.error("fetchData failed:", e instanceof Error ? e.message : String(e));
    }
  })();
}, []);
```

## Library API with an async callback plus a post-step

Await the whole call; do not chain `.then()` on the outside:

```ts
// Good
void (async () => {
  await initEngine(async (engine) => {
    await load(engine);
  });
  setReady(true);
})();
```

## Fire-and-forget browser API (e.g. audio resume/close)

```ts
void ctx.resume().catch(() => {}); // intentional
void ctx.close().catch(() => {});  // intentional, in cleanup
```

## Summary

| Situation | Pattern |
|---|---|
| Regular async function | `async` + `await` + `try/catch` |
| Effect with async work | `void (async () => { ... })()` |
| Library API with async callback + post-step | `await` the whole call, then next line |
| Fire-and-forget browser API | `void promise.catch(() => {}) // intentional` |
