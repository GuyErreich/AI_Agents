# Injection & XSS

## SQL / query injection

Never interpolate user input into a query. Use the data layer's parameterization.

```ts
// VULNERABLE — value interpolated into the filter
.eq("user_id", `${userId} OR 1=1`)

// SECURE — value passed as a parameter, treated as a literal
.eq("user_id", userId)

// Direct SQL — placeholders, values passed separately
await db.query("SELECT * FROM users WHERE id = $1", [userId]);
```

Always check the returned error on data calls and surface it safely.

## XSS

Framework auto-escaping makes interpolated text safe by default. Danger appears when rendering raw HTML.

```tsx
// VULNERABLE — raw HTML from user input executes scripts
<div dangerouslySetInnerHTML={{ __html: marked(markdown) }} />

// SECURE — sanitize first
const sanitized = DOMPurify.sanitize(marked(markdown));
<div dangerouslySetInnerHTML={{ __html: sanitized }} />
```

Never inject unsanitized HTML. When you must allow some HTML, sanitize with an explicit allow-list of tags and attributes.

```ts
DOMPurify.sanitize(userContent, {
  ALLOWED_TAGS: ["h1", "h2", "p", "strong", "em", "a", "ul", "li"],
  ALLOWED_ATTR: ["href", "title"],
});
```
