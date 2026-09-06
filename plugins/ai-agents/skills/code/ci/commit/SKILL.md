---
name: ci-commit
description: Commit workflow — confirm consent, review at change tier, split the working tree into logical commits, then commit each with a conventional message. Use when the user asks to commit. Extends engineering.
disable-model-invocation: true
---

# CI — Commit

The milestone workflow for creating commit(s). Review before committing; never commit without explicit user intent. Prefer **multiple logical commits** over one mixed dump when the tree spans more than one concern.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first.

## Split by logic

After consent and review, inspect `git status` and the full staged/unstaged diff. Partition changes into the smallest set of **self-contained** commits — each one reason to change, one clear why in the message.

| Split when… | Keep as one commit when… |
|---|---|
| Unrelated features, fixes, or refactors are mixed | Everything serves one concern |
| Skill/rule/docs vs product code | Product + its tightly coupled test/docs in the same change |
| Independent subsystems touched in one session | A single bugfix necessarily spans several files |
| Dependency/lockfile vs behavior change (unless the lockfile *is* the fix) | — |

Order commits so later ones can depend on earlier ones (foundations → feature → polish). Stage only the paths (or hunks via non-interactive `git add -p` only if required and safe) that belong to the current commit — never `git add -i`. Do not use interactive rebase to reshuffle; get the split right at commit time.

One user “commit” / “commit this” request authorizes the whole planned split for that working tree, not a single blob. If the split is ambiguous, state the planned commit list briefly and proceed unless the user objects.

## Workflow

1. **Confirm consent.** Only commit when the user explicitly asked to commit (see `rules/behaviors/git-commit-consent.mdc`). **Exception:** pr-resolver scoped consent when executing an approved fix plan — see pr-resolver `## Scoped consent`.
2. **Optional dedup.** If the repo provides the review-lock helper, `check change`; skip the scan if the tree is already reviewed.
3. **Review at change tier.** Run `skills/code/review/reviewer/SKILL.md` (tier: change) on the **full** working-tree change set. If findings exist, run the local review loop (`skills/code/ci/local-review-loop/SKILL.md`) until the verdict is clean or the user explicitly skips. Record the verdict if using the lockfile.
4. **Plan the split.** Group files/hunks by logic (above). Draft one imperative message per group (`add` / `update` / `fix` focused on the why).
5. **Commit each group** in dependency order, only after the review passed or was explicitly skipped. For each: stage only that group’s paths, commit via HEREDOC, then `git status`. Do not stage files that may contain secrets (`.env`, credentials, local MCP config); warn if the user asks to.
6. **Verify** the tree is clean (or only intentional leftovers remain) after the last commit.
7. **Do not push** unless pr-resolver Step 6 applies. General pushes need separate explicit consent (`rules/behaviors/git-push-consent.mdc`).

## Message format

Use the same subject-line prefixes as PR titles — see `skills/code/ci/pr/references/title-conventions.md` (`feat:`, `fix:`, etc.).

```bash
git commit -m "$(cat <<'EOF'
Concise imperative summary.

Optional body explaining the why.
EOF
)"
```

If a commit fails (for example a pre-commit check rejects it), fix the issue and create a **new** commit — do not amend a rejected commit.
