# Naming

Names are the primary documentation. A good name removes the need for a comment.

## Principles

- **Name by responsibility.** A name should say what the thing is or does, not how it is implemented. `retryWithBackoff` is better than `loop2`.
- **Stay consistent within a domain.** Use the dominant vocabulary already present in a feature. Do not introduce an alternate suffix (for example `*Controls`) when a clearer domain name (`*Pagination`) already exists.
- **Avoid misleading names.** A name must not imply behavior the code does not have. Rename when behavior changes.
- **Avoid cryptic abbreviations.** Prefer `index` over `idx` unless the short form is an established convention in the codebase.
- **Booleans read as predicates.** `isActive`, `hasError`, `canRetry` — not `active`, `error`, `retry`.
- **Match scope to length.** Short names for short-lived locals; descriptive names for exported, long-lived identifiers.

## Consistency over personal preference

When the codebase already has a naming convention, follow it even if you would have chosen differently. New conventions fragment the codebase and slow every future reader.

## Smell

If you need a comment to explain what a name means, the name is wrong — fix the name instead of adding the comment.
