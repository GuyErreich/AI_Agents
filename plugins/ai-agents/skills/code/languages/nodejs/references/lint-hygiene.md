# Lint Hygiene

## Empty catch blocks

Two acceptable patterns; never an empty bound catch.

```ts
// Intentional suppression — omit the binding
try {
  // optional browser API that may throw on unsupported environments
} catch {
  // intentional — feature not supported
}

// When you need to log — use the error, then handle or re-throw
try {
  await risky();
} catch (err) {
  console.error("risky failed:", err instanceof Error ? err.message : String(err));
  throw err;
}

// Never
} catch (e) {}                     // triggers no-empty and no-unused-vars
} catch (e) { console.log(e); }    // log without propagating in critical code
```

## Unused variables

- Prefix intentionally unused names with `_`; linters ignore `_`-prefixed names.
- Remove imports that are never referenced.
- For unused destructured values, omit them or prefix with `_`.

## Fail-fast & exception handling

Code that can fail must fail loudly at the point of failure, not silently downstream.

- **Optional browser API** (audio, WebGL): silent suppression with an annotation (`catch {}`).
- **System boundary** (data layer, fetch): check the returned error and surface it; do not assume success.
- **Re-throw after logging** when you catch only to log: `throw err;` so callers still know.

## Console logging

Only `console.error` (unrecoverable failures) and `console.warn` (expected degradation) belong in shipped code. Everything else (`console.log/debug/info/table`) is forbidden — it leaks state and clutters output.

Log only a safe string, never the raw error object (which can embed user input or sensitive content in its stack):

```ts
// Bad
.catch((e) => console.error(e));

// Good
.catch((e: unknown) =>
  console.error("[Component] failed:", e instanceof Error ? e.message : String(e)),
);
```

## Fast Refresh — one concern per file

When a tool warns that a module exports both a component and a non-component (context, constant, hook), split the file so each module has a single export concern. Do not suppress the warning — fix it by splitting.

## Suppression comments

Do not add `// eslint-disable` (or equivalent) comments as a fix. Fix the actual issue. Configure ignore patterns (for example `_`-prefixed unused vars) at the config level, not per line.

## Unused dependencies

Before adding a dependency, and before finishing, verify it is actually imported. Remove packages that appear in the manifest but have no usage — they inflate install time and bundle size.
