# Render Optimization

## Memoize where it matters

| Tool | Use when |
|---|---|
| `useCallback` | a handler is passed to a memoized child or used in a dependency array |
| `useMemo` | a derived value is expensive or passed to a memoized child |
| `React.memo` | a child should not re-render on unrelated parent state changes |

Do not memoize trivial values reflexively — it adds noise without measurable benefit. Profile first when optimizing broadly.

## Throttle high-frequency listeners

Scroll, resize, and mousemove can fire 100+ times per second. Throttle the callback:

```tsx
function useThrottledResize(callback: () => void, delay = 100) {
  const timeout = useRef<TimeoutHandle | null>(null);
  useEffect(() => {
    const onResize = () => {
      if (timeout.current) return;
      callback();
      timeout.current = setTimeout(() => {
        timeout.current = null;
      }, delay);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [callback, delay]);
}
```

(`TimeoutHandle` is the project's timer-handle alias — see `code/languages/nodejs` and the project `AGENT.md`.)

## Code splitting

Lazy-load heavy libraries used on a single route so they do not bloat the main bundle:

```tsx
const HeavyView = lazy(() => import("./HeavyView"));
// render inside <Suspense fallback={...}>
```

## Reuse over recreate

Create geometries, materials, and other expensive objects once via `useMemo`; reuse and update them rather than recreating per frame.

## Validation

Use the browser memory and render profilers to confirm memory returns to baseline after unmount and that components do not re-render unnecessarily. Bundle-size checks run via the project's build command (see `AGENT.md`).
