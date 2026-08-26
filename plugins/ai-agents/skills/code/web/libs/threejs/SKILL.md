---
name: threejs
description: React Three Fiber and Three.js — render-loop performance, typed materials/refs, shader uniforms, and resource disposal. Use when writing or reviewing R3F/WebGL components. Extends engineering, nodejs, react, ui.
disable-model-invocation: true
---

# React Three Fiber & 3D

Three.js and R3F patterns layered on the full chain.

## Extends

Load in order: `engineering` → `code/languages/nodejs` → `code/web/libs/react` → `code/web/ui`, then this skill. Add 3D-specific rules only.

## Core rules

- **Never allocate inside the render loop.** No `new` objects (vectors, colors, geometries, materials, matrices) inside `useFrame` or animation update callbacks — allocate once via `useMemo`/`useRef` and reuse.
- **Mutate, do not re-render, per frame.** Update material uniforms / ref values directly in the loop; never `setState` per frame.
- **Type concretely.** Type refs to the exact class; narrow `material` to the concrete material type before accessing uniforms; name prop interfaces — never `any[]`.
- **Use the ecosystem.** Prefer `@react-three/drei` helpers and `useFrame` over raw Three.js primitives or raw `requestAnimationFrame`.
- **Stable uniforms.** Define shader uniforms via `useMemo` so the object reference is stable; mutate `.value` in the loop.
- **Dispose everything you create.** Geometries, materials, textures created in component scope must be disposed in cleanup (see `code/quality/performance`).
- **Instance at scale.** Use `InstancedMesh` for many identical geometries.

## When to load references

| Topic | Reference |
|---|---|
| Render-loop rules, drei usage, ref mutation | `references/r3f-lifecycle.md` |
| Geometry/material/texture disposal | `references/disposal.md` |
| Shader uniform pattern and material typing | `references/shaders.md` |
| Scaffolding a new R3F component | `assets/r3f-component-template.tsx` |

Load a reference only when the matching task arises.

## Project specifics

Folder location for 3D components, orchestration/animation context wiring, and audio-in-canvas conventions are project-specific — read the nearest `AGENT.md`.
