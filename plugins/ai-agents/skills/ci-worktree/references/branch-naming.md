# Branch naming and version bump

The consumer's auto-semver config (or the repo `AGENT.md`) is authoritative. Use this table when that config is silent.

## Prefix → typical bump

| Prefix | Typical bump | Use when |
|---|---|---|
| `major/` `breaking/` | Major | Breaking API or behavior |
| `feature/` | Minor | New capability without breaking changes |
| `fix/` `bug/` `hotfix/` `chore/` `devops/` | Patch | Fixes, maintenance, infrastructure |
| `docs/` `refactor/` `style/` `test/` `ci/` | Default patch | Docs, tests, style, CI — unless the repo config says otherwise |

Name as `<prefix>/<kebab-case-slug>`. Be specific (`feature/tag-promotion-workflow`, not `feature/new-stuff`).

## Creation

Hand off to this skill's **Create** / **Fallback** sections (`wtp add -b` or `git worktree add -b`). Do **not** `git switch -c` in the current checkout unless the user waived the worktree requirement.

## In-place fallback (explicit waiver only)

When the user said **work in place**, **skip worktree**, or **stay in this checkout**:

1. `git stash -u` if the tree is dirty — never switch dirty.
2. `git switch <base> && git pull --ff-only` (base from `AGENT.md`).
3. `git switch -c <prefix>/<slug>`.
4. Restore the stash; verify `git status`.
5. Never push — `push -u` needs explicit consent (`git-push-consent.mdc`).

## Bump vs release-notes group

- **Branch prefix** selects the version bump (this table / consumer config).
- **PR title** selects the release-notes group under `summary_mode: header_only`.

See `skills/ci-pr/references/title-conventions.md`. Prefer `feat:` / `fix:` on the PR title unless the repo documents supported imperatives.
