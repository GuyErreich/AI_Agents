# UObject and reflection

## `UPROPERTY` is a GC root

Every UObject pointer that must survive a GC pass is a `UPROPERTY`. A raw `UObject*` (or `TObjectPtr` without `UPROPERTY`) is invisible to the collector and becomes a dangling pointer after the next sweep.

```cpp
// Forbidden — unrooted; GC can collect Mid
UMaterialInterface* Mid;

// Prefer
UPROPERTY(VisibleAnywhere, Category = "Rendering")
TObjectPtr<UMaterialInterface> Mid;
```

## `TObjectPtr` vs weak vs soft

| Type | When |
|---|---|
| `TObjectPtr<T>` + `UPROPERTY` | Hard ref; default for components, owned objects, loaded assets |
| `TWeakObjectPtr<T>` | Observe without keeping alive (cached actor, last instigator) |
| `TSoftObjectPtr<T>` / `TSoftClassPtr<T>` | Asset path; load on demand — avoids cooking a hard dependency |

`IsValid(Object)` (or `Weak.IsValid()`) before dereference. Do not compare a `TObjectPtr` to `nullptr` as the only check after an async load.

## Specifiers

- Always set `Category=` on editable properties so the Details panel is navigable.
- `BlueprintReadOnly` / `BlueprintReadWrite` only when designers need the field. Default is C++-only.
- `VisibleAnywhere` for runtime-owned components; `EditDefaultsOnly` for CDO configuration; `EditAnywhere` is the exception, not the default.
- Replicated properties also need `Replicated` / `ReplicatedUsing=` — see `references/networking-and-authority.md`.

## `UFUNCTION`

- `BlueprintCallable` only for operations designers should invoke.
- `BlueprintPure` only for side-effect-free queries.
- `BlueprintNativeEvent` when C++ provides a default and BP may override; `BlueprintImplementableEvent` when C++ only dispatches.
- Do not mark a hot-path function `BlueprintCallable` just to "make it available."

## Reflection macros

`UCLASS()`, `USTRUCT()`, `UENUM()`, `GENERATED_BODY()` on every reflected type. Put `GENERATED_BODY()` first in the class. Include the `.generated.h` as the **last** include in the header.
