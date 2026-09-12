# Auth, Sessions, CSRF & Input Validation

## Never expose secrets in client code

```ts
// VULNERABLE — hardcoded secret, visible in the browser
const client = createClient(URL, "hardcoded-value");

// SECURE — public, RLS-limited key via env; sensitive ops go through a server function
const client = createClient(import.meta.env.VITE_API_URL, import.meta.env.VITE_PUBLIC_KEY);
```

Server-only secrets must never use the client-inlined env prefix.

## Validate the session on protected paths

Check both the error and the presence of the user/session, and fail safely:

```tsx
const { data, error } = await auth.getUser();
if (error || !data.user) {
  // redirect to login / show safe error
  return;
}
```

## Secure session cookies (server-set)

```ts
res.cookie("sessionToken", token, {
  httpOnly: true,   // not readable by JS — mitigates XSS theft
  secure: true,     // HTTPS only
  sameSite: "Strict", // mitigates CSRF
});
```

## CSRF

Validate `Origin`/`Referer` against an allow-list on state-changing requests, and/or require an anti-CSRF token issued to the client and verified server-side.

## Input validation

- Client checks are UX only. Enforce on the server.
- Validate format, length, and type.
- **Whitelist** allowed values; never blacklist (attackers find variations).

```ts
const allowed = ["created_at", "updated_at", "name", "status"];
if (!allowed.includes(sortBy)) return badRequest();
```

## Safe error logging

Log only the message, never the raw error or sensitive values:

```ts
console.error(e instanceof Error ? e.message : String(e));
```

Mask identifiers (e.g. emails) when logging an attempt; never log passwords, tokens, or PII.
