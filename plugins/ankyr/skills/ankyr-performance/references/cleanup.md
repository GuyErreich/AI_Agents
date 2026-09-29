# Resource Cleanup Patterns

Every resource that allocates memory must be freed in its effect's cleanup.

## AudioContext

```tsx
useEffect(() => {
  const audioCtx = new AudioContext();
  // ...
  return () => {
    void audioCtx.close().catch(() => {}); // intentional
  };
}, []);
```

`close()` returns a Promise — use `void promise.catch(() => {})` to mark intentional suppression.

## Three.js geometries & materials

```tsx
useEffect(() => {
  const geom = new THREE.IcosahedronGeometry(10, 4);
  const mat = new THREE.MeshPhongMaterial({ color: 0xff0000 });
  // ...
  return () => {
    geom.dispose();
    mat.dispose();
  };
}, []);
```

## Event listeners

```tsx
useEffect(() => {
  const handleResize = () => setWidth(window.innerWidth);
  window.addEventListener("resize", handleResize);
  return () => window.removeEventListener("resize", handleResize);
}, []);
```

## Timers & intervals

```tsx
useEffect(() => {
  const id = setInterval(tick, 1000);
  return () => clearInterval(id);
}, []);
```

## Fetch / async with AbortController

```tsx
useEffect(() => {
  const abort = new AbortController();
  void (async () => {
    try {
      const res = await fetch("/api/data", { signal: abort.signal });
      setData(await res.json());
    } catch (e) {
      if (!(e instanceof DOMException && e.name === "AbortError")) {
        console.error(e instanceof Error ? e.message : String(e));
      }
    }
  })();
  return () => abort.abort();
}, []);
```

## Leak audit table

| Pattern | Risk | Fix |
|---|---|---|
| `new AudioContext()` without close | HIGH | `ctx.close()` in cleanup |
| `addEventListener` without remove | HIGH | `removeEventListener` in cleanup |
| `setInterval`/`setTimeout` without clear | HIGH | `clearInterval`/`clearTimeout` in cleanup |
| Three.js geom/mat without dispose | HIGH | `.dispose()` in cleanup |
| Fetch without AbortController | MEDIUM | abort in cleanup |
| Subscription without unsubscribe | MEDIUM | `.unsubscribe()`/`.off()` in cleanup |
