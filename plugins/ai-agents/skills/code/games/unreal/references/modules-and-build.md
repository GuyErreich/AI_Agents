# Modules and build

## One module per feature

A gameplay feature (inventory, online, UI shell) is a module with its own `*.Build.cs`, Public/Private split, and `IMPLEMENT_MODULE`. Do not dump new systems into the game module's grab-bag when they have their own dependencies and lifecycle.

## Public vs Private

| Folder | Visible to | Put here |
|---|---|---|
| `Public/` | Downstream modules that depend on this one | Types and APIs other modules must name |
| `Private/` | This module only | Implementation, helpers, translation units |

In `*.Build.cs`:

- `PublicDependencyModuleNames` — modules whose **public** headers this module's public headers include.
- `PrivateDependencyModuleNames` — modules used only in Private `.cpp` / private headers.

A Public dependency is a promise to every consumer. Prefer Private. Circular module deps are a design bug — split the shared types into a third module.

## Includes

- Include engine and plugin public APIs only. Do not include `Runtime/*/Private/...` engine headers.
- PCH: include the module PCH first in `.cpp` files when the module uses one. Do not add incidental engine headers to the PCH "to make it faster" without measuring.

## Targets

`*.Target.cs` lists modules for Editor / Game / Server / Client targets. A dedicated-server target must not pull editor-only or UI-only modules. Guard editor code with `#if WITH_EDITOR`.

## Generated files

`*.generated.h`, `Intermediate/`, and `Binaries/` are build outputs. Never hand-edit `.generated.h`. After adding a `UCLASS` / `USTRUCT`, include `FileName.generated.h` as the last include and compile so UHT can emit it.
