# npm Tooling

npm lint scripts, dependency audit, and lockfile hygiene for Node projects. Concrete command names and severity bars come from the repository `AGENT.md` **Validate** section when present.

## Prefer project scripts

- Run lint via the project script from `AGENT.md` (typically `npm run lint`), not ad-hoc `eslint` / `biome` invocations that skip config.
- Run build / type-check via the project build script from `AGENT.md`.
- Do not invent alternate flags that weaken the project's configured rules.

## Audit

- Run the audit command from `AGENT.md` (commonly `npm audit --audit-level=high`).
- **Required** when `package.json`, `package-lock.json`, or `npm-shrinkwrap.json` changed in the turn, and whenever the project's Validate suite includes audit at milestones.
- **Do not** silence audit with `npm audit fix --force`, `--audit-level=none`, or by deleting lockfile entries without user consent. Fix or upgrade dependencies deliberately; ask before force-resolving.
- Re-run audit after any install / update / uninstall that rewrites the lockfile.

## When work is complete

Before considering a Node/TS change done:

1. Lint from `AGENT.md` — zero errors.
2. Build when types or the build surface were touched.
3. Audit when deps/lockfile changed or the milestone requires the full Validate suite.

Record pass/fail from **raw** shell exit codes (do not trust wrappers that mask exit status).
