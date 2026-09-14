# TypeScript Patterns

## Never use `any`

Always use a specific type. If none exists, create a named interface or type alias.

```ts
// Forbidden
const ref = useRef<any>(null);
(window as any).webkitAudioContext;
shapes: any[]
```

### Typed refs — provide the exact element/object type

```ts
const ref = useRef<HTMLDivElement>(null);
const audio = useRef<{ ctx: AudioContext; osc: OscillatorNode } | null>(null);
```

### Browser-vendor API extensions — extend the interface inline, never cast to `any`

```ts
const AudioCtx =
  window.AudioContext ||
  (window as Window & { webkitAudioContext?: typeof AudioContext })
    .webkitAudioContext;
```

### Prop/parameter shapes — define a named interface

```ts
interface OrbitShape {
  x: number;
  z: number;
  angle?: number;
}
```

### Library object access — cast to the concrete type before reaching members

When a library types a field as a union/base class, narrow to the concrete type before accessing members specific to it, rather than widening to `any`.

## Never use `@ts-nocheck`

It disables all checking for the file. Replace it by fixing the cause:

- Type every function parameter explicitly (`t: number`, not `t`).
- Narrow union/base types to the concrete type before member access.
- Remove unused imports that the suppression was hiding.

## Type packages & canonical types

Prefer official types over workarounds.

| Priority | Action |
|---|---|
| 1 | Add `@types/<package>` as a direct devDependency when DefinitelyTyped or the library provides it |
| 2 | Enable the type package in the correct tsconfig for the file's scope |
| 3 | Use the canonical exported type — not `ReturnType<typeof ...>` or a raw primitive when a named type exists |
| 4 | Add a project-owned alias only when a stable domain name helps (thin aliases over package types are fine) |

### Timer / animation-frame handles

Do not type a `setTimeout`/`setInterval` handle as `ReturnType<typeof setTimeout>` or raw `number`. Use the canonical environment type, and if the project defines a stable alias for it, use that alias. The concrete alias name and its location are a project convention — check the repository `AGENT.md` and project types.

```ts
// Avoid
const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
const cooldown = useRef<number | null>(null); // storing a timeout handle

// Prefer a named handle type (project alias over the canonical type)
const timerRef = useRef<TimeoutHandle | null>(null);
```
