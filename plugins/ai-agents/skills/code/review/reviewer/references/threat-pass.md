# Phase 8 — Threat Model (Security-Review-style)

Go beyond the Phase 5 convention checks. For each finding, trace **attack path → impact → evidence in the diff**.

| Category | What to look for |
|---|---|
| **Secret exposure** | Server-only secrets inlined into client builds via the public env prefix; secrets in committed config |
| **Credential storage** | Tokens in committed files (config, examples, hooks); files that should be gitignored |
| **Injection** | Shell/scripts building commands from untrusted input; string-built queries |
| **Auth / tenancy** | New protected paths skipping session checks; data calls without error checks; RLS assumed but bypassed |
| **Client trust boundaries** | Sensitive operations moved client-side that belong on the server |
| **Supply chain** | New runtime dependencies with no actual usage; unnecessary packages |
| **Agent policy** | Instructions that weaken security (relaxing prod CORS, skipping consent, committing secrets) |

## Severity guide

- **Critical** — active secret in committed code, or exploitable without user action.
- **High** — realistic misconfiguration footgun, or missing auth on a sensitive path.
- **Medium** — doc/policy inconsistency with a plausible exploit path.
- **Low** — hygiene only.

Load `code/quality/security` references only if this pass surfaces an issue needing deeper patterns.
