# Lens — Unreal Engine 5

Activate with `code/games/unreal`. Hunt GC, lifecycle, and authority defects, not naming taste.

## Hunt list

- **Unrooted UObject refs** — raw `UObject*` / `TObjectPtr` without `UPROPERTY`; cached actor pointer that GC can collect
- **Missing reflection** — UObject field that must serialize or show in Details without `UPROPERTY`; `.generated.h` not last
- **Tick creep** — `bCanEverTick` left true; allocations, string builds, or `LoadSynchronous` inside Tick
- **Constructor-time world access** — `GetWorld()`, spawn, or asset load in a constructor (CDO-unsafe)
- **Delegates** — bound in `BeginPlay` and never unbound in `EndPlay`; lambda captures `this` past destroy
- **Client-trusting RPCs** — Server RPC without `_Validate`; gameplay state mutated on a simulated proxy
- **Hard asset references** — `TObjectPtr` to a large/optional asset on a CDO that should be `TSoftObjectPtr`

Trace each finding to a GC crash, desync, cook bloat, or editor CDO failure, not “I prefer another specifier.”
