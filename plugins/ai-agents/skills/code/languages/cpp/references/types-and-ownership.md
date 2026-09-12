# Types and ownership

## Never use `void*` or C-style casts

Use a specific type. If none exists, define one.

```cpp
// Forbidden
void* load(void* data);
auto n = (int)raw;

// Prefer
struct RawPayload { std::string_view bytes; };
ParsedConfig load(RawPayload data);
auto n = static_cast<int>(raw);
```

- **`enum class`** for closed sets of values — never a bare `int` flag.
- **Named structs** for multi-field parameters — never a bag of `bool`/`int`.
- **`auto`** is fine when the type is obvious from the right-hand side (`make_unique`, iterators). Do not use it to paper over an unknown or unstable type at a public boundary.

## Smart-pointer choice

| Use | When |
|---|---|
| Value / `unique_ptr` | Exclusive ownership; default |
| `shared_ptr` | Shared ownership is the real contract (rare) |
| `weak_ptr` | Break a `shared_ptr` cycle; observe without keeping alive |
| Raw `T*` / `T&` | Non-owning view; the callee must not `delete` |

Never return an owning raw pointer. A function that transfers ownership returns `unique_ptr` (or a value).

```cpp
// Forbidden
Widget* make_widget();

// Prefer
std::unique_ptr<Widget> make_widget();
```

## Rule of zero, else rule of five

Prefer members that manage their own resources so the class needs no special members. If you define one of destructor, copy ctor, copy assign, move ctor, or move assign, define or `= delete` all five.

## Ownership at the signature

| Parameter | Meaning |
|---|---|
| `T` | Sink — callee takes a copy or moves in |
| `const T&` | Read, no copy |
| `T&&` | Move-sink |
| `T*` / `T&` | Non-owning; nullable only when `T*` and documented |
| `std::span<T>` / `std::string_view` | Non-owning view of a contiguous range / string |

## Lifetime traps

- Do not return `std::string_view` or a reference to a function-local, a temporary, or a container element that can reallocate.
- Do not store a `string_view` / `span` past the lifetime of the backing buffer.
- Prefer `.at()` or a bounds-checked `span` over unchecked `[]` on untrusted indexes.
- Type-pun with `std::bit_cast` or `memcpy` into a `std::byte` buffer — not `reinterpret_cast` between unrelated object types.

Language and library semantics: [cppreference](https://cppreference.com/).
