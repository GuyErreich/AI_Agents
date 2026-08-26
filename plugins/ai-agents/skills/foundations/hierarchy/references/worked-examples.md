# Worked Examples

Illustrations for **domain-agnostic** folder placement. Agent-library container tiers live in `ai-agent/hierarchy` → `references/worked-examples.md`.

## Source UI tree — context under a feature

**Candidate:** `src/components/ui/` with feature folders such as `gamedev/` / `devops/`.

| Item | Nesting test | Placement |
|---|---|---|
| Cross-feature primitives (buttons, shells used everywhere) | Fails for any single feature | Stay at `ui/` root |
| Feature-only reusable blocks | Passes for that feature | `ui/<feature>/common/` |
| Desktop / mobile layout variants of one feature | Passes — meaningless outside the feature | `ui/<feature>/desktop/`, `ui/<feature>/mobile/` |

**Rule applied:** nest to maintain logical context under the feature; keep shared primitives high so retrieval for "the button" does not require knowing a feature name.
