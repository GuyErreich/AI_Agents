---
name: ankyr-performance
description: Memory-leak prevention, render performance, and hot-loop data layout — resource cleanup, render optimization, AoS vs SoA. Use when adding effects, listeners, timers, animations, resources that need cleanup, or a loop over many elements.
disable-model-invocation: true
---

# Performance & Memory

Zero memory leaks and efficient rendering. Cross-cutting quality concern that applies to any code that allocates a resource.

## Foundation

Resolve standards project-first (`AGENT.md` chain, project rules, project skills, then this plugin if installed). Preferred if installed: engineering first; also react and threejs when the change is React or 3D.

## Core rules

- **Every resource is freed where it was created.** Each effect that allocates a listener, timer, subscription, context, or GPU resource returns a cleanup that releases it.
- **AudioContext** is closed in cleanup (`void ctx.close().catch(() => {})`).
- **Three.js geometries, materials, textures** created in scope are disposed in cleanup.
- **Listeners and timers** are removed/cleared in cleanup (`removeEventListener`, `clearInterval`, `clearTimeout`).
- **In-flight async work** is cancellable (`AbortController`, aborted on unmount).
- **No allocation in the render loop** (see `threejs`).
- **Optimize renders where it matters** — memoize values passed to memoized children or used in dependency arrays; do not over-memoize.
- **Throttle high-frequency listeners** (scroll, resize, mousemove).
- **Lazy-load heavy, route-local code** to keep the main bundle lean.
- **Hot loops stream contiguous fields.** A loop that updates one attribute across many elements uses a Structure of Arrays or a contiguous component array. Object graphs stay off that loop. See `references/data-layout.md`.

## When to load references

| Topic | Reference |
|---|---|
| Cleanup patterns: audio, Three.js, listeners, timers, fetch | `references/cleanup.md` |
| Render optimization, throttling, code splitting, leak audit table | `references/render-optimization.md` |
| AoS vs SoA, entity-component-system batches, when to leave the object graph | `references/data-layout.md` |

## Validation

Profiling and bundle-size checks use the project's build commands and browser dev tools — see the repository `AGENT.md`.
