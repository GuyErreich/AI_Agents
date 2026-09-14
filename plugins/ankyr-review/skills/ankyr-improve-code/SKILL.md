---
name: ankyr-improve-code
description: Improve existing code that is not a git diff — a file, module, or package. Resolves the named path, routes language skills via the reviewer table (python for .py/.pyi), reviews at the file-argument tier, then drives ci-local-review-loop. Use when the user asks to improve, clean up, or find issues in a path rather than a branch diff.
---

# Improve Code

Owns **non-diff scope**. Issue hunting stays on `reviewer`. The fix loop stays on `ci-local-review-loop`.

## Foundation

Resolve standards in this order: the `AGENT.md` chain (leaf → root), then project rules, then project skills, then this plugin's matching skill if installed. The first source that speaks wins. Consent, review-gate, and security floors always apply.

## When to use

The user names a file, module, package, or folder and asks to improve it, clean it up, or find issues — not "review my changes", commit, PR, or push.

## Scope

1. Resolve the path the user named (file, module, or package). If it is missing, ask once.
2. Read the `AGENT.md` chain from that path up to the repo root.
3. Do not expand to the git diff unless the user switches to a milestone review.

## Route and hunt

1. Prefer the project's reviewer skill; if none, load this plugin's `skills/ankyr-reviewer/SKILL.md` if installed. Use its capability routing table. Do not copy that table here.
2. `*.py` / `*.pyi` → `python` (and `testing` when the path is a test).
3. Review at the **file argument** tier (`skills/ankyr-reviewer/references/tiers-and-scope.md`).
4. Produce the reviewer's findings table.

## Loop

Hand the findings and the same path scope to `skills/ankyr-ci-local-review-loop/SKILL.md`. That skill owns triage, approved fixes, Validate, and re-review. Do not invent a second loop.

When the loop ends clean (zero findings or accepted-by-design), offer `ankyr-ci-commit` only if the user asks. Never auto-commit.
