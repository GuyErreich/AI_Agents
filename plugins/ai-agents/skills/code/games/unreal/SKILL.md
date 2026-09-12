---
name: unreal
description: Unreal Engine 5 C++ — Epic naming, UObject/GC, reflection, Tick discipline, authority, Blueprint boundary, modules, and content VCS. Use when writing or reviewing Source/, .Build.cs, .uproject, or UE gameplay code. Extends engineering and cpp.
disable-model-invocation: true
---

# Unreal Engine 5

UE5-specific patterns layered on the C++ and engineering foundations. Engine APIs win over STL defaults — see the divergence table.

## Extends

Load in order: `skills/code/foundations/engineering/SKILL.md` → `skills/code/languages/cpp/SKILL.md`, then this skill. Add UE-specific rules only. Where this table conflicts with `cpp` (containers, strings, ownership, logging, asserts, exceptions), follow this skill.

## UE vs standard C++

| Concern | Standard C++ (`cpp`) | Unreal |
|---|---|---|
| Containers | `std::vector` / `std::unordered_map` | `TArray` / `TMap` |
| Strings | `std::string` | `FString` (mutable), `FName` (interned id), `FText` (display/loc) |
| Ownership (non-UObject) | `unique_ptr` / `shared_ptr` | `TUniquePtr` / `TSharedPtr` / `TWeakPtr` |
| Ownership (UObject) | n/a | GC via `UPROPERTY` / `TObjectPtr`; not `unique_ptr` |
| Logging | project logger; no `std::cout` | `UE_LOG` |
| Asserts | `assert` | `check` / `ensure` / `verify` |
| Errors | status type / exceptions | no exceptions; return codes and `check` |

## Core rules

- **Epic naming.** Type prefixes `F` (struct), `U` (UObject), `A` (Actor), `E` (enum), `I` (interface), `T` (template). Bool members use a `b` prefix (`bIsActive`). PascalCase for functions **and** variables — this overrides generic camelCase. A project `AGENT.md` may override.
- **Reflection.** `UPROPERTY()` on every UObject reference that must survive GC. `TObjectPtr<T>` for UE5 `UPROPERTY` pointers. Always set `Category=`. `UFUNCTION(BlueprintCallable)` only where designers need it. See `references/uobject-and-reflection.md`.
- **GC safety.** Never cache a raw `UObject*` outside a `UPROPERTY`. `TWeakObjectPtr` for weak refs, `TSoftObjectPtr` for assets (avoid hard-reference load bloat). `IsValid()` before use.
- **Lifecycle.** Constructors set CDO defaults only — no world access, no gameplay logic. Use `OnConstruction` / `PostInitializeComponents` / `BeginPlay`; release in `EndPlay`. Never assume actor init order. See `references/lifecycle-and-tick.md`.
- **Tick discipline.** `PrimaryActorTick.bCanEverTick = false` unless the actor must tick. Prefer timers, delegates, and subsystems. No allocations or heavy work per tick.
- **Authority.** `HasAuthority()` before mutating simulated state. `GetLifetimeReplicatedProps` for replicated fields. `_Validate` on server RPCs. Never trust client input — ties to `code/quality/security`. See `references/networking-and-authority.md`.
- **Blueprint boundary.** C++ owns systems and data; Blueprints compose. Expose a minimal typed API via `BlueprintNativeEvent` / `BlueprintImplementableEvent`. Do not duplicate gameplay-critical logic in BP. See `references/blueprint-and-data.md`.
- **Modules and build.** One module per feature. Public vs Private deps in `*.Build.cs`. No engine-private includes. See `references/modules-and-build.md`.
- **Content and VCS.** Assets grouped by feature — never loose in `Content/` root. Prefixes `BP_`, `M_`, `T_`, `SK_`. Git LFS for `*.uasset` / `*.umap` / binaries. Never commit `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`. See `references/content-and-vcs.md`.
- **Authority for APIs.** [Programming with C++ in Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/programming-with-cplusplus-in-unreal-engine).

## When to load references

| Topic | Reference |
|---|---|
| `UCLASS` / `UPROPERTY` / `TObjectPtr`, GC roots, soft refs | `references/uobject-and-reflection.md` |
| CDO vs BeginPlay, EndPlay, Tick vs timers | `references/lifecycle-and-tick.md` |
| Blueprint exposure, data assets, C++/BP split | `references/blueprint-and-data.md` |
| Replication, RPCs, `_Validate`, client trust | `references/networking-and-authority.md` |
| Modules, Public/Private, `*.Build.cs` | `references/modules-and-build.md` |
| Feature folders, asset prefixes, LFS, generated dirs | `references/content-and-vcs.md` |

Load a reference only when the matching decision arises.

## Validation

Before considering work complete, run the project's **Validate** commands from the repository `AGENT.md` and require zero errors.

- **Build** the editor target (or the project's listed UE target) after C++ or `*.Build.cs` changes.
- **Live Coding / Hot Reload** is not a substitute for a clean compile.
- Follow `cpp` Validation for tidy/format/sanitizers when the project enables them on game modules.
