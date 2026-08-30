# PR and commit title conventions

Squash-merge uses the **PR title** as the git commit header. Repos using auto-semver with `commit_groups.summary_mode: header_only` classify release notes from that single line.

**Default:** use a conventional-commit prefix on the PR title (`gh pr create --title "..."`).

## Prefix → release-notes group

| Title prefix | Use when | Typical auto-semver group |
|--------------|----------|---------------------------|
| `feat:` / `feat(scope):` | New capability or meaningful enhancement | Features & Enhancements |
| `fix:` / `fix(scope):` | Bug fix | Bug Fixes & Resolutions |
| `refactor:` | Behavior-neutral restructure | Refactoring & Code Quality |
| `docs:` | Documentation only | Documentation |
| `test:` | Tests only | Testing |
| `ci:` / `chore:` / `build:` | Tooling, deps, workflows | Infrastructure & Tooling |
| `perf:` | Performance improvement | Performance |
| `feat!:` / `BREAKING CHANGE:` | Breaking API or behavior | Breaking Changes |

## Imperative titles (no prefix)

Some teams use imperative titles without a prefix (`Add …`, `Fix …`, `Harden …`). These only land in the right release-notes group when the consumer's `commit_groups.patterns` lists that verb. Prefer `feat:` / `fix:` unless the repo documents supported imperatives.

## Multi-concern branches

Under `header_only`, only the **title** is grouped — Summary bullets are not classified separately.

- Prefer **one PR per concern**, or
- Title the **dominant** change type; mention secondary work in Summary bullets only.

## Examples

```
feat: harden merge-based auto-promote with dev/rc metadata wins
fix: resolve auto-promote merge conflicts on promotion metadata
docs: document merge-based promotion troubleshooting
```
