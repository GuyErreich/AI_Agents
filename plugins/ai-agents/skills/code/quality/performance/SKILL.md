---
name: performance
description: Memory-leak prevention and render performance — resource cleanup, render optimization, WebGL/audio/timer disposal. Use when adding effects, listeners, timers, animations, or any resource that needs cleanup. Extends engineering.
disable-model-invocation: true
---

# Performance & Memory

Zero memory leaks and efficient rendering. Cross-cutting quality concern that applies to any code that allocates a resource.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first. For React/3D specifics, also load `code/web/libs/react` and `code/web/libs/threejs` as relevant.

## Core rules

- **Every resource is freed where it was created.** Each effect that allocates a listener, timer, subscription, context, or GPU resource returns a cleanup that releases it.
- **AudioContext** is closed in cleanup (`void ctx.close().catch(() => {})`).
- **Three.js geometries, materials, textures** created in scope are disposed in cleanup.
- **Listeners and timers** are removed/cleared in cleanup (`removeEventListener`, `clearInterval`, `clearTimeout`).
- **In-flight async work** is cancellable (`AbortController`, aborted on unmount).
- **No allocation in the render loop** (see `code/web/libs/threejs`).
- **Optimize renders where it matters** — memoize values passed to memoized children or used in dependency arrays; do not over-memoize.
- **Throttle high-frequency listeners** (scroll, resize, mousemove).
- **Lazy-load heavy, route-local code** to keep the main bundle lean.

## When to load references

| Topic | Reference |
|---|---|
| Cleanup patterns: audio, Three.js, listeners, timers, fetch | `references/cleanup.md` |
| Render optimization, throttling, code splitting, leak audit table | `references/render-optimization.md` |

## Validation

Profiling and bundle-size checks use the project's build commands and browser dev tools — see the repository `AGENT.md`.
