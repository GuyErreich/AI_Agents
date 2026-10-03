# Data layout

Load this when a loop touches many elements and the work is dominated by memory access. Domain modeling stays in the engineering OOP reference. This page is the hardware constraint.

## When layout matters

CPU caches move memory in lines (typically 64 bytes). A loop that updates one field across thousands of records spends the fetch on whatever sits next to that field.

| Layout | Shape | Use when |
|---|---|---|
| Array of Structures (AoS) | Each element is a full record, often behind a pointer | The working set is small, or the operation needs most fields of each record together |
| Structure of Arrays (SoA) | One contiguous array per field | The hot loop needs one or a few fields across many elements |

- **Enforce** SoA, or a contiguous array of the hot field, on a measured hot path that streams one attribute.
- **Do not** convert every object graph to SoA. Pointer-based records are the right model for invariants, identity, and small collections.
- **Do not** allocate inside the hot loop. Reuse the arrays the system already owns.

Contiguous same-type fields are what SIMD units can consume. Prefer a straightforward loop over packed data. Reach for explicit vector intrinsics only when a profile shows the scalar loop is the limit and the project already uses them.

## Entity, component, system

For a data-intensive simulation or a large batch transform:

- An **entity** is an id. It holds no fields and no methods.
- A **component** is a plain data record, stored in a contiguous array keyed by that id.
- A **system** is a stateless function that reads and writes the component arrays it needs. It does not walk an object graph.

Objects remain at the boundary: load, save, and present. The inner loop sees arrays.

## Decision

1. Is this loop hot and wide (thousands of elements, one or few fields)? → SoA or a contiguous component array.
2. Does the type protect an invariant or a small graph of collaborators? → keep the object.
3. Is the cost unmeasured? → keep the simpler layout. Speculative SoA splits wait until a profile asks for them.
