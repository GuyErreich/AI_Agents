---
name: improve-code
description: Improve existing code that is not a git diff — a file, module, or package. Resolves the named path, routes language skills via the reviewer table (python for .py/.pyi), reviews at the file-argument tier, then drives ci-local-review-loop. Use when the user asks to improve, clean up, or find issues in a path rather than a branch diff.
---

# Improve Code

Owns **non-diff scope**. Issue hunting stays on `reviewer`. The fix loop stays on `ci-local-review-loop`.

## Extends

Load `skills/engineering/SKILL.md` first.

## When to use

The user names a file, module, package, or folder and asks to improve it, clean it up, or find issues — not "review my changes", commit, PR, or push.

## Scope

1. Resolve the path the user named (file, module, or package). If it is missing, ask once.
2. Read the `AGENT.md` chain from that path up to the repo root.
3. Do not expand to the git diff unless the user switches to a milestone review.

## Route and hunt

1. Load `skills/reviewer/SKILL.md` and use its **File → skill routing** table. Do not copy that table here.
2. `*.py` / `*.pyi` → `python` (and `testing` when the path is a test).
3. Review at the **file argument** tier (`skills/reviewer/references/tiers-and-scope.md`).
4. Produce the reviewer's findings table.

## Loop

Hand the findings and the same path scope to `skills/ci-local-review-loop/SKILL.md`. That skill owns triage, approved fixes, Validate, and re-review. Do not invent a second loop.

When the loop ends clean (zero findings or accepted-by-design), offer `ci-commit` only if the user asks. Never auto-commit.
