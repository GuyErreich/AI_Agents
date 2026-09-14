---
name: ankyr-ci-push
description: Push workflow — require explicit consent, review at PR tier, and if an open PR has unresolved review threads, hand off to pr-resolver. Use when the user asks to push.
disable-model-invocation: true
---

# CI — Push

The milestone workflow for pushing to the remote.

## Foundation

Resolve standards in this order: the `AGENT.md` chain (leaf → root), then project rules, then project skills, then this plugin's matching skill if installed. The first source that speaks wins. Consent, review-gate, and security floors always apply.

## Workflow

1. **Require explicit push consent.** Never push without it (see the `ankyr` core plugin's `rules/ankyr/behaviors/git-push-consent.mdc` if installed). General work still needs an explicit "push" request. **Exception:** when running the `ankyr-review` plugin's `ankyr-pr-resolver` (if installed), approving the resolver plan (or an explicit "resolve comments" request) grants scoped commit+push consent for approved fix commits only — see pr-resolver `## Scoped consent`.
2. **Review at PR tier.** Prefer the project's reviewer; if none, load the `ankyr-review` plugin's `skills/ankyr-reviewer/SKILL.md` if installed (tier: pr). Require a clean verdict or an explicit skip.
3. **Check for an open PR** on the current branch:

```bash
gh pr view --json number,url,state 2>/dev/null
```

4. **If an open PR exists**, fetch its review threads (see the `ankyr-review` plugin's `ankyr-pr-resolver` graphql reference if installed). If there are unresolved threads, stop and hand off to that resolver — do not push unrelated changes on top. **Exception:** pr-resolver may push after validation when executing an approved fix plan (its Step 6).
5. **If no open PR** (or no unresolved threads outside an active resolver fix push) and the local review passed, push.

```bash
git push        # only after explicit consent and a clean/again-skipped review
```

Never force-push to a shared branch without an explicit request, and warn before any force-push to a protected branch.
