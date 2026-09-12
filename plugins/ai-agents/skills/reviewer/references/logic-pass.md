# Phase 7 — Logic & Regression (Bugbot-style)

Hunt real bugs and regressions in the diff — not style nits already covered by earlier phases. For each finding, identify the concrete failure path.

| Category | What to look for |
|---|---|
| **API / doc drift** | Skills, rules, or docs describing APIs, props, or env vars that do not exist in code |
| **Workflow contradictions** | Agent instructions that conflict with each other or with repo rules (for example mandatory push vs a push-consent rule) |
| **Logic errors** | Off-by-one, wrong branch conditions, stale closures, race conditions, missing null checks on new paths |
| **Incomplete migrations** | Old copies left behind when a canonical version was updated, so behavior diverges by tool or path |
| **Hook / script bugs** | Wrong diff scope, infinite follow-up loops, state not reset on new changes |
| **Edge cases** | New paths without error handling; cleanup skipped on failure; effects firing after unmount |

Trace each candidate to a concrete trigger before reporting it. Load the relevant domain skill only if you need its patterns to judge a finding.
