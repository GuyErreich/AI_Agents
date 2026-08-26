# Lens — Frontend (React / UI / UX)

Activate with `code/web/libs/react`, `code/web/ui`, `code/web/ux` when components/pages/hooks change.

## Hunt list

### React correctness
- Effect/dependency honesty; stale closures; subscriptions without cleanup
- State that should be a ref (per-frame / ephemeral) or vice versa
- Derived state duplicated instead of computed
- Event handlers recreating expensive child work without need

### Accessibility (blockers are Medium+)
- Keyboard path for every mouse-only control (Enter/Space, arrows where expected)
- Focus order, focus trap/restore on overlays
- Non-interactive elements with `tabIndex={0}` / click handlers without role+key
- Labels, names, live regions for dynamic UI
- Contrast / hit-target only when clearly broken in changed UI

### UX / interaction
- Press, dismiss, outside-click, Escape consistent with existing patterns
- Reduced-motion respected for non-essential motion
- Loading/empty/error UI not left as blank or spinner forever
- Controlled/uncontrolled input mismatches

### Structure
- God components that should split by responsibility
- Hooks in the wrong folder vs project `AGENT.md`
- Prop drilling that already has a context/store pattern in-tree

Read the nearest `AGENT.md` for product-specific UI contracts before calling something “by design.”
