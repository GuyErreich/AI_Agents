---
name: ankyr-ci-commit
description: Commit workflow — confirm consent, review at change tier, split the working tree into logical commits, then commit each with a conventional message. Use when the user asks to commit, or when a rebase or other rewrite must be signed again before it is published.
disable-model-invocation: true
---

# CI — Commit

The milestone workflow for creating commit(s). Review before committing; never commit without explicit user intent. Prefer **multiple logical commits** over one mixed dump when the tree spans more than one concern.

## Foundation

Resolve standards in this order: the `AGENT.md` chain (leaf → root), then project rules, then project skills, then this plugin's matching skill if installed. The first source that speaks wins. Consent, review-gate, and security floors always apply.

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

1. **Confirm consent.** Only commit when the user explicitly asked to commit (see the `ankyr` core plugin's `rules/ankyr/behaviors/git-commit-consent.mdc` if installed). **Exception:** pr-resolver scoped consent when executing an approved fix plan — see the `ankyr-review` plugin's pr-resolver `## Scoped consent` if installed.
2. **Optional dedup.** If the repo provides the review-lock helper, `check change`; skip the scan if the tree is already reviewed.
3. **Review at change tier.** Prefer the project's reviewer; if none, load the `ankyr-review` plugin's `skills/ankyr-reviewer/SKILL.md` if installed (tier: change) on the **full** working-tree change set. If findings exist, run the local review loop (`ankyr-review` plugin's `skills/ankyr-ci-local-review-loop/SKILL.md` if installed) until the verdict is clean or the user explicitly skips. Record the verdict if using the lockfile.
4. **Plan the split.** Group files/hunks by logic (above). Draft one imperative message per group (`add` / `update` / `fix` focused on the why).
5. **Commit each group** in dependency order, only after the review passed or was explicitly skipped. For each: stage only that group’s paths, commit via HEREDOC, then `git status`. Do not stage files that may contain secrets (`.env`, credentials, local MCP config); warn if the user asks to.
6. **Verify** the tree is clean (or only intentional leftovers remain) after the last commit.
7. **Do not push** unless pr-resolver Step 6 applies. General pushes need separate explicit consent (the `ankyr` core plugin's `rules/ankyr/behaviors/git-push-consent.mdc` if installed).

## Message format

Use the same subject-line prefixes as PR titles — see `skills/ankyr-ci-pr/references/title-conventions.md` (`feat:`, `fix:`, etc.).

```bash
git commit -m "$(cat <<'EOF'
Concise imperative summary.

Optional body explaining the why.
EOF
)"
```

If a commit fails (for example a pre-commit check rejects it), fix the issue and create a **new** commit — do not amend a rejected commit.

## Re-sign after a rewrite

A rebase, amend, or history filter writes new commit objects. A GPG or SSH signature covers one payload — tree, parents, author, committer, and message — so it cannot be copied onto the replacement. GitHub then reports the new objects as unverified (`unsigned`).

When a rewrite replaces commits that were already verified:

1. Replay them with signing. A plain `git rebase <upstream>` does nothing when the branch is already based on that upstream ("up to date") and leaves the unsigned objects in place. Force the replay:

```bash
git rebase --force-rebase --gpg-sign <upstream>
```

Rebase keeps the author name, email, and author date. Do not use an interactive rebase to reshuffle the series while re-signing.

2. The committer email must belong to the GitHub account that owns the signing key. A valid signature from any other account's key stays unverified (`unknown_key`). Keep the committer on the identity that key is registered to. Do not retarget the committer to a noreply address that has no matching key.

3. Confirm the signature before treating the rewrite as done. `git log --format='%G?'` prints `N` for SSH signatures until `gpg.ssh.allowedSignersFile` exists locally. That local `N` is not GitHub's verdict. After the consented push, check each new SHA:

```bash
gh api repos/<owner>/<repo>/commits/<sha> --jq '.commit.verification | {verified, reason}'
```

`verified: true` and `reason: valid` is the badge. `unsigned` means the rewrite dropped the signature. `unknown_key` means the key is not registered to the committer.

4. If this environment has no signing key, stop. Do not force-push unsigned replacements over verified commits. The push itself still follows `skills/ankyr-ci-push/SKILL.md` (explicit consent, `--force-with-lease`, and no protected branch unless the user named that branch).
