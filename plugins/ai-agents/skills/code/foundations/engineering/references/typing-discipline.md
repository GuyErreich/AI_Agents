# Typing Discipline (intent, not syntax)

This is about *what types should express*, independent of language. Language-specific rules (for example TypeScript `any`, `@ts-nocheck`, or `@types/*` packages) live in `code/languages/nodejs`.

## Principles

- **Types document intent.** A type at a boundary tells the reader what is allowed and what the value means. Prefer a named type over an anonymous shape when the shape has meaning.
- **Be honest.** Never use a typing escape hatch (casts to a permissive type, suppression directives, widening to a catch-all) to silence an error you have not actually solved. A type error usually signals a real design gap — fix the gap.
- **Type the boundaries.** Public function parameters, return values, and module interfaces should be explicit. Internal locals can rely on inference when it stays readable.
- **Prefer canonical types.** When a library or platform already exports a type for a value, use it rather than re-deriving or approximating it.
- **Name stable concepts.** When a type carries domain meaning that appears in more than one place, give it a name and reuse it.

## Smells

- A cast used to reach a property the type system says does not exist — usually the wrong type was chosen upstream.
- A permissive catch-all type on a value that has a known shape.
- Suppression directives that disable checking for a whole file or block.
- Re-declaring the same shape inline in several places instead of naming it once.

## What belongs to the language skill

Concrete forbidden patterns, ESLint/tsconfig configuration, and project type-alias conventions are in `code/languages/nodejs`. Load it for the specifics.
