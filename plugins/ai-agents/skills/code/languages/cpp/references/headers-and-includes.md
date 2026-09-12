# Headers and includes

## Include-what-you-use

Include the header that declares each name you use. Do not rely on transitive includes. Drop includes that are unused after an edit.

## `#pragma once`

Use `#pragma once` as the include guard. Do not add a second `#ifndef`/`#define` guard on the same file unless a project `AGENT.md` requires both.

## Header surface

- Headers are self-contained: include them alone and they compile.
- Forward-declare classes and structs you only mention by pointer or reference. Include the definition when you need size, members, or inheritance.
- No `using namespace` at header scope (including `std`). A file-local `using` in a `.cpp` is acceptable for a short alias.
- Prefer `inline` / header-only only for templates and trivial accessors. Put non-template definitions in a `.cpp` to keep the ODR honest.

## Include order

When the project does not already specify one, group:

1. The matching header for this translation unit
2. Project headers
3. Third-party
4. Standard library

Separate groups with a blank line. Angle brackets for system/third-party, quotes for project headers.

## Modules

C++20 modules (`export module`, `import`) are allowed when the project's toolchain and CMake already enable them. Do not mix module and header interfaces for the same entity. Until the repo adopts modules, stay with headers.

## ODR

One definition per entity across the program. `inline` on header-defined functions; no non-inline globals in headers. Template definitions live in the header (or a `.tpp` included from it).
