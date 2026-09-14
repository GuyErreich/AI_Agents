# Hardening: Uploads, External APIs, Rate Limiting, Checklist

## File uploads

```ts
const ALLOWED_MIMES = ["image/jpeg", "image/png", "image/webp"];
const MAX = 5 * 1024 * 1024;

if (!ALLOWED_MIMES.includes(file.mimetype)) return reject("type");
if (file.size > MAX) return reject("size");
// also check extension; generate a safe random filename, never trust the user's
```

## External API responses

Validate against a schema before trusting/persisting; set a timeout.

```ts
const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
if (!res.ok) throw new Error(`API ${res.status}`);
const validated = Schema.parse(await res.json());
```

## Errors generic to users

Log full detail to server logs; return a generic message to the client so internals (IPs, ports, stack) do not leak.

## Rate limiting

Apply rate limits to login and other sensitive routes to blunt brute-force and abuse. Time out long-running requests.

## Pre-merge checklist (auth / API / data / input)

- [ ] No injection: parameterized queries, never interpolation
- [ ] No XSS: framework-escaped or sanitized; no unsanitized raw HTML
- [ ] No CSRF: origin checks / tokens on state changes
- [ ] No hardcoded secrets; server-only secrets not client-inlined
- [ ] Server-side input validation with allow-lists
- [ ] No credential/PII logging; only safe messages logged
- [ ] Sensitive data protected at rest where applicable
- [ ] User-facing errors generic; detail in server logs
- [ ] Uploads validated (MIME, size, extension, safe name)
- [ ] External responses schema-validated
- [ ] Rate limiting on sensitive routes

## Pentest mindset

Ask: Can I bypass this check? What if I send null/empty/huge input? Can I inject special characters? Can I access another user's data by changing an id? What happens if my token expires mid-request? What gets logged if logs leak? Is there a race condition on double submit?
