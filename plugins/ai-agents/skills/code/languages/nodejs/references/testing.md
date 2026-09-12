# Node.js — runner-less scripts

Universal test-authoring rules live in `code/quality/testing`. This file is the Node *how* for repos that have **no unit-test runner**.

Do not assume Vitest or Jest. If a project adds a runner, the repository `AGENT.md` Validate block governs. Until then, tests are plain Node (or Deno) programs invoked from `package.json` scripts (`security:test:*`, `infra:check-*`).

## Shared fixture data file

One JSON file of `{name, input, expected}` rows drives every implementation that must agree. When the file changes, update every reader in the same change. Compare by sorting both sides, then serializing — do not depend on insertion order.

## Table-driven cases without a runner

Return an array of named cases (`name`, expected status or value, inputs) and run them in a `for` loop. One row per interesting input. Tolerant expected values (`[401, 403]`) only when the contract allows a range — never to hide a flaky check.

## Exit-code contract

Accumulate into `let failed = 0`. On any failure, `process.exit(1)` (`Deno.exit(1)` in a Deno twin). A script that prints FAIL and exits 0 is invisible to CI.

## Preflight

Collect required env vars, report **all** missing names at once, and exit before any side effect.

## Cleanup

Release created resources in `finally`. Cleanup failures increment `failed` — they are test failures, not warnings.

## Console discipline

Same rules as the Node skill: `console.error` for FAIL, `console.warn` for the summary, `process.stdout.write` for PASS. Never `console.log`. Log `e instanceof Error ? e.message : String(e)`, never the raw error.

## Smoke tests

Security and end-to-end scripts hit the real deployed boundary. Mock nothing there. Create disposable identities with unguessable names, and delete them even when the suite fails.
