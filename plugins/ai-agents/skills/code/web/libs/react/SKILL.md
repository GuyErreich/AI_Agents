---
name: react
description: React patterns — hook dependencies, component structure, render optimization, and GSAP integration. Use when writing or reviewing React components and hooks. Extends engineering and nodejs.
disable-model-invocation: true
---

# React

React-specific patterns layered on the language and engineering foundations.

## Extends

Load `skills/code/foundations/engineering/SKILL.md`, then `skills/code/languages/nodejs/SKILL.md`. For files that also carry layout, load `skills/code/web/ui/SKILL.md`. Add React-specific rules only.

## Core rules

- **Complete dependency arrays.** Every value referenced inside `useEffect`/`useCallback`/`useMemo` must appear in its dependency array. Do not suppress the linter — fix the dependencies or restructure.
- **One concern per file for fast refresh.** Do not mix a component export with context/constant/hook exports in the same module. Split instead of suppressing.
- **Block separation by responsibility.** Order a component body as config → state/refs → derived → effects → handlers → return, with a blank line between groups and before the return (see engineering `separation-of-concerns.md`).
- **Hooks live in responsibility folders**, never inside a single component's folder when they are reusable.
- **Render optimization where it matters.** Use `useCallback`/`useMemo` for values passed to memoized children or used in dependency arrays; wrap stable children in `React.memo`. Do not over-memoize trivial values.
- **Per-frame/continuous values use ref mutation, not state.** Driving continuous animation through `setState` causes a re-render every frame.

## When to load references

| Topic | Reference |
|---|---|
| Dependency-array patterns and effect structure | `references/hooks-deps.md` |
| Component splitting, file size, render optimization | `references/component-structure.md` |
| GSAP / animation-library integration and cleanup | `references/gsap-patterns.md` |

Load a reference only when the matching decision arises.
