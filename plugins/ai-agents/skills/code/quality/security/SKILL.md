---
name: security
description: Vulnerability prevention — injection, XSS, CSRF, auth/session, input validation, secret handling, uploads, and safe error logging. Use when code touches user input, auth, API routes, data access, or sensitive data. Extends engineering.
disable-model-invocation: true
---

# Security & Vulnerability Prevention

Cross-cutting quality concern. Target: zero vulnerabilities, zero penetration paths. Apply whenever code touches user input, authentication, API routes, or sensitive data.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first.

## Core rules

- **No injection.** Never interpolate user input into a query or command. Use parameterized queries / argument lists.
- **No XSS.** Rely on framework auto-escaping; sanitize any HTML rendered from user input before injecting it; never inject unsanitized HTML.
- **No CSRF on state changes.** Validate origin and/or use anti-CSRF tokens for state-changing requests.
- **Validate on the server.** Client validation is UX only; enforce format, length, and type server-side. Whitelist allowed values, never blacklist.
- **Protect auth and sessions.** Validate the session on every protected path and surface auth errors safely. Use secure cookie flags for server-set session tokens.
- **Never expose secrets to the client.** Keep server-only secrets out of client-inlined env vars; never hardcode keys.
- **Never log secrets or PII.** Log only safe identifiers and `e instanceof Error ? e.message : String(e)` — never the raw error or sensitive values.
- **Errors are generic to users.** Full detail goes to server logs only.
- **Validate uploads and external responses.** Check MIME/size/extension; validate external API responses against a schema.

## When to load references

| Topic | Reference |
|---|---|
| Injection, XSS, sanitization patterns | `references/injection-xss.md` |
| Auth, sessions, CSRF, secrets, input validation | `references/auth-and-input.md` |
| Uploads, external APIs, rate limiting, audit checklist, pentest mindset | `references/hardening-checklist.md` |

## Note on environment variables

Client bundlers inline variables with the public prefix into shipped output. Server-only secrets must never use that prefix — keep them in a server/edge secret store. The specific prefix and secret locations are project-specific (see the project `AGENT.md`).
